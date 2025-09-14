export const storageManager = {
  async save(conversation) {
    // TODO: Persist conversation to local storage
    return new Promise(resolve => {
      chrome.storage.local.set({ [conversation.metadata.url || Date.now()]: conversation }, resolve);
    });
  }
};
