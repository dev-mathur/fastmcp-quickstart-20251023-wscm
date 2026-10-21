import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getBooks } from '../lib/books';
import { site } from '../data/site';
import { url } from '../lib/paths';

export async function GET(context: APIContext) {
  const books = await getBooks();
  return rss({
    title: site.name,
    description: site.description,
    site: context.site!,
    items: books.map((book) => ({
      title: book.data.title,
      description: book.data.subtitle,
      pubDate: book.data.publishedAt,
      link: url(`/books/${book.id}/`),
    })),
  });
}
