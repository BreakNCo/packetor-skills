export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://packets.build";

export const SITE_NAME = "packets";

export function isProductionDeploy() {
  return process.env.VERCEL_ENV === "production";
}

export function shouldIndex() {
  if (process.env.INDEXING_ENABLED === "true") return true;
  if (process.env.INDEXING_ENABLED === "false") return false;
  return isProductionDeploy();
}
