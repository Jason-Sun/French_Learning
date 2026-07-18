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
  const MAX_DRAFTS = 48;
  const SUPPORTED_KINDS = new Set(['explanation', 'usage_note', 'memory_tip', 'examples', 'sentence_guide', 'provisional_lookup']);
  const providerMethodFor = request => {
    if (request.kind === 'usage_note') return 'generateUsageNote';
    if (request.kind === 'memory_tip') return 'generateMemoryTip';
    if (request.kind === 'examples') return 'generateExamples';
    if (request.kind === 'sentence_guide') return 'explainSentence';
    if (request.kind === 'explanation' && (request.target?.type_code || request.target?.type) === 'grammar_construction') return 'explainGrammar';
    return 'generateLearningResource';
  };

  const readDrafts = () => {
    try {
      const value = JSON.parse(localStorage.getItem(DRAFTS_KEY) || '[]');
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  };

  const writeDrafts = drafts => localStorage.setItem(DRAFTS_KEY, JSON.stringify(drafts.slice(0, MAX_DRAFTS)));
  const plainText = value => String(value || '').replace(/\s+/g, ' ').trim();
  const keyFor = request => [
    request.target?.id || `lookup:${plainText(request.query).toLocaleLowerCase('fr')}`,
    request.kind,
    request.language || 'en',
    request.context?.senseId || '',
    request.context?.sentence || '',
  ].join('|');

  const publicTarget = target => target ? {
    id: target.id,
    canonicalForm: target.canonical_form,
    displayForm: target.display_form,
    type: target.type_code,
    cefrLevel: target.cefr_level || null,
    partOfSpeech: target.part_of_speech || null,
  } : null;

  const sanitizeResponse = (response, request) => {
    const body = plainText(response?.body || response?.content || '');
    if (!body || body.length > 1800) throw new Error('The provider returned an invalid learning draft.');
    const title = plainText(response?.title || request.title || 'Learning note').slice(0, 120);
    return {
      id: `ai-draft:${crypto.randomUUID()}`,
      key: keyFor(request),
      kind: request.kind,
      language: request.language || 'en',
      targetId: request.target?.id || null,
      query: plainText(request.query) || null,
      title,
      body,
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

  const get = request => readDrafts().find(draft => draft.key === keyFor(request)) || null;
  const enabled = () => localStorage.getItem(ENABLED_KEY) === 'true';
  const setEnabled = value => localStorage.setItem(ENABLED_KEY, String(Boolean(value)));

  async function generate(request) {
    if (!SUPPORTED_KINDS.has(request?.kind)) throw new Error('Unsupported learning resource kind.');
    if (!enabled()) return { status: 'disabled' };
    if (!providerReady()) return { status: 'provider_unavailable' };

    const existing = get(request);
    if (existing) return { status: 'cached', draft: existing };

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

    const draft = sanitizeResponse(response, request);
    writeDrafts([draft, ...readDrafts().filter(item => item.key !== draft.key)]);
    return { status: 'generated', draft };
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
    generate,
    clear: request => writeDrafts(readDrafts().filter(item => item.key !== keyFor(request))),
  });
})();
