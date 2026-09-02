import { SITE_URL } from "@/lib/seo/site";
import { stripHtml } from "./toc";

const CTA_PATHS = ["/contact", "/early-access", "/audit-readiness"];

export function extractH1(html: string): string {
  const match = html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i);
  if (!match) return "";
  return stripHtml(match[1] ?? "");
}

/** Remove the first H1 so the page can render it as the article title without duplicating. */
export function stripFirstH1(html: string): string {
  return html.replace(/<h1\b[^>]*>[\s\S]*?<\/h1>/i, "").trim();
}

function hrefPath(href: string): string | null {
  if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) {
    return null;
  }
  try {
    if (href.startsWith("http://") || href.startsWith("https://")) {
      return new URL(href).pathname;
    }
  } catch {
    return null;
  }
  const withoutQuery = href.split("?")[0] ?? href;
  return withoutQuery.split("#")[0] ?? withoutQuery;
}

function isInternalHref(href: string): boolean {
  if (href.startsWith("/")) return true;
  try {
    const site = new URL(SITE_URL);
    const target = new URL(href);
    return target.hostname === site.hostname || target.hostname.endsWith(`.${site.hostname}`);
  } catch {
    return false;
  }
}

export function analyzeBodyHtml(html: string): {
  h1: string;
  internalLinksCount: number;
  sourcesCount: number;
  hasCta: boolean;
} {
  const hrefs = [...html.matchAll(/\shref=["']([^"']+)["']/gi)].map((match) => match[1] ?? "");
  let internalLinksCount = 0;
  let sourcesCount = 0;
  let hasCta = false;

  for (const href of hrefs) {
    const path = hrefPath(href);
    if (!path) continue;
    if (CTA_PATHS.some((cta) => path === cta || path.startsWith(`${cta}/`))) {
      hasCta = true;
    }
    if (isInternalHref(href)) {
      internalLinksCount += 1;
    } else {
      sourcesCount += 1;
    }
  }

  return {
    h1: extractH1(html),
    internalLinksCount,
    sourcesCount,
    hasCta,
  };
}
