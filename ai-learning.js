/*
 * Liens Learning Assistance
 *
 * This module owns learner-scoped AI Learning Resources. It never imports,
 * mutates, indexes, or exports canonical Language Graph content. Its durable
 * store is the separate browser AI Learning Database (IndexedDB).
 */
(() => {
  const ENABLED_KEY = 'liens-ai-learning-enabled';
  const LEGACY_DRAFTS_KEY = 'liens-ai-learning-drafts-v1';
  const LEGACY_RECENT_LOOKUPS_KEY = 'liens-ai-recent-lookups-v1';
  const PREBUILT_PACK_URLS = Object.freeze([
    'data/learning-packs/core-a1-v1.json',
    'data/learning-packs/core-everyday-function-words-v1.json',
    'data/learning-packs/core-everyday-words-v1.json',
  ]);
  const inFlight = new Map();
  const generationQueue = [];
  let activeGenerationCount = 0;
  const MAX_CONCURRENT_GENERATIONS = 1;
  const SUPPORTED_KINDS = new Set([
    'explanation', 'usage_note', 'memory_tip', 'examples', 'comparison',
    'common_mistake', 'sentence_guide', 'provisional_lookup',
    'pronunciation_note', 'conjugation',
  ]);
  const drafts = new Map();
  const recentLookups = new Map();

  const plainText = value => String(value || '').replace(/\s+/g, ' ').trim();
  const normaliseLookup = value => plainText(value)
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');
  const store = () => globalThis.LiensAILearningStore || null;
  const providerMethodFor = request => {
    if (request.kind === 'usage_note') return 'generateUsageNote';
    if (request.kind === 'memory_tip') return 'generateMemoryTip';
    if (request.kind === 'examples') return 'generateExamples';
    if (request.kind === 'sentence_guide') return 'explainSentence';
    if (request.kind === 'explanation' && (request.target?.type_code || request.target?.type) === 'grammar_construction') return 'explainGrammar';
    return 'generateLearningResource';
  };

  const keyFor = request => [
    request.target?.id || `lookup:${normaliseLookup(request.query)}`,
    request.kind,
    request.kind === 'sentence_guide' ? 'translation-v3-deterministic-analysis' : '',
    request.language || 'en',
    request.context?.resourceVersion || '',
    request.context?.senseId || '',
    request.context?.sentence || '',
  ].join('|');

  const normaliseDraft = draft => ({
    ...draft,
    resourceKey: draft.resourceKey || draft.key,
    lifecycle: draft.lifecycle === 'superseded' ? 'superseded' : 'active',
    revisionNumber: Number.isInteger(draft.revisionNumber) ? draft.revisionNumber : 1,
    queryNormalized: draft.queryNormalized || normaliseLookup(draft.query),
  });

  const legacyList = key => {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  };

  const hydrateMemory = () => {
    const database = store();
    if (database) {
      database.listResources().map(normaliseDraft).forEach(draft => draft?.id && drafts.set(draft.id, draft));
      database.listRecent().forEach(recent => recent?.normalizedQuery && recentLookups.set(recent.normalizedQuery, recent));
    }
  };

  const migrateLegacyStorage = async () => {
    const database = store();
    if (!database) return;
    const legacyDrafts = legacyList(LEGACY_DRAFTS_KEY).map(normaliseDraft).filter(draft => draft.id && draft.resourceKey);
    const legacyRecents = legacyList(LEGACY_RECENT_LOOKUPS_KEY).filter(recent => plainText(recent?.query));
    const missingDrafts = legacyDrafts.filter(draft => !drafts.has(draft.id));
    const missingRecents = legacyRecents.map(recent => ({
      query: plainText(recent.query),
      normalizedQuery: recent.normalizedQuery || normaliseLookup(recent.query),
      lastOpenedAt: recent.lastOpenedAt || new Date().toISOString(),
    })).filter(recent => !recentLookups.has(recent.normalizedQuery));
    await Promise.all([
      ...missingDrafts.map(draft => database.putResource(draft)),
      ...missingRecents.map(recent => database.putRecent(recent)),
    ]);
    missingDrafts.forEach(draft => drafts.set(draft.id, draft));
    missingRecents.forEach(recent => recentLookups.set(recent.normalizedQuery, recent));
    if (legacyDrafts.length || legacyRecents.length) {
      localStorage.removeItem(LEGACY_DRAFTS_KEY);
      localStorage.removeItem(LEGACY_RECENT_LOOKUPS_KEY);
    }
  };

  const putDraft = async draft => {
    const normalized = normaliseDraft(draft);
    drafts.set(normalized.id, normalized);
    const database = store();
    if (database) await database.putResource(normalized);
    else localStorage.setItem(LEGACY_DRAFTS_KEY, JSON.stringify([...drafts.values()]));
    return normalized;
  };

  const packRequest = resource => ({
    target: resource.targetId ? { id: resource.targetId } : null,
    kind: resource.kind,
    language: resource.language || 'en',
    query: resource.query || '',
    context: resource.context && typeof resource.context === 'object' ? resource.context : {},
  });

  const activeResourceForKey = resourceKey => [...drafts.values()]
    .some(draft => draft.lifecycle === 'active' && draft.resourceKey === resourceKey);

  async function importPrebuiltPack(pack) {
    if (!pack || pack.schemaVersion !== 1 || typeof pack.id !== 'string' || !Array.isArray(pack.resources)) return 0;
    let imported = 0;
    for (const resource of pack.resources) {
      if (!resource || typeof resource.id !== 'string' || typeof resource.targetId !== 'string'
        || !SUPPORTED_KINDS.has(resource.kind) || typeof resource.title !== 'string' || typeof resource.body !== 'string') continue;
      const request = packRequest(resource);
      const resourceKey = keyFor(request);
      // A learner's existing generated or imported draft always wins over a shipped default.
      if (activeResourceForKey(resourceKey)) continue;
      await putDraft({
        id: `ai-pack:${pack.id}:${resource.id}`,
        schemaVersion: 1,
        key: resourceKey,
        resourceKey,
        revisionNumber: 1,
        kind: resource.kind,
        language: request.language,
        targetId: resource.targetId,
        query: plainText(resource.query) || null,
        queryNormalized: normaliseLookup(resource.query),
        title: plainText(resource.title).slice(0, 120),
        body: plainText(resource.body),
        translation: plainText(resource.translation).slice(0, 360) || null,
        payload: null,
        origin: 'prebuilt_ai_draft',
        lifecycle: 'active',
        createdAt: resource.createdAt || pack.createdAt || new Date().toISOString(),
        provider: plainText(resource.provider || pack.provider || 'Liens prebuilt learning pack').slice(0, 80),
        model: plainText(resource.model || pack.model || '').slice(0, 120) || null,
        prompt_version: plainText(resource.prompt_version || pack.prompt_version || '').slice(0, 120) || null,
        packId: pack.id,
        generationContext: {
          targetId: resource.targetId,
          resourceKind: resource.kind,
          language: request.language,
          contextVersion: request.context?.resourceVersion || null,
          promptVersion: plainText(resource.prompt_version || pack.prompt_version || '').slice(0, 120) || null,
          source: 'prebuilt_learning_pack',
        },
      });
      imported += 1;
    }
    return imported;
  }

  async function importPrebuiltPacks() {
    if (typeof fetch !== 'function') return 0;
    const results = await Promise.all(PREBUILT_PACK_URLS.map(async url => {
      try {
        const response = await fetch(url, { headers: { Accept: 'application/json' } });
        if (!response.ok) return 0;
        return importPrebuiltPack(await response.json());
      } catch {
        // A pack is an optional offline enhancement; a missing asset must not block Liens.
        return 0;
      }
    }));
    return results.reduce((total, count) => total + count, 0);
  }

  const ready = Promise.resolve(store()?.ready?.())
    .then(async () => {
      hydrateMemory();
      await migrateLegacyStorage();
      await importPrebuiltPacks();
      globalThis.dispatchEvent?.(new Event('liens-ai-learning-ready'));
    })
    .catch(error => {
      console.warn('Liens could not initialize the AI Learning Database.', error);
    });

  const replaceResource = putDraft;

  const recordRecentLookup = query => {
    const displayQuery = plainText(query);
    const normalizedQuery = normaliseLookup(displayQuery);
    if (!displayQuery || !normalizedQuery) return null;
    const entry = { query: displayQuery, normalizedQuery, lastOpenedAt: new Date().toISOString() };
    recentLookups.set(normalizedQuery, entry);
    ready.then(async () => {
      const database = store();
      if (database) await database.putRecent(entry);
      else localStorage.setItem(LEGACY_RECENT_LOOKUPS_KEY, JSON.stringify(listRecentLookups()));
    }).catch(() => {});
    return entry;
  };

  const listRecentLookups = () => [...recentLookups.values()]
    .sort((left, right) => String(right.lastOpenedAt).localeCompare(String(left.lastOpenedAt)));

  const publicTarget = target => target ? {
    id: target.id,
    canonicalForm: target.canonical_form,
    displayForm: target.display_form,
    type: target.type_code,
    cefrLevel: target.cefr_level || null,
    partOfSpeech: target.part_of_speech || null,
    features: target.features || null,
  } : null;

  const sanitizeResponse = (response, request, revisionNumber) => {
    const body = plainText(response?.body || response?.content || '');
    const bodyLimit = request.kind === 'provisional_lookup' ? 650 : 1800;
    if (!body || body.length > bodyLimit) throw new Error('The provider returned an invalid learning draft.');
    const title = plainText(response?.title || request.title || 'Learning note').slice(0, 120);
    return {
      id: `ai-draft:${crypto.randomUUID()}`,
      schemaVersion: 1,
      key: keyFor(request),
      resourceKey: keyFor(request),
      revisionNumber,
      kind: request.kind,
      language: request.language || 'en',
      targetId: request.target?.id || null,
      query: plainText(request.query) || null,
      queryNormalized: normaliseLookup(request.query),
      title,
      body,
      translation: plainText(response?.translation || '').slice(0, 360) || null,
      payload: response?.payload && typeof response.payload === 'object' ? response.payload : null,
      origin: 'ai_generated',
      lifecycle: 'active',
      createdAt: new Date().toISOString(),
      provider: plainText(response?.provider || globalThis.LiensAIProvider?.id || 'configured-provider').slice(0, 80),
      model: plainText(response?.model || '').slice(0, 120) || null,
      prompt_version: plainText(response?.prompt_version || response?.promptVersion || '').slice(0, 120) || null,
      generationContext: {
        targetId: request.target?.id || null,
        resourceKind: request.kind,
        language: request.language || 'en',
        contextVersion: request.context?.resourceVersion || null,
        promptVersion: plainText(response?.prompt_version || response?.promptVersion || '').slice(0, 120) || null,
      },
    };
  };

  const provider = () => globalThis.LiensAIProvider;
  const providerReady = () => {
    const candidate = provider();
    return Boolean(candidate && (typeof candidate.isAvailable === 'function' ? candidate.isAvailable() : typeof candidate.generateLearningResource === 'function'));
  };
  const currentPromptVersion = () => {
    const value = provider()?.promptVersion;
    return plainText(typeof value === 'function' ? value() : value).slice(0, 120) || null;
  };
  const revisionsFor = request => [...drafts.values()]
    .filter(draft => draft.lifecycle === 'active' && draft.resourceKey === keyFor(request))
    .sort((left, right) => right.revisionNumber - left.revisionNumber || String(right.createdAt).localeCompare(String(left.createdAt)));
  const get = request => revisionsFor(request)[0] || null;
  const needsRegeneration = request => {
    const draft = get(request);
    const latest = currentPromptVersion();
    return Boolean(draft && latest && draft.prompt_version !== latest);
  };
  const findProvisionalLookup = query => [...drafts.values()]
    .filter(draft => draft.lifecycle === 'active' && draft.kind === 'provisional_lookup' && draft.queryNormalized === normaliseLookup(query))
    .sort((left, right) => String(right.createdAt).localeCompare(String(left.createdAt)))[0] || null;
  const enabled = () => localStorage.getItem(ENABLED_KEY) !== 'false';
  const setEnabled = value => localStorage.setItem(ENABLED_KEY, String(Boolean(value)));

  async function generate(request, { regenerate = false } = {}) {
    if (!SUPPORTED_KINDS.has(request?.kind)) throw new Error('Unsupported learning resource kind.');
    await ready;
    if (!enabled()) return { status: 'disabled' };
    if (!providerReady()) return { status: 'provider_unavailable' };
    const existing = get(request);
    if (existing && !regenerate) return { status: 'cached', draft: existing };
    const method = providerMethodFor(request);
    if (typeof provider()[method] !== 'function') throw new Error(`The configured provider cannot ${method}.`);
    const response = await provider()[method](Object.freeze({
      schemaVersion: 1,
      resourceKind: request.kind,
      language: request.language || 'en',
      target: publicTarget(request.target),
      query: plainText(request.query) || null,
      context: Object.freeze({
        senseId: request.context?.senseId || null,
        sentence: plainText(request.context?.sentence) || null,
        knownGraphSummary: plainText(request.context?.knownGraphSummary) || null,
      }),
      constraints: Object.freeze({
        canonicalGraphReadOnly: true,
        createRelationships: false,
        createCanonicalObjects: false,
        output: 'plain_text_learning_resource',
      }),
    }));
    const draft = sanitizeResponse(response, request, (existing?.revisionNumber || 0) + 1);
    await replaceResource(draft);
    return { status: 'generated', draft };
  }

  function drainGenerationQueue() {
    if (activeGenerationCount >= MAX_CONCURRENT_GENERATIONS || !generationQueue.length) return;
    const next = generationQueue.shift();
    activeGenerationCount += 1;
    Promise.resolve().then(() => generate(next.request)).then(next.resolve, next.reject).finally(() => {
      activeGenerationCount -= 1;
      drainGenerationQueue();
    });
  }

  async function ensure(request) {
    await ready;
    const existing = get(request);
    if (existing) return { status: 'cached', draft: existing };
    if (!enabled()) return { status: 'disabled' };
    if (!providerReady()) return { status: 'provider_unavailable' };
    const key = keyFor(request);
    if (!inFlight.has(key)) {
      const pending = new Promise((resolve, reject) => {
        generationQueue.push({ request, resolve, reject });
        drainGenerationQueue();
      }).finally(() => inFlight.delete(key));
      inFlight.set(key, pending);
    }
    return inFlight.get(key);
  }

  async function supersede(request, reason = 'canonical_resource_available') {
    await ready;
    const matching = revisionsFor(request);
    if (!matching.length) return false;
    await Promise.all(matching.map(draft => replaceResource({
      ...draft,
      lifecycle: 'superseded',
      supersededAt: new Date().toISOString(),
      supersededBy: reason,
    })));
    return true;
  }

  async function clear(request) {
    await ready;
    const matching = revisionsFor(request);
    matching.forEach(draft => drafts.delete(draft.id));
    const database = store();
    if (database) await database.deleteByResourceKey(keyFor(request));
    else localStorage.setItem(LEGACY_DRAFTS_KEY, JSON.stringify([...drafts.values()]));
  }

  globalThis.LiensLearningAssist = Object.freeze({
    ready: () => ready,
    storageMode: () => store()?.mode?.() || 'legacy-local-storage',
    enabled,
    setEnabled,
    providerReady,
    providerMessage: () => {
      const candidate = provider();
      return plainText(typeof candidate?.unavailabilityMessage === 'function' ? candidate.unavailabilityMessage() : '');
    },
    currentPromptVersion,
    refreshProviderAvailability: async () => {
      const candidate = provider();
      return typeof candidate?.refreshAvailability === 'function' ? candidate.refreshAvailability() : providerReady();
    },
    get,
    needsRegeneration,
    getRevisions: revisionsFor,
    keyFor,
    findProvisionalLookup,
    importPrebuiltPack,
    recentLookups: listRecentLookups,
    recordRecentLookup,
    generate,
    ensure,
    supersede,
    clear,
  });
})();
