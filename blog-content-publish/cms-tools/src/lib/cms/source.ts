import { mapArticle, mapPerson, type ArticleDoc, type PersonDoc } from "./payload-mapper";
import type { Article, Category, Person } from "./types";
import { getPayload } from "@/payload/get-payload";
import { categories as seedCategories } from "./content";

export function isPublishable(article: Article) {
  return Boolean(article.authorSlug && article.reviewerSlug && article.lastReviewedDate && article.seo.index);
}

async function withCmsFallback<T>(fallback: T, query: () => Promise<T>): Promise<T> {
  if (!process.env.DATABASE_URI || !process.env.PAYLOAD_SECRET) {
    return fallback;
  }

  try {
    return await query();
  } catch (error) {
    console.warn("[cms] query failed:", error instanceof Error ? error.message : error);
    return fallback;
  }
}

export async function getCategories(): Promise<Category[]> {
  return withCmsFallback(seedCategories, async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "categories",
      limit: 100,
      sort: "title",
    });
    return result.docs.map((doc) => ({
      slug: doc.slug as Category["slug"],
      title: doc.title,
      description: doc.description,
    }));
  });
}

export async function getPeople(): Promise<Person[]> {
  return withCmsFallback([], async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "people",
      limit: 100,
      sort: "name",
    });
    return result.docs.map((doc) => mapPerson(doc as PersonDoc)).filter((person): person is Person => Boolean(person));
  });
}

export async function getPersonBySlug(slug: string): Promise<Person | undefined> {
  return withCmsFallback(undefined, async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "people",
      where: { slug: { equals: slug } },
      limit: 1,
    });
    const person = result.docs[0] ? mapPerson(result.docs[0] as PersonDoc) : null;
    return person ?? undefined;
  });
}

export async function getPublishedArticles(): Promise<Article[]> {
  return withCmsFallback([], async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "articles",
      depth: 2,
      where: {
        and: [{ _status: { equals: "published" } }, { "seo.index": { equals: true } }],
      },
      sort: "-publishedDate",
      limit: 200,
    });

    return result.docs
      .map((doc) => mapArticle(doc as ArticleDoc))
      .filter((article): article is Article => Boolean(article && isPublishable(article)));
  });
}

export async function getArticleBySlug(slug: string): Promise<Article | undefined> {
  return withCmsFallback(undefined, async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "articles",
      depth: 2,
      where: {
        and: [{ slug: { equals: slug } }, { _status: { equals: "published" } }],
      },
      limit: 1,
    });

    const article = result.docs[0] ? mapArticle(result.docs[0] as ArticleDoc) : null;
    return article ?? undefined;
  });
}

export async function getArticlesByAuthor(slug: string): Promise<Article[]> {
  return withCmsFallback([], async () => {
    const payload = await getPayload();
    const personResult = await payload.find({
      collection: "people",
      where: { slug: { equals: slug } },
      limit: 1,
    });
    const personDoc = personResult.docs[0];
    if (!personDoc) return [];

    const result = await payload.find({
      collection: "articles",
      depth: 2,
      where: {
        and: [
          { _status: { equals: "published" } },
          {
            or: [{ author: { equals: personDoc.id } }, { reviewer: { equals: personDoc.id } }],
          },
        ],
      },
      sort: "-publishedDate",
      limit: 100,
    });

    return result.docs.map((doc) => mapArticle(doc as ArticleDoc)).filter((article): article is Article => Boolean(article));
  });
}

export async function getRelatedArticles(article: Article): Promise<Article[]> {
  if (article.relatedArticleSlugs.length === 0) return [];

  return withCmsFallback([], async () => {
    const payload = await getPayload();
    const result = await payload.find({
      collection: "articles",
      depth: 2,
      where: {
        and: [{ slug: { in: article.relatedArticleSlugs } }, { _status: { equals: "published" } }],
      },
      limit: article.relatedArticleSlugs.length,
    });

    return result.docs.map((doc) => mapArticle(doc as ArticleDoc)).filter((item): item is Article => Boolean(item));
  });
}
