import { conversationParser } from './conversation-parser.js';
import { storageManager } from './storage-manager.js';

(function () {
  console.log('Conversation Archaeologist content script loaded');

  const conversation = conversationParser();
  storageManager.save(conversation);
})();
