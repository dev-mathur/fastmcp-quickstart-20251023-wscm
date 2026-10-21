// Turns a lone markdown image into a captioned figure and applies the site base path.
//
//   ![Alt text describing the diagram](/figures/<book-slug>/<name>.svg "Caption shown under the figure")
//
// Files live in public/figures/<book-slug>/. A src that starts with "/" gets the site base
// prepended (the site lives under /devstack/), so articles never hard-code the base.

function walk(node, visit) {
  visit(node);
  for (const child of node.children ?? []) walk(child, visit);
}

export default function rehypeFigures(options = {}) {
  const base = (options.base ?? '').replace(/\/$/, '');
  return (tree) => {
    walk(tree, (node) => {
      if (node.type !== 'element') return;
      if (node.tagName === 'img') {
        const src = String(node.properties?.src ?? '');
        if (src.startsWith('/') && !src.startsWith('//')) node.properties.src = `${base}${src}`;
        node.properties.loading = 'lazy';
        node.properties.decoding = 'async';
      }
      if (node.tagName !== 'p') return;
      const kids = (node.children ?? []).filter((c) => !(c.type === 'text' && !c.value.trim()));
      if (kids.length !== 1 || kids[0].type !== 'element' || kids[0].tagName !== 'img') return;
      const img = kids[0];
      const caption = String(img.properties?.title ?? '').trim();
      delete img.properties.title;
      node.tagName = 'figure';
      node.properties = { ...node.properties, className: ['figure'] };
      node.children = [img];
      if (caption) {
        node.children.push({
          type: 'element',
          tagName: 'figcaption',
          properties: {},
          children: [{ type: 'text', value: caption }],
        });
      }
    });
  };
}
