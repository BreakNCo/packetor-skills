import type { IaSection } from "./types";

export const compare: IaSection = {
  key: "compare",
  path: "/compare",
  label: "Compare",
  hubTitle: "Packets compared",
  hubDescription:
    "How Packets compares to a compliance tool, a consultant engagement, or hiring a compliance lead, and to named competitors.",
  pages: [
    {
      slug: "tool-vs-consultant-vs-hire",
      title: "Tool vs consultant vs hire vs Packets",
      summary: "Four ways to get compliant. Only one comes with someone accountable.",
      description:
        "A compliance tool leaves the work with you. A consultant hands over a gap report and leaves. A hire takes months and costs ₹30–35 lakh a year. Packets is a named Compliance Lead, the platform, and the implementation work at one fixed price.",
      icon: "Scale",
      sections: [
        {
          heading: "Who this is for",
          body: "Teams that have a questionnaire to answer and are choosing between buying a tool, hiring a consultant, hiring a compliance lead, or running the program with Packets.",
          bullets: [
            "Accountability from week one",
            "Work done for you, not a checklist",
            "Same system in year two: nothing restarts",
          ],
        },
        {
          heading: "Who is accountable",
          body: "A tool makes your engineer accountable. A consultant is gone after the engagement. A hire is accountable once they've ramped. Packets assigns a named Compliance Lead from week one.",
          bullets: [
            "Tool: your engineer",
            "Consultant: nobody after handover",
            "Hire: the person, after ramp",
            "Packets: a named Compliance Lead from week one",
          ],
        },
        {
          heading: "Who does the work",
          body: "The tool is a checklist. The consultant advises; you implement. The hire is one person, part-time across everything. Packets uses agents at volume and specialists where judgement is needed; you approve.",
          bullets: [
            "Policies drafted and evidence collected for you",
            "Continuous monitoring in the same system",
            "Adding a framework reuses controls already in place",
          ],
        },
        {
          heading: "What it costs",
          body: "A tool is a licence plus the work still sitting with you. A consultant is a project fee with no system left behind. A hire is ₹30–35 lakh a year plus two to three months to find them. Packets is one fixed price covering the platform, the implementation work, and your Compliance Lead.",
          bullets: [
            "Quoted against your framework set",
            "No hourly billing, no statement of work",
            "GST invoiced in INR",
          ],
        },
      ],
    },
    {
      slug: "packets-vs-scrut",
      title: "Packets vs Scrut",
      summary: "Automation and implementation versus a product-led GRC tool.",
      description:
        "Scrut is the competitor we hear most. Packets competes on automation, price, and end-to-end delivery, not on looking like Vanta.",
      icon: "Scale",
      sections: [
        {
          heading: "Who should read this",
          body: "Teams evaluating Scrut for ISO/SOC who also want experts and implementation, not only software.",
          bullets: ["Smaller enterprises", "India-first pricing", "Need people, not just a platform"],
        },
        {
          heading: "Placeholder comparison",
          body: "A feature table will land here. Until then: Packets = software + experts + implementation; Scrut is the product-led alternative we position against.",
          bullets: ["Outcome ownership", "Evidence automation", "Forward-deployed option"],
        },
      ],
    },
    {
      slug: "packets-vs-sprinto",
      title: "Packets vs Sprinto",
      summary: "When you need delivery, not only integrations.",
      description:
        "Sprinto is often in the same shortlist. Use this page for buyers comparing a product-led motion to Packets' end-to-end function.",
      icon: "Scale",
      sections: [
        {
          heading: "Placeholder comparison",
          body: "Table copy TBD. Keep this page commercial and specific; it is not a blog post.",
          bullets: ["Implementation included", "Expert advisory", "India delivery and pricing"],
        },
      ],
    },
    {
      slug: "soc-2-vs-iso-27001",
      title: "SOC 2 vs ISO 27001",
      summary: "Which to do first, and how to reuse the work.",
      description:
        "Most teams that need both should start with ISO 27001, then run SOC 2 in parallel. Packets is built for that sequence.",
      icon: "GitCompare",
      sections: [
        {
          heading: "The short version",
          body: "ISO 27001 is a management system. SOC 2 is an attestation against Trust Services Criteria. Overlap is large; start with the one your buyers ask for first, usually ISO in India and mixed globally.",
          bullets: ["ISO first, then SOC 2 in parallel", "Reuse controls and evidence", "Packets maps both in one workspace"],
        },
        {
          heading: "Placeholder table",
          body: "A side-by-side table (audience, report vs certificate, typical timeline) will replace this block.",
          bullets: ["Buyer geography", "Timeline", "What auditors look at"],
        },
      ],
    },
  ],
};
