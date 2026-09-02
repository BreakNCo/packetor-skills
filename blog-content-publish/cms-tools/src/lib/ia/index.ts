import { compare } from "./compare";
import { industries } from "./industries";
import { platform } from "./platform";
import { services } from "./services";
import { solutions } from "./solutions";
import type { IaSection, IaSectionKey } from "./types";

export const IA_SECTIONS: Record<IaSectionKey, IaSection> = {
  solutions,
  platform,
  services,
  industries,
  compare,
};

export function getSection(key: IaSectionKey): IaSection {
  return IA_SECTIONS[key];
}

export function getPage(key: IaSectionKey, slug: string) {
  return IA_SECTIONS[key].pages.find((page) => page.slug === slug);
}

export function getSectionStaticParams(key: IaSectionKey) {
  return IA_SECTIONS[key].pages.map((page) => ({ slug: page.slug }));
}

export { compare, industries, platform, services, solutions };
export type { IaPage, IaSection, IaSectionKey } from "./types";
