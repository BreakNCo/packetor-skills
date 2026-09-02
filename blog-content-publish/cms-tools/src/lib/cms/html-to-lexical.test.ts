import { describe, expect, test } from "bun:test";
import { analyzeBodyHtml } from "./body-html";
import { htmlToLexical, inlineHtmlToLexicalChildren } from "./html-to-lexical";
import { lexicalToSimpleHtml } from "./lexical-text";

const FIXTURE = `
<h1>SOC 2 for AI startups</h1>
<p>A <strong>security questionnaire</strong> can stall an enterprise deal. See the <em>audit</em> path.</p>
<h2>What to collect</h2>
<p>Start with a <a href="/audit-readiness">free audit score</a> and read our <a href="/security">security page</a>.</p>
<ul>
  <li>Map models in an inventory</li>
  <li>Cite an <a href="https://www.iso.org/standard/27001">ISO source</a></li>
</ul>
<p>Talk to us via <a href="/contact">contact</a>.</p>
`.trim();

describe("htmlToLexical", () => {
  test("round-trips scored fields through lexicalToSimpleHtml", () => {
    const lexical = htmlToLexical(FIXTURE);
    const roundTripped = lexicalToSimpleHtml(lexical);
    expect(analyzeBodyHtml(roundTripped)).toEqual(analyzeBodyHtml(FIXTURE));
  });

  test("stores link href under fields.url", () => {
    const lexical = htmlToLexical('<p>See <a href="/audit-readiness">CTA</a></p>');
    const paragraph = lexical.root.children[0];
    expect(paragraph && "children" in paragraph).toBe(true);
    const link = paragraph && "children" in paragraph ? paragraph.children.find((node) => node.type === "link") : undefined;
    expect(link && "fields" in link ? link.fields?.url : undefined).toBe("/audit-readiness");
  });

  test("throws on unsupported tags", () => {
    expect(() => htmlToLexical("<p>Hi <code>x</code></p>")).toThrow(/Unsupported HTML tag: <code>/);
  });
});

describe("inlineHtmlToLexicalChildren", () => {
  test("applies bold and italic format bits", () => {
    const nodes = inlineHtmlToLexicalChildren("Hello <strong>bold</strong> <em>italic</em>");
    const bold = nodes.find((node) => node.type === "text" && node.text === "bold");
    const italic = nodes.find((node) => node.type === "text" && node.text === "italic");
    expect(bold && "format" in bold ? bold.format : undefined).toBe(1);
    expect(italic && "format" in italic ? italic.format : undefined).toBe(2);
  });
});
