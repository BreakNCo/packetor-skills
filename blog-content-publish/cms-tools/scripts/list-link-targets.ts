import { IA_SECTIONS } from "../src/lib/ia";
import { getPublishedArticles } from "../src/lib/cms/source";

export type LinkTarget = {
  path: string;
  title: string;
  kind: "cta" | "static" | "ia-page" | "article";
  category?: string;
};

const STATIC_TARGETS: LinkTarget[] = [
  { path: "/contact", title: "Contact", kind: "cta" },
  { path: "/early-access", title: "Early access", kind: "cta" },
  { path: "/audit-readiness", title: "Free audit score", kind: "cta" },
  { path: "/pricing", title: "Pricing", kind: "static" },
  { path: "/security", title: "Security", kind: "static" },
  { path: "/design-partners", title: "Design partners", kind: "static" },
];

function requireCmsEnv() {
  if (!process.env.DATABASE_URI || !process.env.PAYLOAD_SECRET) {
    throw new Error("DATABASE_URI and PAYLOAD_SECRET must be set (packetor-skills/.env).");
  }
}

async function main() {
  requireCmsEnv();

  const iaPages: LinkTarget[] = Object.values(IA_SECTIONS).flatMap((section) =>
    section.pages.map((page) => ({
      path: `${section.path}/${page.slug}`,
      title: page.title,
      kind: "ia-page" as const,
    })),
  );

  const articles = await getPublishedArticles();
  const articleTargets: LinkTarget[] = articles.map((article) => ({
    path: `/blog/${article.slug}`,
    title: article.title,
    kind: "article" as const,
    category: article.category,
  }));

  const targets: LinkTarget[] = [...STATIC_TARGETS, ...iaPages, ...articleTargets];
  process.stdout.write(JSON.stringify(targets, null, 2) + "\n");
  process.exit(0);
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.stdout.write(
    JSON.stringify({
      ok: false,
      error: "LINK_TARGETS_FAILED",
      detail: error instanceof Error ? error.message : String(error),
    }) + "\n",
  );
  process.exit(1);
});
