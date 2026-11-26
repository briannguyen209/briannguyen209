"""Build tutorial content: renders every step, saves step specs, writes content.json for build_docx.js."""
import json
import tutorial_lib as L
import content_foundations, content_tableau, content_nyt

content_foundations.build()
content_tableau.build()
content_nyt.build()
(L.HERE / "content.json").write_text(json.dumps(L.DOC, ensure_ascii=False), encoding="utf-8")
print(len(L.DOC), "blocks;", sum(1 for b in L.DOC if b["t"] == "img"), "images;",
      sum(1 for b in L.DOC if b["t"] == "code"), "code blocks;", len(list(L.STEPS.glob("*.json"))), "step files")
