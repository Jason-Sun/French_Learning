/*
 * Liens Learning Assistance
 *
 * This module owns learner-scoped AI drafts only. It never imports, mutates,
 * indexes, or exports canonical Language Graph content. A production provider
 * is injected as window.LiensAIProvider and must implement generate(request).
 */
(() => {
  const ENABLED_KEY = 'liens-ai-learning-enabled';
  const DRAFTS_KEY = 'liens-ai-learning-drafts-v1';
  const RECENT_LOOKUPS_KEY = 'liens-ai-recent-lookups-v1';
  const MAX_DRAFTS = 48;
  const MAX_RECENT_LOOKUPS = 24;
  const inFlight = new Map();
  const generationQueue = [];
  let activeGenerationCount = 0;
  const MAX_CONCURRENT_GENERATIONS = 1;
  const SUPPORTED_KINDS = new Set([
    'explanation', 'usage_note', 'memory_tip', 'examples', 'comparison',
    'common_mistake', 'sentence_guide', 'provisional_lookup',
  ]);
  const providerMethodFor = request => {
    if (request.kind === 'usage_note') return 'generateUsageNote';
    if (request.kind === 'memory_tip') return 'generateMemoryTip';
    if (request.kind === 'examples') return 'generateExamples';
    if (request.kind === 'sentence_guide') return 'explainSentence';
    if (request.kind === 'explanation' && (request.target?.type_code || request.target?.type) === 'grammar_construction') return 'explainGrammar';
    return 'generateLearningResource';
  };

  const keyFor = request => [
    request.target?.id || `lookup:${plainText(request.query).toLocaleLowerCase('fr')}`,
    request.kind,
    request.kind === 'sentence_guide' ? 'translation-v2' : '',
    request.language || 'en',
    request.context?.senseId || '',
    request.context?.sentence || '',
  ].join('|');
  const plainText = value => String(value || '').replace(/\s+/g, ' ').trim();
  const normaliseLookup = value => plainText(value)
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');

  const normaliseDraft = draft => ({
    ...draft,
    resourceKey: draft.resourceKey || draft.key,
    revisionNumber: Number.isInteger(draft.revisionNumber) ? draft.revisionNumber : 1,
  });

  const readDrafts = () => {
    try {
      const value = JSON.parse(localStorage.getItem(DRAFTS_KEY) || '[]');
      return Array.isArray(value) ? value.map(normaliseDraft) : [];
    } catch {
      return [];
    }
  };

  const writeDrafts = drafts => localStorage.setItem(DRAFTS_KEY, JSON.stringify(drafts.slice(0, MAX_DRAFTS)));
  const readRecentLookups = () => {
    try {
      const value = JSON.parse(localStorage.getItem(RECENT_LOOKUPS_KEY) || '[]');
      return Array.isArray(value) ? value.filter(item => plainText(item?.query)) : [];
    } catch {
      return [];
    }
  };
  const writeRecentLookups = lookups => localStorage.setItem(
    RECENT_LOOKUPS_KEY,
    JSON.stringify(lookups.slice(0, MAX_RECENT_LOOKUPS)),
  );
  const recordRecentLookup = query => {
    const displayQuery = plainText(query);
    const normalizedQuery = normaliseLookup(displayQuery);
    if (!displayQuery || !normalizedQuery) return null;
    const entry = { query: displayQuery, normalizedQuery, lastOpenedAt: new Date().toISOString() };
    writeRecentLookups([entry, ...readRecentLookups().filter(item => item.normalizedQuery !== normalizedQuery)]);
    return entry;
  };

  const publicTarget = target => target ? {
    id: target.id,
    canonicalForm: target.canonical_form,
    displayForm: target.display_form,
    type: target.type_code,
    cefrLevel: target.cefr_level || null,
    partOfSpeech: target.part_of_speech || null,
  } : null;

  const sanitizeResponse = (response, request, revisionNumber) => {
    const body = plainText(response?.body || response?.content || '');
    const bodyLimit = request.kind === 'provisional_lookup' ? 650 : 1800;
    if (!body || body.length > bodyLimit) throw new Error('The provider returned an invalid learning draft.');
    const title = plainText(response?.title || request.title || 'Learning note').slice(0, 120);
    return {
      id: `ai-draft:${crypto.randomUUID()}`,
      key: keyFor(request),
      resourceKey: keyFor(request),
      revisionNumber,
      kind: request.kind,
      language: request.language || 'en',
      targetId: request.target?.id || null,
      query: plainText(request.query) || null,
      title,
      body,
      translation: plainText(response?.translation || '').slice(0, 360) || null,
      origin: 'ai_generated',
      lifecycle: 'draft',
      createdAt: new Date().toISOString(),
      provider: plainText(response?.provider || globalThis.LiensAIProvider?.id || 'configured-provider').slice(0, 80),
    };
  };

  const provider = () => globalThis.LiensAIProvider;
  const providerReady = () => {
    const candidate = provider();
    return Boolean(candidate && (typeof candidate.isAvailable === 'function' ? candidate.isAvailable() : typeof candidate.generateLearningResource === 'function'));
  };

  const revisionsFor = request => readDrafts()
    .filter(draft => draft.resourceKey === keyFor(request))
    .sort((left, right) => right.revisionNumber - left.revisionNumber || String(right.createdAt).localeCompare(String(left.createdAt)));
  const get = request => revisionsFor(request)[0] || null;
  // Online learning assistance is the default completion path. A learner can
  // explicitly turn it off when they do not want network-backed drafts.
  const enabled = () => localStorage.getItem(ENABLED_KEY) !== 'false';
  const setEnabled = value => localStorage.setItem(ENABLED_KEY, String(Boolean(value)));

  async function generate(request, { regenerate = false } = {}) {
    if (!SUPPORTED_KINDS.has(request?.kind)) throw new Error('Unsupported learning resource kind.');
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
    writeDrafts([draft, ...readDrafts()]);
    return { status: 'generated', draft };
  }

  function drainGenerationQueue() {
    if (activeGenerationCount >= MAX_CONCURRENT_GENERATIONS || !generationQueue.length) return;
    const next = generationQueue.shift();
    activeGenerationCount += 1;
    Promise.resolve()
      .then(() => generate(next.request))
      .then(next.resolve, next.reject)
      .finally(() => {
        activeGenerationCount -= 1;
        drainGenerationQueue();
      });
  }

  async function ensure(request) {
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

  globalThis.LiensLearningAssist = Object.freeze({
    enabled,
    setEnabled,
    providerReady,
    refreshProviderAvailability: async () => {
      const candidate = provider();
      return typeof candidate?.refreshAvailability === 'function' ? candidate.refreshAvailability() : providerReady();
    },
    get,
    getRevisions: revisionsFor,
    keyFor,
    recentLookups: readRecentLookups,
    recordRecentLookup,
    generate,
    ensure,
    clear: request => writeDrafts(readDrafts().filter(item => item.key !== keyFor(request))),
  });
})();
