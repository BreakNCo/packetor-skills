type LexicalNode = {
  children?: LexicalNode[];
  fields?: { url?: string | null; linkType?: string | null };
  listType?: string;
  tag?: string;
  text?: string;
  type?: string;
  url?: string | null;
};

function isNode(value: unknown): value is LexicalNode {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function serialize(node: LexicalNode): string {
  const children = (node.children ?? []).map(serialize).join("");

  if (node.type === "text") return node.text ?? "";
  if (node.type === "linebreak") return "\n";
  if (node.type === "heading" && node.tag) return `<${node.tag}>${children}</${node.tag}>`;
  if (node.type === "paragraph") return `<p>${children}</p>`;
  if (node.type === "listitem") return `<li>${children}</li>`;
  if (node.type === "list") {
    const tag = node.listType === "number" ? "ol" : "ul";
    return `<${tag}>${children}</${tag}>`;
  }
  if (node.type === "quote") return `<blockquote>${children}</blockquote>`;
  if (node.type === "link" || node.type === "autolink") {
    const href = node.fields?.url || node.url || "";
    return href ? `<a href="${href}">${children}</a>` : children;
  }
  return children;
}

/** Flatten Lexical JSON into simple HTML so the SEO scorer can count headings and keywords. */
export function lexicalToSimpleHtml(data: unknown): string {
  if (!data) return "";
  if (typeof data === "string") return data;
  if (!isNode(data)) return "";

  const nested = "root" in data ? (data as { root: unknown }).root : null;
  const root = data.type === "root" ? data : isNode(nested) ? nested : null;
  if (!root) return "";
  return serialize(root);
}
