#!/usr/bin/env node
// Validates every article in src/content/books before the site builds.
// Errors fail the build. Warnings are printed but do not.
//
// Checks:
//   - article title equals the book title
//   - frontmatter fields, topic exists in taxonomy.json, tags are kebab-case
//   - file name is a kebab-case slug, and no two files cover the same book
//   - every chapter 1..N is mentioned by number (so no chapter is silently skipped)
//   - every pull quote is 15 words or fewer
//   - the article has "Remember this" notes and recall questions

import { readdirSync, readFileSync } from 'node:fs';
import { join, basename, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse as parseYaml } from 'yaml';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const booksDir = join(root, 'src/content/books');
const taxonomy = JSON.parse(readFileSync(join(root, 'src/data/taxonomy.json'), 'utf8'));
const topicSlugs = new Set(taxonomy.topics.map((topic) => topic.slug));

const MAX_QUOTE_WORDS = 15;
const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const errors = [];
const warnings = [];
const err = (file, message) => errors.push(`${file}: ${message}`);
const warn = (file, message) => warnings.push(`${file}: ${message}`);

function splitFrontmatter(raw) {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) return null;
  return { data: parseYaml(match[1]) ?? {}, body: match[2], bodyOffset: raw.slice(0, raw.length - match[2].length).split('\n').length - 1 };
}

/** Chapter numbers mentioned in text: "Chapter 3", "Chapters 4 and 5", "Chapters 7 through 9", "Chapters 2-4". */
function mentionedUnits(body, unit) {
  const separator = String.raw`(?:\s*[-–—]\s*|\s+(?:to|through)\s+|\s*,\s*(?:and\s+|&\s*)?|\s+(?:and|&)\s+)`;
  const pattern = new RegExp(String.raw`\b${unit}s?\s+(\d+(?:${separator}\d+)*)`, 'gi');
  const found = new Set();
  for (const match of body.matchAll(pattern)) {
    const numbers = [];
    let range = false;
    for (const token of match[1].matchAll(/(\d+)|(\s*[-–—]\s*|\s+to\s+|\s+through\s+)/g)) {
      if (token[1]) {
        const value = Number(token[1]);
        if (range && numbers.length) {
          for (let n = numbers[numbers.length - 1] + 1; n <= value; n++) numbers.push(n);
          range = false;
        } else {
          numbers.push(value);
        }
      } else {
        range = true;
      }
    }
    numbers.forEach((n) => found.add(n));
  }
  return found;
}

/** Pull quotes: blockquotes that are not "Remember this" callouts. Attribution lines starting with a dash are ignored. */
function checkQuotes(file, body, bodyOffset) {
  const lines = body.split('\n');
  let block = [];
  let start = 0;
  const flush = () => {
    if (block.length === 0) return;
    const paragraphs = block
      .join('\n')
      .split(/\n\s*\n/)
      .map((paragraph) => paragraph.replace(/\s+/g, ' ').trim())
      .filter(Boolean);
    const isRemember = /^\*\*Remember/i.test(paragraphs[0] ?? '');
    if (!isRemember) {
      const quoted = paragraphs.filter((paragraph) => !/^[—–-]\s/.test(paragraph)).join(' ');
      const words = quoted.split(/\s+/).filter(Boolean).length;
      if (words > MAX_QUOTE_WORDS) {
        err(file, `line ${start + bodyOffset + 1}: pull quote is ${words} words (limit ${MAX_QUOTE_WORDS})`);
      }
    }
    block = [];
  };
  lines.forEach((line, index) => {
    if (/^\s*>/.test(line)) {
      if (block.length === 0) start = index;
      block.push(line.replace(/^\s*>\s?/, ''));
    } else {
      flush();
    }
  });
  flush();
}

const files = readdirSync(booksDir).filter((name) => name.endsWith('.md')).sort();
if (files.length === 0) warn('src/content/books', 'no articles found');

const identities = new Map();
let featuredCount = 0;
let sampleCount = 0;

for (const name of files) {
  const file = `src/content/books/${name}`;
  const slug = basename(name, '.md');
  const parsed = splitFrontmatter(readFileSync(join(booksDir, name), 'utf8'));

  if (!parsed) {
    err(file, 'missing frontmatter block');
    continue;
  }
  const { data, body, bodyOffset } = parsed;

  if (!KEBAB.test(slug)) err(file, 'file name must be a kebab-case slug, e.g. atomic-habits.md');

  for (const field of ['title', 'subtitle', 'publishedAt', 'topic', 'chapters']) {
    if (data[field] === undefined || data[field] === null || data[field] === '') err(file, `frontmatter is missing "${field}"`);
  }
  if (!data.book?.title || !data.book?.author) err(file, 'frontmatter needs book.title and book.author');
  if (data.title && data.book?.title && data.title.trim() !== data.book.title.trim()) {
    err(file, `title "${data.title}" must be exactly the book title "${data.book.title}" (put the angle in the subtitle)`);
  }
  if (data.publishedAt && Number.isNaN(new Date(data.publishedAt).getTime())) err(file, 'publishedAt is not a valid date');
  if (data.topic && !topicSlugs.has(data.topic)) {
    err(file, `topic "${data.topic}" is not in src/data/taxonomy.json (known: ${[...topicSlugs].join(', ')})`);
  }
  for (const tag of data.tags ?? []) {
    if (!KEBAB.test(tag)) err(file, `tag "${tag}" must be kebab-case`);
  }
  if (data.featured) featuredCount += 1;
  if (data.sample) sampleCount += 1;

  const identity = `${data.book?.title ?? ''}|${data.book?.author ?? ''}`.toLowerCase();
  if (identities.has(identity)) err(file, `duplicates the book already covered in ${identities.get(identity)}`);
  else identities.set(identity, file);

  if (/^# /m.test(body)) warn(file, 'body contains an H1; the page title already comes from frontmatter');

  // Chapter coverage
  if (Number.isInteger(data.chapters)) {
    const unit = data.unit ?? 'Chapter';
    const found = mentionedUnits(body, unit);
    const missing = [];
    for (let n = 1; n <= data.chapters; n++) if (!found.has(n)) missing.push(n);
    if (missing.length > 0) {
      err(file, `${unit}s not mentioned by number: ${missing.join(', ')} (of ${data.chapters})`);
    }
  }

  checkQuotes(file, body, bodyOffset);

  // Structure
  const words = body.split(/\s+/).filter(Boolean).length;
  const h2 = (body.match(/^## /gm) ?? []).length;
  const remember = (body.match(/^>\s*\*\*Remember/gim) ?? []).length;
  const questions = (body.match(/<details>/g) ?? []).length;

  if (words < 800) err(file, `article is only ${words} words; expected a long-form article`);
  else if (words < 1500) warn(file, `article is ${words} words, which is short for a full book`);
  if (h2 < 4) warn(file, `only ${h2} H2 sections; the contents rail works best with 6 or more`);
  if (remember === 0) warn(file, 'no "Remember this" notes found');
  if (questions < 8) warn(file, `only ${questions} recall questions (<details> blocks); aim for 12-20`);
}

if (featuredCount > 1) warn('src/content/books', `${featuredCount} articles are marked featured; only the first is shown in the hero`);

console.log(`Validated ${files.length} article${files.length === 1 ? '' : 's'}.`);
if (sampleCount > 0) console.log(`Note: ${sampleCount} sample article${sampleCount === 1 ? ' is' : 's are'} present (sample: true).`);
for (const message of warnings) console.warn(`  warning  ${message}`);
for (const message of errors) console.error(`  error    ${message}`);

if (errors.length > 0) {
  console.error(`\n${errors.length} error${errors.length === 1 ? '' : 's'}. Fix them and run "npm run validate" again.`);
  process.exit(1);
}
console.log('Content is valid.');
