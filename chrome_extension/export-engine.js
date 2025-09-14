export const exportEngine = {
  toMarkdown(conversation) {
    // TODO: Build markdown representation
    return `# Conversation Export\n`;
  },
  toJSON(conversation) {
    return JSON.stringify(conversation, null, 2);
  },
  toPDF(conversation) {
    // TODO: Generate PDF file
  }
};
