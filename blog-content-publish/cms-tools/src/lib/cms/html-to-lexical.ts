/** Convert a constrained HTML subset into Payload Lexical JSON.
 *
 * Supported tags: h1, h2, h3, p, a[href], ul, li, strong, em.
 * Throws on any other tag so scored fields never silently drop markup.
 */

export type LexicalTextNode = {
  type: "text";
  text: string;
  format: number;
  mode: "normal";
  style: string;
  detail: number;
  version: 1;
};

export type LexicalElementNode = {
  type: string;
  children: LexicalNode[];
  version: number;
  format: string | number;
  indent: number;
  direction: "ltr";
  tag?: string;
  listType?: string;
  start?: number;
  value?: number;
  fields?: { linkType: "custom"; url: string; newTab: boolean };
};

export type LexicalNode = LexicalTextNode | LexicalElementNode;

export type LexicalRoot = {
  root: LexicalElementNode;
};

const ALLOWED_TAGS = new Set(["h1", "h2", "h3", "p", "a", "ul", "li", "strong", "em"]);
const BLOCK_TAGS = new Set(["h1", "h2", "h3", "p", "ul"]);
const IS_BOLD = 1;
const IS_ITALIC = 2;

type Token =
  | { kind: "text"; value: string }
  | { kind: "open"; tag: string; attrs: Record<string, string> }
  | { kind: "close"; tag: string };

function decodeEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'");
}

function parseAttrs(raw: string): Record<string, string> {
  const attrs: Record<string, string> = {};
  const re = /([a-zA-Z_:][\w:.-]*)\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+))/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(raw))) {
    const name = (match[1] ?? "").toLowerCase();
    const value = match[3] ?? match[4] ?? match[5] ?? "";
    attrs[name] = decodeEntities(value);
  }
  return attrs;
}

function tokenize(html: string): Token[] {
  const tokens: Token[] = [];
  const re = /<!--[\s\S]*?-->|<(\/)?([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>|([^<]+)/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(html))) {
    if (match[0].startsWith("<!--")) continue;
    if (match[4] != null) {
      tokens.push({ kind: "text", value: decodeEntities(match[4]) });
      continue;
    }
    const tag = (match[2] ?? "").toLowerCase();
    const rest = match[3] ?? "";
    if (rest.trimEnd().endsWith("/")) {
      throw new Error(`Unsupported HTML tag: <${tag}>`);
    }
    if (!ALLOWED_TAGS.has(tag)) {
      throw new Error(`Unsupported HTML tag: <${tag}>`);
    }
    if (match[1]) tokens.push({ kind: "close", tag });
    else tokens.push({ kind: "open", tag, attrs: parseAttrs(rest) });
  }
  return tokens;
}

function textNode(text: string, format: number): LexicalTextNode {
  return {
    type: "text",
    text,
    format,
    mode: "normal",
    style: "",
    detail: 0,
    version: 1,
  };
}

function element(
  partial: Omit<LexicalElementNode, "format" | "indent" | "direction" | "version"> &
    Partial<LexicalElementNode>,
): LexicalElementNode {
  return {
    format: "",
    indent: 0,
    direction: "ltr",
    version: 1,
    ...partial,
  };
}

function mergeText(nodes: LexicalNode[]): LexicalNode[] {
  const out: LexicalNode[] = [];
  for (const node of nodes) {
    const prev = out[out.length - 1];
    if (node.type === "text" && prev && prev.type === "text" && prev.format === node.format) {
      prev.text += node.text;
    } else {
      out.push(node);
    }
  }
  return out;
}

function parseInline(tokens: Token[], endTag?: string): { nodes: LexicalNode[]; consumed: number } {
  const nodes: LexicalNode[] = [];
  let i = 0;
  let format = 0;

  while (i < tokens.length) {
    const token = tokens[i];
    if (!token) break;

    if (token.kind === "close") {
      if (endTag && token.tag === endTag) {
        return { nodes: mergeText(nodes), consumed: i + 1 };
      }
      if (token.tag === "strong") {
        format &= ~IS_BOLD;
        i += 1;
        continue;
      }
      if (token.tag === "em") {
        format &= ~IS_ITALIC;
        i += 1;
        continue;
      }
      throw new Error(`Unexpected closing tag: </${token.tag}>`);
    }

    if (token.kind === "text") {
      if (token.value) nodes.push(textNode(token.value, format));
      i += 1;
      continue;
    }

    if (BLOCK_TAGS.has(token.tag) || token.tag === "li") {
      throw new Error(`Block tag <${token.tag}> is not allowed in inline content`);
    }

    if (token.tag === "strong") {
      format |= IS_BOLD;
      i += 1;
      continue;
    }
    if (token.tag === "em") {
      format |= IS_ITALIC;
      i += 1;
      continue;
    }
    if (token.tag === "a") {
      const href = token.attrs.href;
      if (!href) throw new Error("Link tag is missing href");
      const inner = parseInline(tokens.slice(i + 1), "a");
      nodes.push(
        element({
          type: "link",
          version: 3,
          fields: { linkType: "custom", url: href, newTab: false },
          children: inner.nodes.map((child) =>
            child.type === "text" ? { ...child, format: child.format | format } : child,
          ),
        }),
      );
      i += 1 + inner.consumed;
      continue;
    }

    throw new Error(`Unsupported HTML tag: <${token.tag}>`);
  }

  if (endTag) throw new Error(`Unclosed tag: <${endTag}>`);
  return { nodes: mergeText(nodes), consumed: i };
}

/** Parse inline HTML (a, strong, em, text) into Lexical children. */
export function inlineHtmlToLexicalChildren(html: string): LexicalNode[] {
  return parseInline(tokenize(html)).nodes;
}

function takeUntil(tokens: Token[], start: number, tag: string): { inner: Token[]; next: number } {
  let depth = 1;
  for (let i = start; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (!token) break;
    if (token.kind === "open" && token.tag === tag) depth += 1;
    if (token.kind === "close" && token.tag === tag) {
      depth -= 1;
      if (depth === 0) {
        return { inner: tokens.slice(start, i), next: i + 1 };
      }
    }
  }
  throw new Error(`Unclosed tag: <${tag}>`);
}

function headingOrParagraph(tag: "h1" | "h2" | "h3" | "p", inner: Token[]): LexicalElementNode {
  return element({
    type: tag === "p" ? "paragraph" : "heading",
    tag: tag === "p" ? undefined : tag,
    children: parseInline(inner).nodes,
  });
}

function parseList(inner: Token[]): LexicalElementNode {
  const items: LexicalElementNode[] = [];
  let i = 0;
  let value = 1;
  while (i < inner.length) {
    const token = inner[i];
    if (!token) break;
    if (token.kind === "text" && !token.value.trim()) {
      i += 1;
      continue;
    }
    if (!(token.kind === "open" && token.tag === "li")) {
      throw new Error("List children must be <li> elements");
    }
    const taken = takeUntil(inner, i + 1, "li");
    items.push(
      element({
        type: "listitem",
        value,
        children: parseInline(taken.inner).nodes,
      }),
    );
    value += 1;
    i = taken.next;
  }
  return element({
    type: "list",
    listType: "bullet",
    tag: "ul",
    start: 1,
    children: items,
  });
}

export function htmlToLexical(html: string): LexicalRoot {
  const tokens = tokenize(html.trim());
  const children: LexicalNode[] = [];
  let i = 0;
  let pending: Token[] = [];

  const flushInline = () => {
    if (pending.length === 0) return;
    const nodes = parseInline(pending).nodes;
    pending = [];
    const hasContent = nodes.some((node) => node.type !== "text" || node.text.trim());
    if (!hasContent) return;
    children.push(element({ type: "paragraph", children: nodes }));
  };

  while (i < tokens.length) {
    const token = tokens[i];
    if (!token) break;

    if (token.kind === "text" || (token.kind === "open" && (token.tag === "strong" || token.tag === "em" || token.tag === "a"))) {
      pending.push(token);
      i += 1;
      continue;
    }
    if (token.kind === "close" && (token.tag === "strong" || token.tag === "em" || token.tag === "a")) {
      pending.push(token);
      i += 1;
      continue;
    }
    if (token.kind === "close") {
      throw new Error(`Unexpected closing tag: </${token.tag}>`);
    }

    flushInline();
    if (!BLOCK_TAGS.has(token.tag)) {
      throw new Error(`Unsupported HTML tag: <${token.tag}>`);
    }
    const taken = takeUntil(tokens, i + 1, token.tag);
    if (token.tag === "ul") {
      children.push(parseList(taken.inner));
    } else {
      children.push(headingOrParagraph(token.tag as "h1" | "h2" | "h3" | "p", taken.inner));
    }
    i = taken.next;
  }
  flushInline();

  return {
    root: element({
      type: "root",
      children,
    }),
  };
}
