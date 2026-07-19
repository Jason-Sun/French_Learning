/* Gemini development adapter.
 *
 * It receives typed Learning Resource requests from LiensLearningAssist and
 * forwards them to the local development server. Gemini prompts and the API
 * key remain server-side; no page component knows Gemini prompt text.
 */
(() => {
  const endpoint = '/api/ai/learning-resource';
  const statusEndpoint = '/api/ai/status';
  const REQUEST_TIMEOUT_MS = 35_000;
  const RATE_LIMIT_COOLDOWN_MS = 60_000;
  let available = false;
  let promptVersion = null;
  let retryAfter = 0;
  let unavailableMessage = '';

  function markTemporarilyUnavailable(message) {
    available = false;
    unavailableMessage = message;
    retryAfter = Date.now() + RATE_LIMIT_COOLDOWN_MS;
  }

  async function refreshAvailability() {
    if (Date.now() < retryAfter) return false;
    try {
      const response = await fetch(statusEndpoint, { headers: { Accept: 'application/json' } });
      const status = response.ok ? await response.json() : null;
      available = Boolean(status?.ready && status?.provider === 'gemini');
      promptVersion = typeof status?.prompt_version === 'string' ? status.prompt_version : null;
      unavailableMessage = available ? '' : 'Online learning assistance is temporarily unavailable. The local graph remains available.';
    } catch {
      available = false;
      promptVersion = null;
      unavailableMessage = 'Online learning assistance is temporarily unavailable. The local graph remains available.';
    }
    return available;
  }

  async function request(operation, learningResource) {
    if (Date.now() < retryAfter) throw new Error(unavailableMessage || 'Gemini is temporarily rate limited. Please try again shortly.');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ operation, learningResource }),
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = payload?.error || 'Gemini could not prepare this learning note.';
        if (response.status === 429 || /rate limit/i.test(message)) markTemporarilyUnavailable('Gemini is temporarily rate limited. Please try again shortly.');
        throw new Error(message);
      }
      return payload;
    } catch (error) {
      if (error?.name === 'AbortError') throw new Error('Online learning assistance took too long.');
      if (/rate limit/i.test(String(error?.message || error || ''))) markTemporarilyUnavailable('Gemini is temporarily rate limited. Please try again shortly.');
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  const invoke = operation => learningResource => request(operation, learningResource);
  globalThis.LiensAIProvider = Object.freeze({
    id: 'gemini-development',
    isAvailable: () => available,
    promptVersion: () => promptVersion,
    unavailabilityMessage: () => unavailableMessage,
    refreshAvailability,
    generateLearningResource: invoke('generateLearningResource'),
    generateUsageNote: invoke('generateUsageNote'),
    generateMemoryTip: invoke('generateMemoryTip'),
    generateExamples: invoke('generateExamples'),
    generateComparison: invoke('generateComparison'),
    generateCommonMistake: invoke('generateCommonMistake'),
    explainGrammar: invoke('explainGrammar'),
    explainSentence: invoke('explainSentence'),
  });
  refreshAvailability();
})();
