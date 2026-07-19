#!/usr/bin/env node
/* Focused regression tests for local AI Learning Resource cache behaviour. */

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const values = new Map();
const localStorage = {
  getItem: key => values.has(key) ? values.get(key) : null,
  setItem: (key, value) => values.set(key, String(value)),
  removeItem: key => values.delete(key),
};
const storedResources = new Map();
const storedRecents = new Map();
const learningStore = {
  ready: async () => {},
  mode: () => 'indexeddb',
  listResources: () => [...storedResources.values()],
  listRecent: () => [...storedRecents.values()],
  putResource: async resource => storedResources.set(resource.id, resource),
  putRecent: async recent => storedRecents.set(recent.normalizedQuery, recent),
  deleteByResourceKey: async key => {
    [...storedResources.values()]
      .filter(resource => resource.resourceKey === key)
      .forEach(resource => storedResources.delete(resource.id));
  },
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
  Event: class Event {},
  dispatchEvent: () => {},
  LiensAILearningStore: learningStore,
};
context.globalThis = context;
context.LiensAIProvider = {
  id: 'test-provider',
  isAvailable: () => true,
  promptVersion: () => 'test-v4',
  generateLearningResource: async () => {
    calls += 1;
    return { title: 'Paris', body: 'A city and the capital of France.', prompt_version: 'test-v3' };
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('ai-learning.js', 'utf8'), context);

(async () => {
  const assist = context.LiensLearningAssist;
  await assist.ready();
  assert.equal(assist.storageMode(), 'indexeddb', 'the durable AI Learning Database is the active store');
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
  assert.equal(storedResources.size, 1, 'the generated draft is written to the durable AI Learning Database');
  assert.equal([...storedResources.values()][0].prompt_version, 'test-v3', 'each draft records the prompt version that generated it');
  assert.equal(values.has('liens-ai-learning-drafts-v1'), false, 'drafts are not written back to legacy localStorage');
  const cached = await assist.ensure(request);
  assert.equal(cached.status, 'cached');
  assert.equal(calls, 1, 'opening a cached lookup does not generate again');
  assert.equal(assist.get(request).body, 'A city and the capital of France.');
  assert.equal(assist.needsRegeneration(request), true, 'the resolver can detect a newer provider prompt without deleting the stored revision');
  assert.equal(assist.findProvisionalLookup('PARIS').title, 'Paris', 'AI lookups are searchable through normalized query');
  await assist.supersede(request);
  assert.equal(assist.get(request), null, 'a canonical replacement hides the AI draft from normal resolution');
  assert.equal([...storedResources.values()][0].lifecycle, 'superseded', 'the historical AI record remains stored as superseded');
  console.log('AI Learning cache regression checks passed.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
