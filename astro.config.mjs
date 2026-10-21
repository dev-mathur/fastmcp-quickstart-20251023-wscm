import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import rehypeCallouts from './plugins/rehype-callouts.mjs';

// GitHub Pages project site: https://<user>.github.io/<repo>/
// The deploy workflow can override both values with SITE_URL and BASE_PATH.
const site = process.env.SITE_URL ?? 'https://dev-mathur.github.io';
const base = process.env.BASE_PATH ?? '/devstack';

export default defineConfig({
  site,
  base,
  trailingSlash: 'always',
  integrations: [sitemap()],
  markdown: {
    processor: unified({ rehypePlugins: [rehypeCallouts] }),
  },
});
