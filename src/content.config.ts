import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// One markdown file per book in src/content/books/<slug>.md.
// The file name is the slug and becomes /books/<slug>/.
const books = defineCollection({
  loader: glob({ base: './src/content/books', pattern: '**/*.md' }),
  schema: z.object({
    // The article
    title: z.string().min(1), // must equal book.title (enforced by the validator)
    subtitle: z.string().min(20),
    publishedAt: z.coerce.date(),

    // The book it covers
    book: z.object({
      title: z.string(),
      author: z.string(),
      year: z.string().optional(), // free text, e.g. "2018" or "c. 5th century BCE"
      translator: z.string().optional(),
      pages: z.number().int().positive().optional(),
    }),

    // Taxonomy: `topic` must be a slug from src/data/taxonomy.json
    topic: z.string(),
    tags: z.array(z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/)).default([]),

    // Coverage: how many chapters the book has and what the author calls them.
    // The validator checks that the article mentions every one by number.
    chapters: z.number().int().positive(),
    unit: z.enum(['Chapter', 'Book', 'Part', 'Section']).default('Chapter'),

    // Presentation
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
    sample: z.boolean().default(false),

    // Provenance of the extraction (filled in by the ingestion agent)
    source: z
      .object({
        format: z.enum(['pdf', 'epub', 'text']),
        backend: z.string().optional(),
        words: z.number().int().positive().optional(),
      })
      .optional(),
  }),
});

export const collections = { books };
