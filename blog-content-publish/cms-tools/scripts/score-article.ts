import { htmlToLexical } from "../src/lib/cms/html-to-lexical";
import { lexicalToSimpleHtml } from "../src/lib/cms/lexical-text";
import { scoreArticleDraft } from "../src/lib/cms/seo-score";
import type { ArticleDraft } from "../src/lib/cms/types";
import { analyzeBodyHtml } from "../src/lib/cms/body-html";

type ScoreInput = {
  title?: string;
  excerpt?: string;
  slug?: string;
  bodyHtml?: string;
  featuredImageAlt?: string;
  authorSlug?: string;
  reviewerSlug?: string;
  categorySlug?: string;
  seo?: {
    primaryKeyword?: string;
    metaTitle?: string;
    metaDescription?: string;
    canonicalPath?: string;
  };
};

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function toDraft(input: ScoreInput, bodyHtml: string): ArticleDraft {
  const slug = asString(input.slug);
  const title = asString(input.title);
  const seo = input.seo ?? {};
  const fromBody = analyzeBodyHtml(bodyHtml);
  const authorSlug = asString(input.authorSlug);
  return {
    title,
    h1: fromBody.h1,
    slug,
    bodyHtml,
    metaTitle: asString(seo.metaTitle),
    metaDescription: asString(seo.metaDescription),
    primaryKeyword: asString(seo.primaryKeyword),
    canonicalPath: asString(seo.canonicalPath) || (slug ? `/blog/${slug}` : ""),
    featuredImageAlt: asString(input.featuredImageAlt),
    authorSlug,
    reviewerSlug: asString(input.reviewerSlug),
    sourcesCount: fromBody.sourcesCount,
    internalLinksCount: fromBody.internalLinksCount,
    hasCta: fromBody.hasCta,
    schemaConfigured: Boolean(title && fromBody.h1 && slug && authorSlug),
  };
}

async function main() {
  const raw = (await readStdin()).trim();
  if (!raw) {
    throw new Error("Provide JSON on stdin.");
  }
  const input = JSON.parse(raw) as ScoreInput;
  const bodyHtml = asString(input.bodyHtml);
  const roundTrippedBodyHtml = lexicalToSimpleHtml(htmlToLexical(bodyHtml));
  const { score, checks } = scoreArticleDraft(toDraft(input, roundTrippedBodyHtml));
  process.stdout.write(JSON.stringify({ score, checks, roundTrippedBodyHtml }, null, 2) + "\n");
}

main().catch((error) => {
  process.stdout.write(
    JSON.stringify({
      ok: false,
      error: "SCORE_FAILED",
      detail: error instanceof Error ? error.message : String(error),
    }) + "\n",
  );
  process.exit(1);
});
