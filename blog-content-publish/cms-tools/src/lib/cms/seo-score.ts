import { analyzeBodyHtml } from "./body-html";
import { countHeadings, countKeyword, stripHtml, wordCount } from "./toc";
import type { ArticleDraft } from "./types";

export type SeoCheckId =
  | "title"
  | "metaDescription"
  | "singleH1"
  | "keywordInTitle"
  | "keywordInH1"
  | "keywordInUrl"
  | "internalLinks"
  | "externalSources"
  | "imageAlt"
  | "author"
  | "reviewer"
  | "canonical"
  | "schema"
  | "cta"
  | "keywordDensity";

export type SeoCheck = {
  id: SeoCheckId;
  label: string;
  weight: number;
  pass: boolean;
  detail: string;
};

const WEIGHTS: Record<SeoCheckId, number> = {
  title: 10,
  metaDescription: 10,
  singleH1: 10,
  keywordInTitle: 8,
  keywordInH1: 8,
  keywordInUrl: 6,
  internalLinks: 8,
  externalSources: 6,
  imageAlt: 6,
  author: 8,
  reviewer: 8,
  canonical: 4,
  schema: 4,
  cta: 6,
  keywordDensity: 2,
};

function densityPercent(text: string, keyword: string) {
  const words = wordCount(text);
  if (!words || !keyword.trim()) return 0;
  return (countKeyword(text, keyword) / words) * 100;
}

export function scoreArticleDraft(draft: ArticleDraft): {
  checks: SeoCheck[];
  score: number;
} {
  const keyword = draft.primaryKeyword.trim();
  const bodyText = stripHtml(draft.bodyHtml);
  const fromBody = analyzeBodyHtml(draft.bodyHtml);
  const h1 = fromBody.h1;
  const h1Count = countHeadings(draft.bodyHtml, 1);
  const slug = draft.slug.toLowerCase();
  const density = densityPercent(`${draft.title} ${h1} ${bodyText}`, keyword);
  const densityOk = density >= 1 && density <= 2;
  const { internalLinksCount, sourcesCount, hasCta } = fromBody;
  const schemaConfigured = Boolean(draft.title.trim() && h1 && draft.slug.trim() && draft.authorSlug.trim());

  const checks: SeoCheck[] = [
    {
      id: "title",
      label: "Title exists",
      weight: WEIGHTS.title,
      pass: Boolean(draft.title.trim()),
      detail: draft.title.trim() ? draft.title : "Add a title",
    },
    {
      id: "metaDescription",
      label: "Meta description exists",
      weight: WEIGHTS.metaDescription,
      pass: draft.metaDescription.trim().length >= 50,
      detail:
        draft.metaDescription.trim().length >= 50
          ? `${draft.metaDescription.trim().length} characters`
          : "Write at least 50 characters",
    },
    {
      id: "singleH1",
      label: "Exactly one H1 in the article body",
      weight: WEIGHTS.singleH1,
      pass: h1Count === 1,
      detail: `Found ${h1Count}`,
    },
    {
      id: "keywordInTitle",
      label: "Primary keyword in title",
      weight: WEIGHTS.keywordInTitle,
      pass: Boolean(keyword) && draft.title.toLowerCase().includes(keyword.toLowerCase()),
      detail: keyword || "Set a primary keyword",
    },
    {
      id: "keywordInH1",
      label: "Primary keyword in H1",
      weight: WEIGHTS.keywordInH1,
      pass: Boolean(keyword) && h1.toLowerCase().includes(keyword.toLowerCase()),
      detail: h1 ? keyword || "Set a primary keyword" : "Add an H1 heading in the article body",
    },
    {
      id: "keywordInUrl",
      label: "Primary keyword in URL",
      weight: WEIGHTS.keywordInUrl,
      pass: Boolean(keyword) && slug.includes(keyword.toLowerCase().replace(/\s+/g, "-")),
      detail: slug || "Set a slug",
    },
    {
      id: "internalLinks",
      label: "Internal links present",
      weight: WEIGHTS.internalLinks,
      pass: internalLinksCount > 0,
      detail: `${internalLinksCount} internal links in the article body`,
    },
    {
      id: "externalSources",
      label: "External sources present",
      weight: WEIGHTS.externalSources,
      pass: sourcesCount > 0,
      detail: `${sourcesCount} external links in the article body`,
    },
    {
      id: "imageAlt",
      label: "Image alt text present",
      weight: WEIGHTS.imageAlt,
      pass: Boolean(draft.featuredImageAlt.trim()),
      detail: draft.featuredImageAlt.trim() || "Add alt text",
    },
    {
      id: "author",
      label: "Author assigned",
      weight: WEIGHTS.author,
      pass: Boolean(draft.authorSlug.trim()),
      detail: draft.authorSlug || "Assign an author",
    },
    {
      id: "reviewer",
      label: "Reviewer assigned",
      weight: WEIGHTS.reviewer,
      pass: Boolean(draft.reviewerSlug.trim()),
      detail: draft.reviewerSlug || "Assign a reviewer",
    },
    {
      id: "canonical",
      label: "Canonical configured",
      weight: WEIGHTS.canonical,
      pass: Boolean(draft.canonicalPath.trim()),
      detail: draft.canonicalPath || "Set a canonical path",
    },
    {
      id: "schema",
      label: "Schema configured",
      weight: WEIGHTS.schema,
      pass: schemaConfigured,
      detail: schemaConfigured ? "Article schema will render" : "Missing schema fields",
    },
    {
      id: "cta",
      label: "CTA present",
      weight: WEIGHTS.cta,
      pass: hasCta,
      detail: hasCta ? "CTA link found in the article body" : "Link to /contact, /early-access, or /audit-readiness",
    },
    {
      id: "keywordDensity",
      label: "Keyword density 1–2%",
      weight: WEIGHTS.keywordDensity,
      pass: densityOk,
      detail: `${density.toFixed(1)}%`,
    },
  ];

  const totalWeight = checks.reduce((sum, check) => sum + check.weight, 0);
  const earned = checks.reduce((sum, check) => sum + (check.pass ? check.weight : 0), 0);
  const score = totalWeight === 0 ? 0 : Math.round((earned / totalWeight) * 100);

  return { checks, score };
}

export function emptyArticleDraft(): ArticleDraft {
  return {
    title: "",
    h1: "",
    slug: "",
    bodyHtml: "",
    metaTitle: "",
    metaDescription: "",
    primaryKeyword: "",
    canonicalPath: "",
    featuredImageAlt: "",
    authorSlug: "",
    reviewerSlug: "",
    sourcesCount: 0,
    internalLinksCount: 0,
    hasCta: false,
    schemaConfigured: true,
  };
}
