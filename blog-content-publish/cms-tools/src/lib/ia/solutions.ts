import type { IaSection } from "./types";

export const solutions: IaSection = {
  key: "solutions",
  path: "/solutions",
  label: "Solutions",
  hubTitle: "Compliance programs we run with you",
  hubDescription:
    "Outcome-first programs spanning software, expert guidance, and hands-on implementation, from first audit to continuous compliance.",
  pages: [
    {
      slug: "end-to-end-compliance",
      title: "End-to-end compliance",
      summary: "Platform, experts, and implementation as one function.",
      description:
        "Packets is the compliance function for teams that need to get certified and stay certified without building it all in-house.",
      icon: "Layers",
      sections: [
        {
          heading: "What you get",
          body: "A single team and workspace covering design, implementation, evidence, and ongoing monitoring, not a tool you have to operate alone.",
          bullets: [
            "Platform to manage the program",
            "Experts to scope and guide it",
            "People to implement alongside your team",
          ],
        },
        {
          heading: "When this is the right starting point",
          body: "Choose this if you need ownership of the outcome, not just licenses for a GRC product.",
          bullets: [
            "First-time ISO 27001 or SOC 2",
            "Lean teams without a full-time GRC hire",
            "Need a named owner through certification",
          ],
        },
        {
          heading: "How it maps to Packets",
          body: "The program pulls in the platform, expert advisory, and forward-deployed implementation as needed for your scope.",
          bullets: [
            "Start with a readiness assessment",
            "Stand up the workspace and control set",
            "Run evidence collection through audit",
          ],
        },
      ],
    },
    {
      slug: "soc-2",
      title: "SOC 2",
      summary: "Type I and Type II programs with evidence automation.",
      description:
        "Get audit-ready for SOC 2 with mapped Trust Services Criteria, automated evidence, and implementation support through the auditor review.",
      icon: "Shield",
      sections: [
        {
          heading: "The outcome",
          body: "A SOC 2 report your customers will accept, with a workspace that stays useful after the audit, not a binder you abandon.",
          bullets: [
            "Type I and Type II scoping",
            "Control mapping to TSC",
            "Auditor-ready evidence trails",
          ],
        },
        {
          heading: "What we implement",
          body: "Policies, control owners, evidence requests, and vendor/risk workflows that match how your company actually operates.",
          bullets: [
            "Policy drafts aligned to your stack",
            "Evidence collection with reminders",
            "Mock assessments before the auditor arrives",
          ],
        },
        {
          heading: "Who this is for",
          body: "B2B teams selling to US or enterprise buyers who are asked for SOC 2 in security questionnaires.",
          bullets: [
            "Startups closing their first enterprise deals",
            "Teams running SOC 2 alongside ISO 27001",
            "Companies replacing spreadsheet audits",
          ],
        },
      ],
    },
    {
      slug: "iso-27001",
      title: "ISO 27001",
      summary: "ISMS design, implementation, and certification support.",
      description:
        "Stand up an ISO 27001:2022 information security management system with Packets software, expert guidance, and hands-on implementation.",
      icon: "FileCheck",
      sections: [
        {
          heading: "The outcome",
          body: "A certifiable ISMS: Statement of Applicability, risk treatment, and evidence, not a policy pack sitting unused.",
          bullets: [
            "ISO 27001:2022 control set",
            "Risk assessment and treatment",
            "Internal audit / mock assessment",
          ],
        },
        {
          heading: "How we work",
          body: "Experts help you scope the ISMS; the platform tracks controls and evidence; implementation support closes gaps with your team.",
          bullets: [
            "Scope and context of the organization",
            "Control mapping and owners",
            "Continuous monitoring after certification",
          ],
        },
        {
          heading: "India and multi-framework",
          body: "Useful when you also need DPDP, SOC 2, or GDPR: reuse controls instead of running three separate programs.",
          bullets: [
            "Cross-map once, evidence many times",
            "INR pricing and GST invoicing where relevant",
            "IST-friendly delivery",
          ],
        },
      ],
    },
    {
      slug: "gdpr",
      title: "GDPR",
      summary: "Data protection program for EU customer and employee data.",
      description:
        "Operationalize GDPR with policies, records of processing, vendor diligence, and evidence collection, backed by experts, not a checklist PDF.",
      icon: "Lock",
      sections: [
        {
          heading: "The outcome",
          body: "A living GDPR program your team can run: RoPA, DPIA triggers, DSAR handling, and processor contracts.",
          bullets: [
            "Records of processing",
            "Vendor / processor review",
            "Policy and training evidence",
          ],
        },
        {
          heading: "How Packets helps",
          body: "The platform holds the artifacts; experts help you decide what applies; implementation makes it real in your stack.",
          bullets: [
            "Map GDPR articles to controls",
            "Collect evidence from existing tools",
            "Keep it current as vendors change",
          ],
        },
      ],
    },
    {
      slug: "hipaa",
      title: "HIPAA",
      summary: "Security and privacy safeguards for PHI-handling teams.",
      description:
        "Build a HIPAA Security Rule program with risk analysis, policies, access controls, and evidence, with guidance from people who have implemented it.",
      icon: "Heart",
      sections: [
        {
          heading: "The outcome",
          body: "Documented administrative, physical, and technical safeguards with evidence you can show a customer or auditor.",
          bullets: [
            "Security Risk Analysis",
            "Policy set and workforce training",
            "Access, audit, and transmission controls",
          ],
        },
        {
          heading: "How we implement",
          body: "We map HIPAA requirements into Packets controls and help your team collect evidence from the systems that actually hold PHI.",
          bullets: [
            "BAAs and vendor inventory",
            "Incident response evidence",
            "Ongoing monitoring, not a one-time binder",
          ],
        },
      ],
    },
    {
      slug: "ai-governance",
      title: "AI governance",
      summary: "Inventory, risk, and controls for teams shipping AI.",
      description:
        "Start an AI governance program that fits how you actually build: model inventory, risk review, and evidence, as a 20% track alongside ISO/SOC.",
      icon: "Brain",
      sections: [
        {
          heading: "The outcome",
          body: "A practical AI governance layer: what models you use, what data they touch, and who signed off, without pretending EU AI Act is your first purchase.",
          bullets: [
            "AI system inventory",
            "Risk and use-case review",
            "Policy and monitoring hooks",
          ],
        },
        {
          heading: "Where it sits",
          body: "Most buyers still buy ISO/SOC first. This page is for teams that already know AI governance is the next step, or sell AI products today.",
          bullets: [
            "Cross-link to ISO 27001 and SOC 2 programs",
            "Reuse existing access and vendor controls",
            "Grow into ISO 42001 when urgency arrives",
          ],
        },
      ],
    },
    {
      slug: "cyber-resilience",
      title: "Cyber resilience",
      summary: "Incident, continuity, and recovery as an operating program.",
      description:
        "Turn backup slides into a runnable resilience program: incident response, business continuity, and evidence that you actually test it.",
      icon: "Activity",
      sections: [
        {
          heading: "The outcome",
          body: "Documented and exercised incident and continuity processes, with owners and evidence in one workspace.",
          bullets: [
            "Incident response runbooks",
            "BCP / DR tests",
            "Lessons-learned tracking",
          ],
        },
        {
          heading: "Tied to certification",
          body: "Maps to ISO 27001, SOC 2 availability, and customer questionnaires that ask how you recover.",
          bullets: [
            "Reuse evidence across frameworks",
            "Tabletop and test logs",
            "Vendor dependencies in one register",
          ],
        },
      ],
    },
  ],
};
