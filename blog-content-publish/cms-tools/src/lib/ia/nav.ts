import { platform, services } from "./index";

export type NavDropdownLink = {
  href: string;
  title: string;
  summary: string;
};

function servicePage(slug: string) {
  const page = services.pages.find((entry) => entry.slug === slug);
  if (!page) {
    throw new Error(`Missing services page: ${slug}`);
  }
  return page;
}

/** Top nav Platform dropdown — Experts, Platform, Implementation (hero pillar order) */
export const NAV_PLATFORM_LINKS: NavDropdownLink[] = [
  {
    href: `${services.path}/${servicePage("expert-advisory").slug}`,
    title: "Experts",
    summary: servicePage("expert-advisory").summary,
  },
  {
    href: platform.path,
    title: platform.label,
    summary: platform.hubDescription,
  },
  {
    href: `${services.path}/${servicePage("compliance-implementation").slug}`,
    title: "Implementation",
    summary: servicePage("compliance-implementation").summary,
  },
];
