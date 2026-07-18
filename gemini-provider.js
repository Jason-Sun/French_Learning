/* Gemini development adapter.
 *
 * It receives typed Learning Resource requests from LiensLearningAssist and
 * forwards them to the local development server. Gemini prompts and the API
 * key remain server-side; no page component knows Gemini prompt text.
 */
(() => {
  const endpoint = '/api/ai/learning-resource';
  const statusEndpoint = '/api/ai/status';
  let available = false;

  async function refreshAvailability() {
    try {
      const response = await fetch(statusEndpoint, { headers: { Accept: 'application/json' } });
      const status = response.ok ? await response.json() : null;
      available = Boolean(status?.ready && status?.provider === 'gemini');
    } catch {
      available = false;
    }
    return available;
  }

  async function request(operation, learningResource) {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ operation, learningResource }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload?.error || 'Gemini could not prepare this learning note.');
    return payload;
  }

  const invoke = operation => learningResource => request(operation, learningResource);
  globalThis.LiensAIProvider = Object.freeze({
    id: 'gemini-development',
    isAvailable: () => available,
    refreshAvailability,
    generateLearningResource: invoke('generateLearningResource'),
    generateUsageNote: invoke('generateUsageNote'),
    generateMemoryTip: invoke('generateMemoryTip'),
    generateExamples: invoke('generateExamples'),
    explainGrammar: invoke('explainGrammar'),
    explainSentence: invoke('explainSentence'),
  });
  refreshAvailability();
})();
