import { ValidationError, type CollectionConfig } from "payload";
import { extractH1 } from "@/lib/cms/body-html";
import { lexicalToSimpleHtml } from "@/lib/cms/lexical-text";

function requireEeatOnPublish(data: Record<string, unknown>) {
  if (data._status !== "published") return;

  const errors: { path: string; message: string }[] = [];
  if (!data.author) {
    errors.push({ path: "author", message: "Assign an author before publishing." });
  }
  if (!data.reviewer) {
    errors.push({ path: "reviewer", message: "Assign a reviewer before publishing." });
  }
  if (!data.lastReviewedDate) {
    errors.push({
      path: "lastReviewedDate",
      message: "Set last reviewed date before publishing.",
    });
  }
  if (!extractH1(lexicalToSimpleHtml(data.body))) {
    errors.push({
      path: "body",
      message: "Add exactly one H1 heading in the article body before publishing.",
    });
  }

  if (errors.length > 0) {
    throw new ValidationError({
      collection: "articles",
      errors,
    });
  }
}

export const Articles: CollectionConfig = {
  slug: "articles",
  admin: {
    useAsTitle: "title",
    defaultColumns: ["title", "author", "reviewer", "updatedAt", "_status"],
  },
  versions: {
    drafts: {
      autosave: {
        interval: 300,
      },
    },
  },
  fields: [
    { name: "title", type: "text", required: true, admin: { description: "CMS and browser title. The on-page H1 lives in the article body." } },
    { name: "slug", type: "text", required: true, unique: true, index: true },
    { name: "excerpt", type: "textarea", required: true },
    {
      name: "body",
      type: "richText",
      required: true,
      admin: {
        description:
          "Start with a single H1 heading. Put internal links, citations, and the CTA in the article; they are scored from this editor, not separate fields.",
      },
    },
    {
      name: "featuredImage",
      type: "upload",
      relationTo: "media",
    },
    { name: "featuredImageAlt", type: "text" },
    {
      name: "author",
      type: "relationship",
      relationTo: "people",
      admin: {
        description: "Required to publish. Create a Person first if the list is empty.",
      },
    },
    {
      name: "reviewer",
      type: "relationship",
      relationTo: "people",
      admin: {
        description: "Required to publish. Create a Person first if the list is empty.",
      },
    },
    {
      name: "category",
      type: "relationship",
      relationTo: "categories",
      required: true,
    },
    {
      name: "tags",
      type: "relationship",
      relationTo: "tags",
      hasMany: true,
    },
    { name: "publishedDate", type: "date" },
    { name: "updatedDate", type: "date" },
    {
      name: "lastReviewedDate",
      type: "date",
      admin: {
        description: "Required to publish. Editorial review date, separate from updated date.",
      },
    },
    {
      name: "seo",
      type: "group",
      fields: [
        { name: "primaryKeyword", type: "text" },
        { name: "secondaryKeywords", type: "text", hasMany: true },
        { name: "metaTitle", type: "text" },
        { name: "metaDescription", type: "textarea" },
        { name: "canonicalPath", type: "text" },
        { name: "index", type: "checkbox", defaultValue: true },
        { name: "follow", type: "checkbox", defaultValue: true },
        { name: "ogTitle", type: "text" },
        { name: "ogDescription", type: "textarea" },
        {
          name: "ogImage",
          type: "upload",
          relationTo: "media",
        },
      ],
    },
    {
      name: "relatedArticles",
      type: "relationship",
      relationTo: "articles",
      hasMany: true,
    },
  ],
  hooks: {
    beforeChange: [
      ({ data }) => {
        if (data) requireEeatOnPublish(data as Record<string, unknown>);
      },
    ],
  },
};
