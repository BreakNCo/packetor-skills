export type TocItem = {
  id: string;
  text: string;
  level: 2 | 3;
};

function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/<[^>]+>/g, "")
    .replace(/&[a-z]+;/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function extractToc(html: string): TocItem[] {
  const matches = html.matchAll(/<h([23])([^>]*)>([\s\S]*?)<\/h\1>/gi);
  const items: TocItem[] = [];
  for (const match of matches) {
    const level = Number(match[1]) as 2 | 3;
    const attrs = match[2] ?? "";
    const text = (match[3] ?? "").replace(/<[^>]+>/g, "").trim();
    if (!text) continue;
    const idMatch = attrs.match(/\sid=["']([^"']+)["']/i);
    items.push({ id: idMatch?.[1] ?? slugify(text), text, level });
  }
  return items;
}

export function countHeadings(html: string, level: 1 | 2 | 3) {
  const matches = html.match(new RegExp(`<h${level}\\b`, "gi"));
  return matches?.length ?? 0;
}

export function stripHtml(html: string) {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

export function countKeyword(text: string, keyword: string) {
  if (!keyword.trim()) return 0;
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = text.match(new RegExp(escaped, "gi"));
  return matches?.length ?? 0;
}

export function wordCount(text: string) {
  if (!text.trim()) return 0;
  return text.trim().split(/\s+/).length;
}
