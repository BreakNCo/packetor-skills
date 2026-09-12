import type { Category } from "./types";

/** Default blog categories — seeded into Payload via `bun run seed:cms`. */
export const categories: Category[] = [
  {
    slug: "soc-2-for-ai-companies",
    title: "SOC 2 for AI companies",
    description: "How growing AI teams get and stay SOC 2 ready.",
  },
  {
    slug: "iso-27001-for-ai-companies",
    title: "ISO 27001 for AI companies",
    description: "ISMS design and certification for AI-native companies.",
  },
  {
    slug: "india-compliance",
    title: "India compliance",
    description: "DPDP, cost, and procurement for India-based teams.",
  },
  {
    slug: "ai-governance",
    title: "AI governance",
    description: "Policies, inventories, and evidence for AI systems.",
  },
];
