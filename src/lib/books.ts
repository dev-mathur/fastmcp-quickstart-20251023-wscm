import { getCollection, type CollectionEntry } from 'astro:content';
import taxonomy from '../data/taxonomy.json';

export type Book = CollectionEntry<'books'>;

export interface Topic {
  slug: string;
  name: string;
  description: string;
  hue: number;
}

export const allTopics: Topic[] = taxonomy.topics;

export function topicBySlug(slug: string): Topic | undefined {
  return allTopics.find((topic) => topic.slug === slug);
}

/** Published books, newest first. Drafts show up only in `astro dev`. */
export async function getBooks(): Promise<Book[]> {
  const books = await getCollection(
    'books',
    ({ data }) => import.meta.env.DEV || !data.draft,
  );
  return books.sort((a, b) => b.data.publishedAt.valueOf() - a.data.publishedAt.valueOf());
}

/** Topics that have at least one book, with counts, in taxonomy order. */
export async function getActiveTopics(): Promise<(Topic & { count: number })[]> {
  const books = await getBooks();
  return allTopics
    .map((topic) => ({
      ...topic,
      count: books.filter((book) => book.data.topic === topic.slug).length,
    }))
    .filter((topic) => topic.count > 0);
}

export function wordCount(body = ''): number {
  return body.split(/\s+/).filter(Boolean).length;
}

export function readingMinutes(body = ''): number {
  return Math.max(1, Math.round(wordCount(body) / 230));
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

/** Stable 0-2 value used to vary cover ornaments per book. */
export function coverVariant(slug: string): 'a' | 'b' | 'c' {
  let hash = 0;
  for (const char of slug) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return (['a', 'b', 'c'] as const)[hash % 3];
}
