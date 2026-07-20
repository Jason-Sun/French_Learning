#!/usr/bin/env node
/* Focused regression tests for local AI Learning Resource cache behaviour. */

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const packPaths = [
  'data/learning-packs/core-a1-v1.json',
  'data/learning-packs/core-everyday-function-words-v1.json',
  'data/learning-packs/core-everyday-words-v1.json',
  'data/learning-packs/demo-sentence-je-vais-manger-v1.json',
];
const packResourceKeys = new Set();
for (const packPath of packPaths) {
  const pack = JSON.parse(fs.readFileSync(packPath, 'utf8'));
  assert.equal(pack.schemaVersion, 1, `${packPath} has the supported schema version`);
  assert.equal(typeof pack.id, 'string', `${packPath} has a stable pack ID`);
  assert.ok(Array.isArray(pack.resources) && pack.resources.length, `${packPath} has resources`);
  for (const resource of pack.resources) {
    assert.equal(typeof resource.id, 'string', `${packPath} resource has an ID`);
    assert.ok(typeof resource.targetId === 'string' || (resource.kind === 'sentence_guide' && typeof resource.query === 'string'), `${packPath} resource has a canonical target or exact sentence context`);
    assert.equal(typeof resource.kind, 'string', `${packPath} resource has a kind`);
    assert.ok(['en', 'zh-Hans'].includes(resource.language), `${packPath} resource uses a supported teaching language`);
    assert.ok(resource.title && resource.body && resource.body.length <= 1800, `${packPath} resource has bounded learner content`);
    const identity = `${resource.targetId || resource.query}|${resource.kind}|${resource.language}|${JSON.stringify(resource.context || {})}`;
    assert.equal(packResourceKeys.has(identity), false, `${packPath} does not duplicate a resource identity`);
    packResourceKeys.add(identity);
  }
}

const values = new Map();
const localStorage = {
  getItem: key => values.has(key) ? values.get(key) : null,
  setItem: (key, value) => values.set(key, String(value)),
  removeItem: key => values.delete(key),
};
const storedResources = new Map();
const storedRecents = new Map();
const shippedPack = {
  schemaVersion: 1,
  id: 'auto-loaded-pack',
  provider: 'OpenAI Codex',
  model: 'GPT-5',
  prompt_version: 'auto-pack-v1',
  resources: [{
    id: 'aimer-en',
    targetId: 'fr:word:aimer:ver',
    kind: 'usage_note',
    language: 'en',
    title: 'Using aimer',
    body: 'Aimer means to like or to love.',
  }],
};
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
  fetch: async () => ({ ok: true, json: async () => shippedPack }),
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
  assert.equal(storedResources.size, 1, 'the shipped learning pack loads into the durable AI Learning Database');
  assert.equal([...storedResources.values()][0].origin, 'prebuilt_ai_draft', 'a shipped pack remains explicitly non-canonical');
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
  assert.equal(storedResources.size, 2, 'the generated draft is written to the durable AI Learning Database');
  assert.equal([...storedResources.values()].find(resource => resource.origin === 'ai_generated').prompt_version, 'test-v3', 'each draft records the prompt version that generated it');
  assert.equal(values.has('liens-ai-learning-drafts-v1'), false, 'drafts are not written back to legacy localStorage');
  const cached = await assist.ensure(request);
  assert.equal(cached.status, 'cached');
  assert.equal(calls, 1, 'opening a cached lookup does not generate again');
  assert.equal(assist.get(request).body, 'A city and the capital of France.');
  assert.equal(assist.needsRegeneration(request), true, 'the resolver can detect a newer provider prompt without deleting the stored revision');
  assert.equal(assist.findProvisionalLookup('PARIS').title, 'Paris', 'AI lookups are searchable through normalized query');
  const prebuiltRequest = {
    target: { id: 'fr:word:aller:ver' },
    kind: 'usage_note',
    language: 'en',
    title: 'Learning aller',
    context: {},
  };
  const imported = await assist.importPrebuiltPack({
    schemaVersion: 1,
    id: 'test-core-pack',
    provider: 'OpenAI Codex',
    model: 'GPT-5',
    prompt_version: 'test-pack-v1',
    resources: [{
      id: 'aller-en',
      targetId: 'fr:word:aller:ver',
      kind: 'usage_note',
      language: 'en',
      title: 'Using aller',
      body: 'Aller means to go.',
    }],
  });
  assert.equal(imported, 1, 'a valid prebuilt pack imports into the AI Learning Database');
  assert.equal(assist.get(prebuiltRequest).origin, 'prebuilt_ai_draft', 'prebuilt resources remain explicitly non-canonical AI drafts');
  const prebuiltCached = await assist.ensure(prebuiltRequest);
  assert.equal(prebuiltCached.status, 'cached', 'a prebuilt learning resource prevents an unnecessary provider call');
  assert.equal(calls, 1, 'the provider is not called for a matching prebuilt resource');
  const sentenceRequest = {
    kind: 'sentence_guide',
    language: 'en',
    title: 'Understanding Je vais manger.',
    query: 'Je vais manger.',
    context: { sentence: 'Je vais manger.' },
  };
  const sentenceImported = await assist.importPrebuiltPack({
    schemaVersion: 1,
    id: 'test-sentence-pack',
    resources: [{
      id: 'je-vais-manger-en',
      kind: 'sentence_guide',
      language: 'en',
      query: 'Je vais manger.',
      context: { sentence: 'Je vais manger.' },
      title: 'Understanding Je vais manger.',
      body: 'This is the futur proche.',
      translation: 'I am going to eat.',
    }],
  });
  assert.equal(sentenceImported, 1, 'a prebuilt sentence guide imports without inventing a canonical sentence target');
  assert.equal(assist.get(sentenceRequest).translation, 'I am going to eat.', 'the sentence guide supplies its cached translation');
  assert.equal((await assist.ensure(sentenceRequest)).status, 'cached', 'a prebuilt sentence guide prevents an unnecessary provider call');
  assert.equal(calls, 1, 'the provider is not called for the cached sentence guide');
  const unpunctuatedSentenceRequest = {
    ...sentenceRequest,
    query: 'Je vais manger',
    context: { sentence: 'Je vais manger' },
  };
  assert.equal(assist.get(unpunctuatedSentenceRequest).translation, 'I am going to eat.', 'sentence guidance ignores cosmetic terminal punctuation');
  const duplicatePack = await assist.importPrebuiltPack({
    schemaVersion: 1,
    id: 'test-core-pack-v2',
    resources: [{
      id: 'aller-en',
      targetId: 'fr:word:aller:ver',
      kind: 'usage_note',
      language: 'en',
      title: 'A replacement',
      body: 'This must not overwrite a learner resource.',
    }],
  });
  assert.equal(duplicatePack, 0, 'a shipped pack never overwrites an active learner resource');
  await assist.supersede(request);
  assert.equal(assist.get(request), null, 'a canonical replacement hides the AI draft from normal resolution');
  assert.equal([...storedResources.values()].find(resource => resource.origin === 'ai_generated').lifecycle, 'superseded', 'the historical AI record remains stored as superseded');
  console.log('AI Learning cache regression checks passed.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
