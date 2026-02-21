import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const novel = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/novel' }),
  schema: z.object({
    title: z.string(),
    breadcrumb: z.array(z.string()),
    draft: z.boolean().default(false),
    publishDate: z.string().optional(),

    // ── Chapter-level fields (optional, for depth-0 nodes) ──
    /** e.g. "第四章", "楔子", "间章", "尾声" */
    chapterLabel: z.string().optional(),
    /** Latin or other subtitle below the title */
    subtitle: z.string().optional(),
    /** Segmented subtitle hover data */
    subtitleSegments: z.array(z.object({
      chars: z.string(),
      note: z.string(),
    })).optional(),
    /** Whether this is a chapter-level node with special title page */
    isChapter: z.boolean().default(false),
    /** Optional cover/splash image path (relative to public/) */
    coverImage: z.string().optional(),
  }),
});

export const collections = { novel };
