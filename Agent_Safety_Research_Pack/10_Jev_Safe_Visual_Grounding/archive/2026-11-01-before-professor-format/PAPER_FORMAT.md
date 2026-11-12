# Conference paper layout

Updated 24 October 2026. The current PDF and editable TeX use a single-column research preprint layout inspired by the NIPS 2017 appearance of Attention Is All You Need (https://arxiv.org/pdf/1706.03762). It is a local layout, not an official venue template or an acceptance claim.

- Letter paper; a true 5.5-inch text block and 9-inch text height.
- Serif body text, bold black headings, an inset abstract and ruled title block.
- Seven main sections, with Experimental Setup and Results divided into subsections.
- Numbered equations, numbered figures and compact booktabs-style tables.
- References follow the conclusion; diagnostic and qualitative material follows as appendices.
- The final PDF embeds serif fonts. On macOS the builder uses installed Times New Roman; it falls back to standard PDF Times fonts elsewhere. Font files are not redistributed. TeX uses mathptmx.

Scientific content remains in scripts/paper_content.py. scripts/paper_layout.py transforms only hierarchy, numbering and typography. scripts/build_paper_pdf.py generates both the PDF and paper/main.tex, plus paper/jev_conference.sty. scripts/render_paper_math.py renders the unchanged expressions with serif math. Compile paper/main.tex when using the built-in LaTeX editor or an external TeX installation; the reports source mirror depends on that project.

The before-format PDF/TeX and builder are archived under archive/2026-10-24-before-conference-format/. Original experiment data were not rerun or changed.

Verification: 66 prose paragraphs, 25 tables, 8 equations, 10 figures and 15 reference entries retained. Existing 25 numerical-evidence files match their pre-format hashes. The complete 21-page PDF was rendered and visually reviewed; text stayed within the intended column; LaTeX compilation succeeded and 73 tests passed.
