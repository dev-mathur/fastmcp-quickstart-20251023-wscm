import type { APIRoute } from 'astro';
import { getBooks, readingMinutes, topicBySlug } from '../lib/books';
import { url } from '../lib/paths';

function plain(markdown: string): string {
  return markdown
    .replace(/<[^>]+>/g, ' ')
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_`|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export const GET: APIRoute = async () => {
  const books = await getBooks();
  const index = books.map((book) => ({
    title: book.data.title,
    subtitle: book.data.subtitle,
    book: book.data.book.title,
    author: book.data.book.author,
    topic: topicBySlug(book.data.topic)?.name ?? '',
    tags: book.data.tags,
    minutes: readingMinutes(book.body),
    url: url(`/books/${book.id}/`),
    text: plain(book.body ?? '').slice(0, 12000),
  }));

  return new Response(JSON.stringify(index), {
    headers: { 'Content-Type': 'application/json' },
  });
};
