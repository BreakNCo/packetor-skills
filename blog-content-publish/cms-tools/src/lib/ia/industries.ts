import type { IaSection } from "./types";

export const industries: IaSection = {
  key: "industries",
  path: "/industries",
  label: "Industries",
  hubTitle: "Built for how your kind of company sells",
  hubDescription:
    "Vertical pages for the ICPs we sell to most. Buyer type (company vs consultancy) still lives on /companies and /consultancies.",
  pages: [
    {
      slug: "b2b-saas",
      title: "B2B SaaS",
      summary: "Enterprise questionnaires, SOC 2, and ISO without a huge GRC team.",
      description:
        "Packets helps B2B SaaS teams get through security reviews and stay certified while they ship product.",
      icon: "Cloud",
      sections: [
        {
          heading: "Why this ICP",
          body: "Deals stall on security questionnaires. You need SOC 2 (and often ISO) without pausing the roadmap for a year of spreadsheet compliance.",
          bullets: ["SOC 2 for US buyers", "ISO 27001 for global enterprise", "Vendor and access evidence on tap"],
        },
        {
          heading: "How Packets shows up",
          body: "Platform for the program, experts for scoping, implementation so engineering is not the evidence helpdesk.",
          bullets: ["Weeks-level typical scopes", "Reuse controls across frameworks", "Auditor collaboration in-product"],
        },
      ],
    },
    {
      slug: "ai-companies",
      title: "AI companies",
      summary: "ISO/SOC now, AI governance as the next layer.",
      description:
        "AI-native companies still buy ISO 27001 and SOC 2 first. Packets gets those done, then layers AI governance when you are ready.",
      icon: "Sparkles",
      sections: [
        {
          heading: "What we prioritize",
          body: "80% of effort is AI-native ISO and SOC 2: the urgent, budgeted work. AI governance is a 20% track, not the first SKU.",
          bullets: ["ISO 27001 and SOC 2 programs", "Evidence automation for fast-moving stacks", "AI inventory when you need it"],
        },
        {
          heading: "Related content",
          body: "Long-form guides will live in the blog under soc-2-for-ai-companies and ai-governance. This page is the sales/program entry.",
          bullets: [
            "Link to /solutions/soc-2 and /solutions/iso-27001",
            "Link to /solutions/ai-governance",
            "Audience still: /companies",
          ],
        },
      ],
    },
    {
      slug: "fintech",
      title: "Fintech",
      summary: "Customer due diligence, ISO/SOC, and continuous readiness.",
      description:
        "Fintech buyers and partners ask for ISO, SOC 2, and proof you stay ready, not a certificate from two years ago.",
      icon: "Landmark",
      sections: [
        {
          heading: "Why this ICP",
          body: "Audits and partner reviews are recurring. Continuous evidence collection matters more than a one-off binder.",
          bullets: ["SOC 2 / ISO as table stakes", "Vendor and access reviews", "Audit-ready all year"],
        },
        {
          heading: "Placeholder for copy",
          body: "Add India-specific licensing and RBI/SEBI questionnaire language here when the content intern drafts it.",
          bullets: ["DPDP where personal data is in scope", "Cross-map once", "Forward-deployed for first certification"],
        },
      ],
    },
  ],
};
