/**
 * Tree-building utilities for the Palimpsestus novel.
 *
 * Single-book structure: all content lives under one volume folder (01/).
 * The volume layer is transparent in the UI — the home page shows
 * chapters directly under the book title.
 *
 * File naming: {volume}/{section-path}.mdx
 *   01/00.mdx       → 楔子 (chapter, depth 0)
 *   01/01.mdx       → 第一章 (chapter, depth 0, has children)
 *   01/01-00.mdx    → 其一 (section, depth 1)
 *   01/01-00-00.mdx → 其一之一 (section, depth 2)
 *
 * Reading order = lexicographic sort of file IDs.
 */

export interface TreeNode {
  id: string;
  sectionId: string;
  volume: string;
  title: string;
  breadcrumb: string[];
  url: string;
  /** 0 = chapter (direct child of book), 1+ = section */
  depth: number;
  children: TreeNode[];
  /** True if this node has child nodes */
  hasChildren: boolean;
  /** From frontmatter: marks this as a chapter-level node with special rendering */
  isChapter: boolean;
  /** Optional extra data passed through from frontmatter */
  data: Record<string, any>;
}

export interface ReadingOrder {
  prev: TreeNode | null;
  current: TreeNode;
  next: TreeNode | null;
}

/** "01/02-00-05" → "/01/02/00/05/" */
export function idToUrl(id: string): string {
  const [volume, ...rest] = id.split('/');
  const sectionPart = rest.join('/');
  if (!sectionPart) return `/${volume}/`;
  return `/${volume}/${sectionPart.replace(/-/g, '/')}/`;
}

/** Get parent section ID: "02-00-05" → "02-00", "02" → null */
function parentSectionId(sectionId: string): string | null {
  const lastDash = sectionId.lastIndexOf('-');
  return lastDash === -1 ? null : sectionId.substring(0, lastDash);
}

/** Flatten tree depth-first, pre-order (self before children) */
export function flattenTree(nodes: TreeNode[]): TreeNode[] {
  const result: TreeNode[] = [];
  function walk(node: TreeNode) {
    result.push(node);
    for (const child of node.children) walk(child);
  }
  for (const node of nodes) walk(node);
  return result;
}

/** Build tree from flat entries within a single volume */
function buildTree(
  entries: { sectionId: string; node: TreeNode }[]
): TreeNode[] {
  const nodeMap = new Map<string, TreeNode>();
  for (const { sectionId, node } of entries) nodeMap.set(sectionId, node);

  const roots: TreeNode[] = [];
  const sorted = [...entries].sort((a, b) => a.sectionId.localeCompare(b.sectionId));

  for (const { sectionId, node } of sorted) {
    const parentId = parentSectionId(sectionId);
    if (parentId === null) {
      roots.push(node);
    } else {
      const parent = nodeMap.get(parentId);
      if (parent) {
        parent.children.push(node);
      } else {
        roots.push(node); // orphan fallback
      }
    }
  }

  // Set hasChildren flag
  function markChildren(node: TreeNode) {
    node.hasChildren = node.children.length > 0;
    for (const child of node.children) markChildren(child);
  }
  for (const root of roots) markChildren(root);

  return roots;
}

/**
 * Main entry: build navigation structure.
 * Returns chapters (top-level nodes) and flatList (reading order).
 */
export function buildNavigation(
  entries: { id: string; data: Record<string, any> }[]
): { chapters: TreeNode[]; flatList: TreeNode[] } {
  const published = entries
    .filter((e) => !e.data.draft)
    .sort((a, b) => a.id.localeCompare(b.id));

  const treeEntries: { sectionId: string; node: TreeNode }[] = [];

  for (const entry of published) {
    const slashIndex = entry.id.indexOf('/');
    const volume = slashIndex === -1 ? '' : entry.id.substring(0, slashIndex);
    const sectionId = slashIndex === -1 ? entry.id : entry.id.substring(slashIndex + 1);
    const depth = sectionId.split('-').length - 1;

    treeEntries.push({
      sectionId,
      node: {
        id: entry.id,
        sectionId,
        volume,
        title: entry.data.title,
        breadcrumb: entry.data.breadcrumb || [],
        url: idToUrl(entry.id),
        depth,
        children: [],
        hasChildren: false,
        isChapter: entry.data.isChapter || false,
        data: entry.data,
      },
    });
  }

  const chapters = buildTree(treeEntries);
  const flatList = flattenTree(chapters);

  return { chapters, flatList };
}

/** Get prev/next for reading navigation */
export function getReadingOrder(
  flatList: TreeNode[],
  currentId: string
): ReadingOrder | null {
  const index = flatList.findIndex((n) => n.id === currentId);
  if (index === -1) return null;
  return {
    prev: index > 0 ? flatList[index - 1] : null,
    current: flatList[index],
    next: index < flatList.length - 1 ? flatList[index + 1] : null,
  };
}
