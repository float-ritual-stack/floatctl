export function conversationParser() {
  // TODO: Extract metadata and messages from the current page
  return {
    metadata: {},
    messages: [],
    artifacts: { code: [], documents: [], charts: [] },
    tags: [],
    folder: null
  };
}
