/**
 * Nushu inline markup parser.
 *
 * Syntax:  {nushu|汉字}           → default (calt)
 *          {nushu:original|汉字}  → ss01 original calligraphy
 *          {nushu:alt|汉字}       → ss03 variant strokes
 *
 * Used in frontmatter fields (title, breadcrumb, chapterLabel, etc.)
 * so that visual nüshu rendering works everywhere without JSX.
 */

export interface NushuSegment {
  type: 'text' | 'nushu';
  content: string;
  /** Only for type 'nushu': 'original' | 'alt' | undefined (default) */
  variant?: string;
}

const NUSHU_RE = /\{nushu(?::(\w+))?\|([^}]+)\}/g;

/**
 * Parse a string containing {nushu|...} markup into segments.
 * Plain strings with no markup return a single text segment.
 */
export function parseNushuMarkup(text: string): NushuSegment[] {
  const segments: NushuSegment[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(NUSHU_RE)) {
    const [full, variant, content] = match;
    const idx = match.index!;

    // Text before this match
    if (idx > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, idx) });
    }

    segments.push({ type: 'nushu', content, variant });
    lastIndex = idx + full.length;
  }

  // Remaining text
  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) });
  }

  return segments;
}

/**
 * Check if a string contains any nushu markup.
 */
export function hasNushuMarkup(text: string): boolean {
  return NUSHU_RE.test(text);
}

/**
 * Strip nushu markup, returning plain text (for <title> tags, aria-labels, etc.)
 */
export function stripNushuMarkup(text: string): string {
  return text.replace(NUSHU_RE, '$2');
}

/**
 * Convert nushu markup to HTML string (for client-side JS rendering).
 * Output is safe to assign to innerHTML since content comes from
 * author-controlled frontmatter, not user input.
 */
export function nushuMarkupToHtml(text: string): string {
  return text.replace(NUSHU_RE, (_full, variant, content) => {
    const cls = variant === 'original' ? 'nushu nushu-original'
              : variant === 'alt' ? 'nushu nushu-alt'
              : 'nushu';
    return `<span class="${cls}">${escapeHtml(content)}</span>`;
  });
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
