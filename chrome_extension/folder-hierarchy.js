export const folderHierarchy = {
  tree: {},
  add(path) {
    // TODO: Add folder path to hierarchy
    this.tree[path] = this.tree[path] || {};
  }
};
