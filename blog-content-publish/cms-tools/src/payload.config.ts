import { postgresAdapter } from "@payloadcms/db-postgres";
import { lexicalEditor } from "@payloadcms/richtext-lexical";
import { buildConfig } from "payload";
import sharp from "sharp";
import { Articles } from "./collections/Articles";
import { Categories } from "./collections/Categories";
import { Media } from "./collections/Media";
import { People } from "./collections/People";
import { Tags } from "./collections/Tags";

// Standalone CLI — never auto-push schema, even if NODE_ENV is unset.
if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = "production";
}

export default buildConfig({
  collections: [Media, People, Categories, Tags, Articles],
  editor: lexicalEditor(),
  secret: process.env.PAYLOAD_SECRET || "",
  logger: {
    options: { level: "warn" },
    destination: process.stderr,
  },
  db: postgresAdapter({
    push: false,
    pool: {
      connectionString: process.env.DATABASE_URI || "",
    },
  }),
  sharp,
});
