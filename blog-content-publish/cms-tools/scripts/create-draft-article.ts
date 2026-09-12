import { htmlToLexical } from "../src/lib/cms/html-to-lexical";
import { getPayload } from "../src/payload/get-payload";

type DraftInput = {
  title?: string;
  slug?: string;
  excerpt?: string;
  bodyHtml?: string;
  featuredImageAlt?: string;
  authorSlug?: string;
  reviewerSlug?: string;
  categorySlug?: string;
  tags?: string[];
  relatedArticleSlugs?: string[];
  status?: string;
  _status?: string;
  seo?: {
    primaryKeyword?: string;
    secondaryKeywords?: string[];
    metaTitle?: string;
    metaDescription?: string;
    canonicalPath?: string;
    ogTitle?: string;
    ogDescription?: string;
    index?: boolean;
    follow?: boolean;
  };
};

function requireCmsEnv() {
  if (!process.env.DATABASE_URI || !process.env.PAYLOAD_SECRET) {
    throw new Error("DATABASE_URI and PAYLOAD_SECRET must be set (packetor-skills/.env).");
  }
}

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

async function findBySlug(
  payload: Awaited<ReturnType<typeof getPayload>>,
  collection: "people" | "categories" | "tags" | "articles",
  slug: string,
) {
  const result = await payload.find({
    collection,
    where: { slug: { equals: slug } },
    limit: 1,
    draft: collection === "articles",
  });
  return result.docs[0] ?? null;
}

async function resolvePerson(
  payload: Awaited<ReturnType<typeof getPayload>>,
  slug: string,
  role: "author" | "reviewer",
): Promise<string | undefined> {
  if (!slug) return undefined;
  const person = await findBySlug(payload, "people", slug);
  if (!person) {
    process.stderr.write(`Warning: ${role} slug "${slug}" not found; leaving unset (drafts do not require E-E-A-T).\n`);
    return undefined;
  }
  return person.id as string;
}

async function ensureTag(payload: Awaited<ReturnType<typeof getPayload>>, raw: string): Promise<string> {
  const slug = slugify(raw);
  const existing = await findBySlug(payload, "tags", slug);
  if (existing) return existing.id as string;
  const created = await payload.create({
    collection: "tags",
    data: { name: raw.trim() || slug, slug },
  });
  return created.id as string;
}

async function main() {
  requireCmsEnv();
  const raw = (await readStdin()).trim();
  if (!raw) throw new Error("Provide JSON on stdin.");
  const input = JSON.parse(raw) as DraftInput;

  const claimedStatus = asString(input.status) || asString(input._status);
  if (claimedStatus && claimedStatus !== "draft") {
    throw new Error(`Refusing non-draft status "${claimedStatus}". This script only saves drafts.`);
  }

  const title = asString(input.title);
  const slug = asString(input.slug);
  const excerpt = asString(input.excerpt);
  const bodyHtml = asString(input.bodyHtml);
  const categorySlug = asString(input.categorySlug);
  if (!title || !slug || !excerpt || !bodyHtml || !categorySlug) {
    throw new Error("title, slug, excerpt, bodyHtml, and categorySlug are required.");
  }

  const payload = await getPayload();
  const category = await findBySlug(payload, "categories", categorySlug);
  if (!category) {
    throw new Error(`Category "${categorySlug}" not found. Run 'bun run seed:cms' first`);
  }

  const authorSlug = asString(input.authorSlug) || "hello-packets";
  const reviewerSlug = asString(input.reviewerSlug) || "hello-packets";
  const author = await resolvePerson(payload, authorSlug, "author");
  const reviewer = await resolvePerson(payload, reviewerSlug, "reviewer");

  const tagIds = await Promise.all((input.tags ?? []).map((tag) => ensureTag(payload, tag)));
  const relatedIds: string[] = [];
  for (const relatedSlug of input.relatedArticleSlugs ?? []) {
    const related = await findBySlug(payload, "articles", relatedSlug);
    if (related) relatedIds.push(related.id as string);
    else process.stderr.write(`Warning: related article "${relatedSlug}" not found; skipping.\n`);
  }

  const seo = input.seo ?? {};
  const data = {
    title,
    slug,
    excerpt,
    body: htmlToLexical(bodyHtml),
    featuredImageAlt: asString(input.featuredImageAlt) || undefined,
    author,
    reviewer,
    category: category.id,
    tags: tagIds,
    relatedArticles: relatedIds,
    seo: {
      primaryKeyword: asString(seo.primaryKeyword),
      secondaryKeywords: seo.secondaryKeywords ?? [],
      metaTitle: asString(seo.metaTitle) || title,
      metaDescription: asString(seo.metaDescription) || excerpt,
      canonicalPath: asString(seo.canonicalPath) || `/blog/${slug}`,
      index: seo.index !== false,
      follow: seo.follow !== false,
      ogTitle: asString(seo.ogTitle) || undefined,
      ogDescription: asString(seo.ogDescription) || undefined,
    },
    _status: "draft" as const,
  };

  const existing = await findBySlug(payload, "articles", slug);
  const doc = existing
    ? await payload.update({
        collection: "articles",
        id: existing.id,
        data,
        draft: true,
      })
    : await payload.create({
        collection: "articles",
        data,
        draft: true,
      });

  if (doc._status && doc._status !== "draft") {
    throw new Error(`Expected draft status after write, got "${doc._status}"`);
  }

  process.stdout.write(
    JSON.stringify({
      ok: true,
      id: doc.id,
      slug,
      adminUrl: `/admin/collections/articles/${doc.id}`,
      previewUrl: `/blog/${slug}`,
    }) + "\n",
  );
  process.exit(0);
}

main().catch((error) => {
  process.stdout.write(
    JSON.stringify({
      ok: false,
      error: "DRAFT_WRITE_FAILED",
      detail: error instanceof Error ? error.message : String(error),
    }) + "\n",
  );
  process.exit(1);
});
