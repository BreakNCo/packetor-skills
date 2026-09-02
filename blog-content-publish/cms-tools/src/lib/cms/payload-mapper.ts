import { convertLexicalToHTML } from "@payloadcms/richtext-lexical/html";
import type { SerializedEditorState } from "lexical";
import { extractH1 } from "./body-html";
import type { Article, ArticleCategorySlug, Person } from "./types";

type MediaDoc = { url?: string | null; alt?: string | null };
export type PersonDoc = {
  slug?: string | null;
  name?: string | null;
  role?: Person["role"] | null;
  bio?: string | null;
  statedExpertise?: string | null;
  credentials?: string | null;
  linkedIn?: string | null;
  headshot?: MediaDoc | number | null;
};
type CategoryDoc = { slug?: string | null };
export type ArticleDoc = {
  slug?: string | null;
  title?: string | null;
  excerpt?: string | null;
  body?: SerializedEditorState | null;
  featuredImage?: MediaDoc | number | null;
  featuredImageAlt?: string | null;
  author?: PersonDoc | number | null;
  reviewer?: PersonDoc | number | null;
  category?: CategoryDoc | number | null;
  tags?: Array<{ slug?: string | null; name?: string | null } | number> | null;
  publishedDate?: string | null;
  updatedDate?: string | null;
  lastReviewedDate?: string | null;
  seo?: {
    primaryKeyword?: string | null;
    secondaryKeywords?: string[] | null;
    metaTitle?: string | null;
    metaDescription?: string | null;
    canonicalPath?: string | null;
    index?: boolean | null;
    follow?: boolean | null;
    ogTitle?: string | null;
    ogDescription?: string | null;
    ogImage?: MediaDoc | number | null;
  } | null;
  relatedArticles?: Array<{ slug?: string | null; title?: string | null; excerpt?: string | null } | number> | null;
};

function isPopulated<T extends object>(value: T | number | null | undefined): value is T {
  return Boolean(value) && typeof value === "object";
}

function mediaUrl(media: MediaDoc | number | null | undefined) {
  if (!isPopulated(media)) return undefined;
  return media.url ?? undefined;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "";
  return value.slice(0, 10);
}

export function mapPerson(doc: PersonDoc): Person | null {
  if (!doc.slug || !doc.name || !doc.role || !doc.bio || !doc.statedExpertise || !doc.credentials) {
    return null;
  }

  return {
    slug: doc.slug,
    name: doc.name,
    role: doc.role,
    bio: doc.bio,
    statedExpertise: doc.statedExpertise,
    credentials: doc.credentials,
    linkedIn: doc.linkedIn ?? undefined,
    headshotSrc: mediaUrl(isPopulated(doc.headshot) ? doc.headshot : null),
  };
}

export function mapArticle(doc: ArticleDoc): Article | null {
  const author = isPopulated(doc.author) ? mapPerson(doc.author) : null;
  const reviewer = isPopulated(doc.reviewer) ? mapPerson(doc.reviewer) : null;
  const categorySlug = isPopulated(doc.category) ? doc.category.slug : null;

  if (
    !doc.slug ||
    !doc.title ||
    !doc.excerpt ||
    !author ||
    !reviewer ||
    !categorySlug ||
    !doc.lastReviewedDate
  ) {
    return null;
  }

  const bodyHtml = doc.body ? convertLexicalToHTML({ data: doc.body }) : "";
  const h1 = extractH1(bodyHtml) || doc.title;
  const seo = doc.seo ?? {};

  return {
    slug: doc.slug,
    title: doc.title,
    h1,
    excerpt: doc.excerpt,
    bodyHtml,
    featuredImageSrc: mediaUrl(isPopulated(doc.featuredImage) ? doc.featuredImage : null),
    featuredImageAlt: doc.featuredImageAlt ?? undefined,
    authorSlug: author.slug,
    reviewerSlug: reviewer.slug,
    category: categorySlug as ArticleCategorySlug,
    tags: (doc.tags ?? [])
      .map((tag) => (isPopulated(tag) ? tag.slug : null))
      .filter((slug): slug is string => Boolean(slug)),
    publishedDate: formatDate(doc.publishedDate),
    updatedDate: formatDate(doc.updatedDate ?? doc.publishedDate),
    lastReviewedDate: formatDate(doc.lastReviewedDate),
    seo: {
      primaryKeyword: seo.primaryKeyword ?? "",
      secondaryKeywords: seo.secondaryKeywords ?? [],
      metaTitle: seo.metaTitle ?? doc.title,
      metaDescription: seo.metaDescription ?? doc.excerpt,
      canonicalPath: seo.canonicalPath ?? `/blog/${doc.slug}`,
      index: seo.index ?? true,
      follow: seo.follow ?? true,
      ogTitle: seo.ogTitle ?? undefined,
      ogDescription: seo.ogDescription ?? undefined,
      ogImageSrc: mediaUrl(isPopulated(seo.ogImage) ? seo.ogImage : null),
    },
    relatedArticleSlugs: (doc.relatedArticles ?? [])
      .map((item) => (isPopulated(item) ? item.slug : null))
      .filter((slug): slug is string => Boolean(slug)),
  };
}

export function mapRelatedArticlePreview(doc: ArticleDoc) {
  if (!doc.slug || !doc.title || !doc.excerpt) return null;
  return { slug: doc.slug, title: doc.title, excerpt: doc.excerpt };
}
