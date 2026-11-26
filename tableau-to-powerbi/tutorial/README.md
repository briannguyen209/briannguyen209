# Deneb chart tutorial

**`Deneb_Chart_Tutorial.docx`** (or the same content as **`Deneb_Chart_Tutorial.pdf`**): a 114-page step-by-step
guide to rebuilding all 11 Deneb charts in the DenebShowcase report from an empty visual.

- `steps/`: every step of every chapter as a ready-to-paste spec (`ch05_heatmap_step3.json`, …). The map steps
  already contain the TopoJSON. `steps/tableau_config.json` is the shared Tableau-look Config.
- Pictures in the guide are rendered from these exact files (`../renders/tutorial/`), so the code and the images always match.

Rebuild after editing the content:

```bash
python tutorial/build_content.py   # renders steps, writes content.json
node tutorial/build_docx.js        # writes the .docx
```
