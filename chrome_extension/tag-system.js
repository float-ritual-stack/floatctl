export const tagSystem = {
  tags: new Set(),
  add(tag) {
    this.tags.add(tag);
  },
  list() {
    return Array.from(this.tags);
  }
};
