import type { IaSection } from "./types";

export const platform: IaSection = {
  key: "platform",
  path: "/platform",
  label: "Platform",
  hubTitle: "One system holds the whole program.",
  hubDescription:
    "Controls, policies, evidence, monitoring, risk and vendors in one place, mapped across every framework you're carrying.",
  pages: [
    {
      slug: "compliance-management",
      title: "Compliance management",
      summary: "Frameworks, controls, owners, and status in one place.",
      description:
        "See every framework, control, and owner in a single workspace. Packets assembles the program so you are not rebuilding it in spreadsheets.",
      icon: "LayoutDashboard",
      sections: [
        {
          heading: "What it does",
          body: "Import frameworks, assign control owners, and track completion without a project-manager spreadsheet.",
          bullets: [
            "Multi-framework view",
            "Control ownership and due dates",
            "Status that reflects tasks and policies",
          ],
        },
        {
          heading: "Who uses it",
          body: "Compliance leads, security, and implementation partners working in the same program.",
          bullets: ["In-house teams", "Consultancies delivering for clients", "Forward-deployed Packets staff"],
        },
      ],
    },
    {
      slug: "evidence-automation",
      title: "Evidence automation",
      summary: "Requests, reminders, labels, and an audit trail.",
      description:
        "Collect and label evidence automatically so audits are not a months-long email thread. Every artifact stays traceable.",
      icon: "FileCheck",
      sections: [
        {
          heading: "What it does",
          body: "Request evidence, remind owners, and keep an immutable trail auditors can follow.",
          bullets: ["Automated requests and reminders", "Labelling and gap flags", "Versioned, tamper-evident files"],
        },
        {
          heading: "Why it matters",
          body: "Most audit delay is chasing screenshots. Automation is how Packets stays cheaper and faster than spreadsheet GRC.",
          bullets: ["Weeks-level readiness for typical scopes", "Less non-billable admin for consultancies", "Reuse across ISO and SOC 2"],
        },
      ],
    },
    {
      slug: "risk-management",
      title: "Risk management",
      summary: "Registers, scoring, and treatment tied to controls.",
      description:
        "Keep a living risk register connected to the same controls and vendors as the rest of your program.",
      icon: "AlertTriangle",
      sections: [
        {
          heading: "What it does",
          body: "Track risks, owners, and treatment, including vendor and change-driven risks as you grow.",
          bullets: ["Risk register", "Scoring and treatment", "Links to controls and vendors"],
        },
        {
          heading: "Placeholder for copy",
          body: "Final copy will describe how new vendors and system changes feed the register. Structure is ready for that drop-in.",
          bullets: ["ISO 27001 risk treatment", "SOC 2 risk assessment evidence", "Vendor-related risks"],
        },
      ],
    },
    {
      slug: "policy-management",
      title: "Policy management",
      summary: "Draft, review, publish, and map policies to controls.",
      description:
        "Draft policies with AI assistance, send them through review, and keep published versions mapped to the controls they satisfy.",
      icon: "FileText",
      sections: [
        {
          heading: "What it does",
          body: "Policy Copilot drafts; your experts (or ours) review; the workspace tracks versions and acknowledgements.",
          bullets: ["Drafts aligned to ISO/SOC", "Review and publish workflow", "Mapped to controls, not orphaned docs"],
        },
        {
          heading: "Human in the loop",
          body: "Software drafts. Experts approve. That split is the product, not an afterthought.",
          bullets: ["In-house reviewers", "Packets expert advisory", "Auditor-facing exports"],
        },
      ],
    },
    {
      slug: "ai-governance",
      title: "AI governance",
      summary: "Inventory and controls for models you build or buy.",
      description:
        "The platform slice of AI governance: system inventory, linked risks, and evidence, complementary to the /solutions/ai-governance program page.",
      icon: "Brain",
      sections: [
        {
          heading: "Platform vs program",
          body: "This page is the software. The solutions page is the outcome (advisory + implementation). They are linked on purpose.",
          bullets: ["Model / system inventory", "Link to risk and vendor records", "Evidence for questionnaires"],
        },
        {
          heading: "Placeholder for copy",
          body: "Feature-level copy will land after the product surface is named. Do not duplicate the full solutions narrative here.",
          bullets: ["Cross-link to /solutions/ai-governance", "Reuse access and logging controls", "Grow into ISO 42001 later"],
        },
      ],
    },
  ],
};
