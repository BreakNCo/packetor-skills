import type { CollectionConfig } from "payload";

export const People: CollectionConfig = {
  slug: "people",
  admin: {
    useAsTitle: "name",
    defaultColumns: ["name", "role", "updatedAt"],
  },
  fields: [
    {
      name: "name",
      type: "text",
      required: true,
    },
    {
      name: "slug",
      type: "text",
      required: true,
      unique: true,
      index: true,
    },
    {
      name: "role",
      type: "select",
      required: true,
      options: [
        { label: "Author", value: "author" },
        { label: "Reviewer", value: "reviewer" },
        { label: "Both", value: "both" },
      ],
    },
    {
      name: "bio",
      type: "textarea",
      required: true,
    },
    {
      name: "statedExpertise",
      type: "text",
      required: true,
    },
    {
      name: "credentials",
      type: "text",
      required: true,
    },
    {
      name: "linkedIn",
      type: "text",
    },
    {
      name: "headshot",
      type: "upload",
      relationTo: "media",
    },
  ],
};
