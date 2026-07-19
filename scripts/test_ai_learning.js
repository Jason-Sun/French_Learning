#!/usr/bin/env node
/* Focused regression tests for local AI Learning Resource cache behaviour. */

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const values = new Map();
const localStorage = {
  getItem: key => values.has(key) ? values.get(key) : null,
  setItem: (key, value) => values.set(key, String(value)),
};
let calls = 0;
const context = {
  console,
  localStorage,
  crypto: { randomUUID: () => 'test-draft-id' },
  Promise,
  Date,
  JSON,
  String,
  Boolean,
  Number,
  Array,
  Object,
  Set,
  Map,
};
context.globalThis = context;
context.LiensAIProvider = {
  id: 'test-provider',
  isAvailable: () => true,
  generateLearningResource: async () => {
    calls += 1;
    return { title: 'Paris', body: 'A city and the capital of France.' };
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('ai-learning.js', 'utf8'), context);

(async () => {
  const assist = context.LiensLearningAssist;
  assist.recordRecentLookup(' Paris ');
  assist.recordRecentLookup('PARIS');
  const recent = assist.recentLookups();
  assert.equal(recent.length, 1, 'recent unknown lookups deduplicate by normalized query');
  assert.equal(recent[0].query, 'PARIS', 'the most recent display form is retained');

  const request = {
    kind: 'provisional_lookup',
    language: 'en',
    title: 'Learning Paris',
    query: 'Paris',
    context: { query: 'Paris' },
  };
  const first = await assist.ensure(request);
  assert.equal(first.status, 'generated');
  assert.equal(calls, 1, 'the initial lookup creates one draft');
  const cached = await assist.ensure(request);
  assert.equal(cached.status, 'cached');
  assert.equal(calls, 1, 'opening a cached lookup does not generate again');
  assert.equal(assist.get(request).body, 'A city and the capital of France.');
  console.log('AI Learning cache regression checks passed.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
