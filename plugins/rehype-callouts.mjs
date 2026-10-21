// Turns two markdown conventions into styled blocks, with no extra dependencies.
//
//   > **Key takeaway.** One to three sentences.    -> <blockquote class="takeaway">
//   > "A short quote." <newline> — p. 38           -> <blockquote class="pullquote">
//
// Every other blockquote is left alone.

function textOf(node) {
  if (!node) return '';
  if (node.type === 'text') return node.value;
  return (node.children ?? []).map(textOf).join('');
}

function firstElement(node) {
  return (node.children ?? []).find((child) => child.type === 'element');
}

function walk(node, visit) {
  visit(node);
  for (const child of node.children ?? []) walk(child, visit);
}

export default function rehypeCallouts() {
  return (tree) => {
    walk(tree, (node) => {
      if (node.type !== 'element' || node.tagName !== 'blockquote') return;

      const paragraph = firstElement(node);
      const lead = paragraph?.tagName === 'p' ? firstElement(paragraph) : undefined;
      const isTakeaway =
        lead?.tagName === 'strong' && /^key takeaway/i.test(textOf(lead).trim());

      const className = isTakeaway ? 'takeaway' : 'pullquote';
      const existing = node.properties?.className ?? [];
      node.properties = {
        ...node.properties,
        className: [...(Array.isArray(existing) ? existing : [existing]), className],
      };
    });
  };
}
