import type { IaSection } from "./types";

export const services: IaSection = {
  key: "services",
  path: "/services",
  label: "Services",
  hubTitle: "Experts and people, not just software",
  hubDescription:
    "Packets is an end-to-end compliance function. The services layer is how we guide and implement: the part product-only GRC tools leave to you.",
  pages: [
    {
      slug: "expert-advisory",
      title: "Expert advisory",
      summary: "ISO and InfoSec experts who scope, review, and unblock.",
      description:
        "Work with compliance and information-security experts who have run ISO 27001 and SOC 2 programs, not a chatbot that replaced your consultant.",
      icon: "GraduationCap",
      sections: [
        {
          heading: "What you get",
          body: "Named experts for scoping, control decisions, policy review, and auditor-facing narrative, sitting on top of the same workspace.",
          bullets: [
            "ISMS / SOC 2 scoping",
            "Control and policy review",
            "Unblock decisions your team should not guess",
          ],
        },
        {
          heading: "How it differs from the platform",
          body: "The platform tracks work. Advisory is human judgment: what is in scope, what is good enough, what the auditor will ask.",
          bullets: ["Office hours and reviews", "Linked to your Packets workspace", "Not a separate PDF engagement"],
        },
      ],
    },
    {
      slug: "compliance-implementation",
      title: "Compliance implementation",
      summary: "We help you stand the program up in your stack.",
      description:
        "Implementation support for policies, tooling choices, evidence sources, and the operational work that sits between buying software and passing an audit.",
      icon: "Wrench",
      sections: [
        {
          heading: "What we implement",
          body: "The unglamorous middle: identity, endpoint, logging, vendor questionnaires, and the evidence paths that make controls real.",
          bullets: [
            "Tooling and control design",
            "Evidence source mapping",
            "Gap closure with your team",
          ],
        },
        {
          heading: "Who this is for",
          body: "Teams that know they need certification but do not have spare cycles to figure out every control from scratch.",
          bullets: ["First-time ISO / SOC 2", "Migration off spreadsheets", "Lean security teams"],
        },
      ],
    },
    {
      slug: "forward-deployed",
      title: "Forward-deployed implementation",
      summary: "A person working alongside your team until it runs.",
      description:
        "A Packets practitioner embedded with your team: white-glove ownership of setup and delivery, not a ticket queue.",
      icon: "Users",
      sections: [
        {
          heading: "What it is",
          body: "Someone who sits with your team, drives the workspace, and owns progress through certification. The Yarnit-style white-glove ask, productized.",
          bullets: [
            "Named implementer on your program",
            "Hands-on setup and evidence chase",
            "Handover into a program you can run",
          ],
        },
        {
          heading: "What it is not",
          body: "Not a full-time vCISO retainer unless you ask for that later. The current offer is implementation through a working program.",
          bullets: [
            "Scoped to certification / readiness outcomes",
            "Works inside Packets, not a parallel spreadsheet",
            "Pairs with expert advisory for judgment calls",
          ],
        },
      ],
    },
  ],
};
