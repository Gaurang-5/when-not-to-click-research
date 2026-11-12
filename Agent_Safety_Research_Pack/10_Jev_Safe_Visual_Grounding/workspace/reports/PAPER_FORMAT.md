# Journal manuscript layout

Updated 1 November 2026. The current PDF and editable LaTeX follow the article-page layout in the professor-supplied published sample, "A XAI-based Framework for Frequency Sub-band Characterization of Cough Spectrograms in Chronic Respiratory Disease" (Applied Artificial Intelligence, DOI 10.1080/08839514.2026.2736309). The separate publisher cover/download page is not reproduced. This is a local manuscript layout, not the journal's official submission template.

## Presentation

- Single column on 210 x 280 mm pages, matching the sample's article-page dimensions.
- Left-aligned dark-blue sans-serif title and unnumbered main headings; italic sans-serif subheadings.
- 10.5-point serif body, 12.5-point leading, justified paragraphs and restrained first-line indentation.
- Shaded, narrower abstract panel with a sans-serif ABSTRACT label.
- Main structure: Introduction, Related work, Materials and methods, Results, Discussion and Conclusion, followed by ethics/data availability, references and diagnostic appendices.
- Author-year citations linked to alphabetized references. Existing authors, years, titles and source URLs are retained; n.d. identifies the undated dataset reference. OpenAI documentation entries use 2026a/2026b.
- Numbered equations rendered as vector math; numbered figures and plain ruled tables with sans-serif captions.
- Publisher logo, DOI, publication date, copyright/license statements, contact details and affiliations are not invented. The existing Anonymous Authors field remains until authors supply their final details.

Installed Times New Roman and Arial are embedded in the PDF on macOS; standard PDF Times and Helvetica are fallbacks. These are substitutes for the sample's Minion Pro and Myriad Pro; proprietary font files are not extracted or redistributed. LaTeX uses mathptmx and helvet, with the same dimensions, colors and hierarchy.

## Reproduction and provenance

Scientific prose and numerical tables remain in scripts/paper_content.py. scripts/paper_layout.py changes hierarchy and display citations only. scripts/build_paper_pdf.py generates the PDF, paper/main.tex and paper/jev_journal.sty. scripts/render_paper_math.py supplies unchanged equations as vector PDFs and PNG previews. Compile paper/main.tex for the complete editable project; the reports source is a mirror.

The prior single-column conference version and its builder are archived in archive/2026-11-01-before-professor-format/. No experiments were rerun and no paid API calls were made for formatting.

Verification retains 66 prose paragraphs, 25 tables, 8 equations, 10 figures and 15 reference entries. All 43 saved numerical JSON/CSV/JSONL evidence files match their pre-format hashes. See results/iteration3/verification_status.json for final page, compilation and test checks.
