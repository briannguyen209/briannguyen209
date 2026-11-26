// Build the Deneb tutorial .docx from content.json (written by build_content.py).
// Usage: node tutorial/build_docx.js  ->  tutorial/Deneb_Chart_Tutorial.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, ImageRun, PageBreak, Footer, Header, PageNumber, LevelFormat, TableOfContents,
  TabStopType,
} = require("docx");

const HERE = __dirname;
const content = JSON.parse(fs.readFileSync(path.join(HERE, "content.json"), "utf8"));
const W = 9360; // content width (DXA) on US Letter with 1" margins
const BODY = "Calibri", HEAD = "Arial", MONO = "Consolas";
const C = { navy: "1F3864", blue: "2E5597", grey: "595959", light: "F3F5F8", border: "D0D5DD", codeText: "1E1E1E", inline: "B03A2E" };

// ---------------------------------------------------------------- inline markup: **bold**, `code`
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: tok.slice(1, -1), font: MONO, size: 19, color: C.inline, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: none, bottom: none, left: none, right: none };

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

// ---------------------------------------------------------------- block renderers
let listInstance = 0;
const children = [];

function codeBlock(text, label) {
  if (label) children.push(new Paragraph({ spacing: { before: 120, after: 40 }, keepNext: true,
    children: [new TextRun({ text: label, italics: true, size: 18, color: C.grey })] }));
  const lines = text.split("\n");
  const paras = lines.map((ln, i) => new Paragraph({
    spacing: { before: 0, after: 0, line: 240 },
    keepNext: lines.length <= 25 && i < lines.length - 1,
    children: [new TextRun({ text: ln.length ? ln : " ", font: MONO, size: 16, color: C.codeText })],
  }));
  children.push(new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: W, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: C.light, color: "auto" },
      margins: { top: 100, bottom: 100, left: 160, right: 120 },
      borders: { top: { style: BorderStyle.SINGLE, size: 4, color: C.border }, bottom: { style: BorderStyle.SINGLE, size: 4, color: C.border },
                 left: { style: BorderStyle.SINGLE, size: 18, color: "8EA9DB" }, right: { style: BorderStyle.SINGLE, size: 4, color: C.border } },
      children: paras })] })],
  }));
  children.push(new Paragraph({ spacing: { before: 0, after: 80 }, children: [] }));
}

const NOTE = { tip: ["Tip", "E2F0D9", "70AD47"], why: ["Why this matters", "DEEBF7", "2E75B6"], watch: ["Watch out", "FFF2CC", "C9A100"] };
function noteBlock(kind, text) {
  const [title, fill, bar] = NOTE[kind] || NOTE.tip;
  children.push(new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [W],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: W, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill, color: "auto" },
      margins: { top: 100, bottom: 100, left: 180, right: 140 },
      borders: { ...noBorders, left: { style: BorderStyle.SINGLE, size: 24, color: bar } },
      children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun({ text: title + ": ", bold: true }), ...runs(text)] })],
    })] })],
  }));
  children.push(new Paragraph({ spacing: { before: 0, after: 80 }, children: [] }));
}

function tableBlock(headers, rows, widths) {
  const borders = { style: BorderStyle.SINGLE, size: 4, color: C.border };
  const t = new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    borders: { top: borders, bottom: borders, left: borders, right: borders, insideHorizontal: borders, insideVertical: borders },
    rows: [headers, ...rows].map((r, ri) => new TableRow({
      tableHeader: ri === 0, cantSplit: true,
      children: r.map((txt, ci) => new TableCell({
        width: { size: widths[ci], type: WidthType.DXA },
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: "DCE3EE", color: "auto" } : undefined,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: runs(String(txt), ri === 0 ? { bold: true, size: 20 } : { size: 20 }) })],
      })),
    })),
  });
  children.push(t);
  children.push(new Paragraph({ spacing: { before: 0, after: 100 }, children: [] }));
}

function imageBlock(file, widthIn, caption) {
  const { w, h, data } = pngSize(file);
  const pxW = Math.round(widthIn * 96), pxH = Math.round(pxW * h / w);
  const maxH = 8.2 * 96; // keep tall images on one page
  const scale = pxH > maxH ? maxH / pxH : 1;
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 }, keepNext: !!caption,
    children: [new ImageRun({ type: "png", data, transformation: { width: Math.round(pxW * scale), height: Math.round(pxH * scale) },
      altText: { title: caption || "chart", description: caption || "chart", name: path.basename(file) } })] }));
  if (caption) children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 160 },
    children: [new TextRun({ text: caption, italics: true, size: 18, color: C.grey })] }));
}

// ---------------------------------------------------------------- title page + contents
children.push(new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Building Tableau-style and NYT-style Charts", font: HEAD, size: 52, bold: true, color: C.navy })] }));
children.push(new Paragraph({ spacing: { before: 0, after: 600 }, children: [new TextRun({ text: "in Power BI with Deneb — a step-by-step guide", font: HEAD, size: 36, color: C.blue })] }));
children.push(new Paragraph({ spacing: { after: 120 }, children: runs("Eleven charts rebuilt from an empty visual, one small step at a time: highlight table, dual axis, bullet graph, scatter with quadrants, bar-in-bar, packed bubbles, treemap, streak tiles, diverging bars, a US route map and a globe.", { size: 24, color: C.grey }) }));
children.push(new Paragraph({ spacing: { after: 120 }, children: runs("Companion files: `tableau-to-powerbi/tutorial/steps/` (every step, ready to paste) and the `DenebShowcase.pbip` report.", { size: 22, color: C.grey }) }));
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Contents", font: HEAD, size: 32, bold: true, color: C.navy })] }));
children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));
children.push(new Paragraph({ spacing: { before: 200 }, children: [new TextRun({ text: "If the page numbers above are missing, right-click the table and choose Update Field (Word asks to do this when the file opens).", italics: true, size: 18, color: C.grey })] }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------------------------------------------------------- body
for (const b of content) {
  switch (b.t) {
    case "h1": children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(b.text.replace(/`/g, ""))] })); break;
    case "h2": children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(b.text.replace(/`/g, ""))] })); break;
    case "h3": children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(b.text.replace(/`/g, ""))] })); break;
    case "p": children.push(new Paragraph({ spacing: { after: 120 }, children: runs(b.text) })); break;
    case "bullets":
      for (const it of b.items) children.push(new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 }, children: runs(it) }));
      children.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      break;
    case "numbered":
      listInstance += 1;
      for (const it of b.items) children.push(new Paragraph({ numbering: { reference: "numbers", level: 0, instance: listInstance }, spacing: { after: 60 }, children: runs(it) }));
      children.push(new Paragraph({ spacing: { after: 60 }, children: [] }));
      break;
    case "code": codeBlock(b.text, b.label); break;
    case "note": noteBlock(b.kind, b.text); break;
    case "table": tableBlock(b.headers, b.rows, b.widths); break;
    case "img": imageBlock(b.path, b.w, b.caption); break;
    case "pagebreak": children.push(new Paragraph({ children: [new PageBreak()] })); break;
    default: throw new Error("unknown block " + b.t);
  }
}

const doc = new Document({
  creator: "Deneb tutorial",
  title: "Building Tableau-style and NYT-style Charts in Power BI with Deneb",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: BODY, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, font: HEAD, color: C.navy }, paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, font: HEAD, color: C.blue }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: HEAD, color: "1F1F1F" }, paragraph: { spacing: { before: 260, after: 100 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Deneb chart tutorial", size: 16, color: "8C8C8C" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: "8C8C8C" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(HERE, "Deneb_Chart_Tutorial.docx");
  fs.writeFileSync(out, buf);
  console.log("Wrote", out, (buf.length / 1024 / 1024).toFixed(1), "MB");
});
