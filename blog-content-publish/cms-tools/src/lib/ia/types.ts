export type IaSectionKey =
  | "solutions"
  | "platform"
  | "services"
  | "industries"
  | "compare";

export type IaPageSection = {
  heading: string;
  body: string;
  bullets: string[];
};

export type IaPage = {
  slug: string;
  title: string;
  summary: string;
  description: string;
  icon: string;
  sections: IaPageSection[];
};

export type IaSection = {
  key: IaSectionKey;
  path: string;
  label: string;
  hubTitle: string;
  hubDescription: string;
  pages: IaPage[];
};
