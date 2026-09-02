export const PERSON_ROLES = ["author", "reviewer", "both"] as const;
export type PersonRole = (typeof PERSON_ROLES)[number];

export const ARTICLE_CATEGORIES = [
  "soc-2-for-ai-companies",
  "iso-27001-for-ai-companies",
  "india-compliance",
  "ai-governance",
] as const;
export type ArticleCategorySlug = (typeof ARTICLE_CATEGORIES)[number];

export type Person = {
  slug: string;
  name: string;
  role: PersonRole;
  bio: string;
  statedExpertise: string;
  credentials: string;
  linkedIn?: string;
  headshotSrc?: string;
};

export type Category = {
  slug: ArticleCategorySlug;
  title: string;
  description: string;
};

export type Citation = {
  title: string;
  url: string;
  publisher?: string;
};

export type RelatedLink = {
  href: string;
  label: string;
};

export type ArticleSeo = {
  primaryKeyword: string;
  secondaryKeywords: string[];
  metaTitle: string;
  metaDescription: string;
  canonicalPath: string;
  index: boolean;
  follow: boolean;
  ogTitle?: string;
  ogDescription?: string;
  ogImageSrc?: string;
};

export type Article = {
  slug: string;
  title: string;
  h1: string;
  excerpt: string;
  bodyHtml: string;
  featuredImageSrc?: string;
  featuredImageAlt?: string;
  authorSlug: string;
  reviewerSlug: string;
  category: ArticleCategorySlug;
  tags: string[];
  publishedDate: string;
  updatedDate: string;
  lastReviewedDate: string;
  seo: ArticleSeo;
  relatedArticleSlugs: string[];
};

export type ArticleDraft = {
  title: string;
  h1: string;
  slug: string;
  bodyHtml: string;
  metaTitle: string;
  metaDescription: string;
  primaryKeyword: string;
  canonicalPath: string;
  featuredImageAlt: string;
  authorSlug: string;
  reviewerSlug: string;
  sourcesCount: number;
  internalLinksCount: number;
  hasCta: boolean;
  schemaConfigured: boolean;
};
