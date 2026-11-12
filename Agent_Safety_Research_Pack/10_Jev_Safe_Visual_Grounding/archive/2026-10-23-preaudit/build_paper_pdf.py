#!/usr/bin/env python3
"""Build the review manuscript PDF from frozen study artifacts."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "output" / "pdf" / "jev_safe_visual_grounding_paper.pdf"


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#4B5563"))
    canvas.drawString(18 * mm, 11 * mm, "When Not to Click - anonymous review manuscript")
    canvas.drawRightString(192 * mm, 11 * mm, str(doc.page))
    canvas.restoreState()


def p(text, style):
    return Paragraph(text, style)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2,
                          leading=12.2, alignment=TA_JUSTIFY, spaceAfter=5)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                        leading=17, textColor=colors.HexColor("#111827"), spaceBefore=10, spaceAfter=5)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11,
                        leading=14, textColor=colors.HexColor("#1F2937"), spaceBefore=7, spaceAfter=4)
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=21,
                           leading=25, alignment=TA_CENTER, textColor=colors.HexColor("#111827"))
    abstract = ParagraphStyle("Abstract", parent=body, fontSize=8.7, leading=11.4,
                              leftIndent=12 * mm, rightIndent=12 * mm)
    caption = ParagraphStyle("Caption", parent=body, fontSize=8, leading=10, alignment=TA_CENTER,
                             textColor=colors.HexColor("#374151"), spaceBefore=3, spaceAfter=8)
    ref = ParagraphStyle("Ref", parent=body, fontSize=8, leading=10, leftIndent=5 * mm, firstLineIndent=-5 * mm)

    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                          topMargin=16*mm, bottomMargin=17*mm, title="When Not to Click")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates(PageTemplate(id="paper", frames=frame, onPage=footer))
    story = []

    story += [Spacer(1, 7*mm), p("When Not to Click: Stress-Testing Native Visual Decisions for Absent and Ambiguous GUI Targets", title),
              Spacer(1, 3*mm), p("<b>Anonymous Authors</b>", ParagraphStyle("Author", parent=body, alignment=TA_CENTER)),
              Spacer(1, 5*mm)]
    status = Table([[p("REVIEW MANUSCRIPT - SYNTHETIC AND EXTERNAL STUDIES EXECUTED", styles["Normal"])]], colWidths=[170*mm])
    status.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF7ED")),
                                ("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#F59E0B")),
                                ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#92400E")),
                                ("ALIGN",(0,0),(-1,-1),"CENTER"), ("TOPPADDING",(0,0),(-1,-1),6),
                                ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story += [status, Spacer(1, 5*mm), p("<b>Abstract</b>", h2)]
    story.append(p("Visual grounding systems often emit a location even when a requested interface target is absent or non-unique. We evaluate whether the native structured outputs of Jev 1.14 - a presence judgement, a caller-defined match-count choice, and a bounding box with confidence - support safer click-or-abstain decisions than box confidence alone. The executed study contains 200 synthetic GUI cases across five disjoint layout families and six target states. Policies were fitted on 80 development cases, selected on 40 calibration cases, frozen, and evaluated once on 80 held-out cases. A box-confidence policy accepted 27/80 cases with 10 incorrect clicks (37.0% selective risk), including 5/10 multiple-target cases. A presence-uniqueness-box gate accepted 26/80 with no observed incorrect clicks, while uniqueness-only accepted all 30 eligible unique targets and no negative case. The multiple-target acceptance difference was -50 percentage points but was not significant after Holm correction (p=0.126). In a separate 951-case two-annotator study, exact status agreement was 79.8%, Cohen's kappa was 0.613, and mean matched box IoU was 0.619. Reviewer-approved Annotator B decisions resolve 259 flagged cases and the remaining 692 use consensus, producing a frozen external label set. The frozen policies were then evaluated on all 951 external cases: 940 outputs parsed successfully and 11 failed closed. The logistic gate accepted 69/951 with no observed incorrect accepts; the three-signal gate accepted 92 with 16 incorrect accepts, while box confidence accepted 127 with 61 incorrect accepts. The findings show external transfer of conservative gating, but do not establish deployment safety.", abstract))

    sections = [
        ("1. Introduction", [
            "GUI agents map natural-language instructions to executable screen coordinates. A plausible coordinate is not evidence that the requested target exists, is uniquely determined, or is safe to click. An absent Delete button and two visible Approve buttons pose different risks, yet a localizer designed to return one region may still produce a box.",
            "This paper studies Jev 1.14's experimental visual interface. A single request can return a Noul presence score, a Choice distribution over none, one, or several matches, and one Box with localization confidence. We ask whether fixed gates composed from these outputs reduce unsafe accepted clicks relative to box confidence alone.",
            "The contribution is an exact-interface measurement: a controlled 200-call study with six target states; family-separated development, calibration, and held-out test sets; frozen policy evaluation with retained API responses; and a separately collected, reviewer-resolved 951-case external study executed with the already-frozen policies and fail-closed parsing."
        ]),
        ("2. Related Work and Novelty Boundary", [
            "ScreenSpot introduced realistic single-step GUI grounding across mobile, desktop, and web environments [1]. OS-Atlas later corrected annotation errors and named the revision ScreenSpot-V2 [2]. ScreenSpot-Pro emphasizes high-resolution professional applications and small targets [3]. These benchmarks mainly measure whether a predicted point falls within a visible target; they do not by themselves resolve safe behavior when no unique target exists.",
            "SafeGround uses dispersion from stochastic grounding samples and calibration to control false discoveries [4]. Argus compares post-hoc uncertainty across models, datasets, and observable interfaces, finding that rankings transfer more reliably across datasets than model classes [5]. CORA wraps a GUI policy with a conformal execute/abstain controller [6]. These works preclude broad novelty claims for confidence gating or abstention. Our narrower question concerns the information in Jev's exact native output trio."
        ]),
        ("3. Model Interface and Policies", [
            "Each request pins jev-1.14.0 and sends one screenshot with presence, match-count, and Box questions. Match-count criteria define none, exactly one, or several valid visible matches. Box is treated as forced-output: a syntactically valid region is not evidence that the target exists. The parser fails closed on version drift, malformed probabilities, non-finite values, and degenerate boxes.",
            "Policies are: A, accept every valid Box; B, threshold Box confidence; C, threshold the minimum of presence and Box confidence; D, threshold the minimum of presence, exactly-one probability, and Box confidence; and E, an L2-regularized logistic gate on native scores and simple interactions. Presence-only, uniqueness-only, and presence-plus-uniqueness are ablations. Calibration maximizes coverage subject to an empirical selective-risk ceiling of 30%."
        ]),
        ("4. Synthetic Dataset and Protocol", [
            "The pilot contains 200 locally rendered screenshots: 25 templates nested in five layout families, with eight target-state variants per template. Sidebar and kanban form development (80 cases), tables form calibration (40), and dialogs plus toolbars form the held-out test (80). Each template contributes three unique cases and one each of absent, multiple, occluded, offscreen, and unclear.",
            "Generator state and DOM geometry provide procedural labels. A click is correct only for a uniquely eligible case when its predicted center lies inside the reference box and IoU is at least 0.5. Every accepted click on a non-eligible state is incorrect. All requests completed before held-out outcomes were analyzed.",
            "Selective risk is incorrect accepted actions divided by accepted actions; coverage is accepted actions divided by all cases. We also report marginal incorrect-action rate, state-specific false acceptance, and useful unique automation. Intervals resample templates. Paired primary comparisons use template-level sign randomization with Holm correction over absent and multiple endpoints."
        ]),
        ("5. Human Annotation Study", [
            "Two annotators independently labeled the same 951 candidate external cases without viewing model predictions. Each selected one of six states (unique, absent, multiple, occluded, offscreen, unclear), drew all valid clickable boxes for unique or multiple cases, and recorded confidence. Automated validation required exactly one status, valid box cardinality, and in-bounds geometry. Thirteen initial format defects were corrected; both complete corrected exports pass all structural checks.",
            "Before resolution, annotators agreed on 759/951 statuses (79.8%), with Cohen's kappa=0.613. Among 205 same-status cases with comparable boxes, mean maximum-matched IoU was 0.619. A deterministic rule flagged 259 cases. Because Annotator B's complete pass had independent reviewer approval, B's decisions were designated final for those cases. The remaining 692 use two-annotator consensus and matched coordinate means for localizable boxes. The frozen set contains 640 absent, 206 unique, 54 multiple, 27 occluded, 5 offscreen, and 19 unclear cases."
        ]),
    ]
    for heading, paras in sections:
        story.append(p(heading, h1))
        story.extend(p(text, body) for text in paras)

    confusion = ROOT / "results" / "human_annotation" / "status_confusion_matrix.png"
    story += [Spacer(1, 2*mm), Image(str(confusion), width=145*mm, height=117*mm),
              p("Figure 1. Pre-adjudication status confusion matrix (n=951). The largest off-diagonal cell is A unique versus B absent (89 cases).", caption)]

    story += [p("6. Results", h1), p("<b>Operations and validity.</b> The synthetic study issued 200 requests with no retries. All resolved to jev-1.14.0; 199 parsed successfully. One development offscreen case returned a zero-width Box and failed closed. All 80 held-out outputs were valid. Total usage was 457,978 input and 15,425 output tokens, with estimated cost $0.019235 under the recorded pricing rule. Held-out latency was 524 ms mean and 647 ms p95.", body)]

    data = [["Policy", "Coverage", "Errors", "Selective risk", "Unique automation"],
            ["Box confidence B", "33.8%", "10", "37.0%", "56.7%"],
            ["Presence + Box C", "27.5%", "5", "22.7%", "56.7%"],
            ["Three-signal D", "32.5%", "0", "0.0%", "86.7%"],
            ["Logistic E", "36.3%", "0", "0.0%", "96.7%"],
            ["Uniqueness only", "37.5%", "0", "0.0%", "100.0%"]]
    table = Table(data, colWidths=[48*mm, 28*mm, 20*mm, 31*mm, 36*mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F2937")),
                               ("TEXTCOLOR",(0,0),(-1,0),colors.white), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                               ("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
                               ("ALIGN",(1,1),(-1,-1),"CENTER"), ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D1D5DB")),
                               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F9FAFB")]),
                               ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story += [Spacer(1,2*mm), table, p("Table 1. Held-out synthetic results (n=80). Unique automation uses 30 eligible unique cases.", caption)]

    results_paras = [
        "All B-E policies rejected 10/10 absent cases. B's ten incorrect accepts were five multiple and five occluded targets. D made no incorrect accepts but rejected four correctly localized toolbar targets; E rejected one. Uniqueness-only accepted all 30 unique cases and no negative case. All unique cases satisfied the primary localization rule; 27/30 reached IoU at least 0.75 and mean IoU was 0.797.",
        "Absent acceptance was zero for B and D. Multiple-target acceptance fell from 50% under B to zero under D. The cluster-bootstrap difference interval was [-0.80,-0.20]; sign randomization gave p=0.063 before and p=0.126 after Holm correction. We therefore report direction and magnitude without a significance claim.",
        "B covered 62.5% of dialog cases but 5.0% of toolbar cases. D covered 37.5% and 27.5%; E covered 35.0% in both. Two families cannot establish transfer. Held-out Brier/ECE were 0.152/0.191 for presence, 0.238/0.325 for Box confidence against correct localization, and 0.045/0.167 for the logistic score.",
        "Annotator A used unique more often (275 versus 206), while B used absent more often (640 versus 582). The moderate kappa and 192 status disagreements motivated the prespecified resolution process. Review flags also include 45 same-status cases with IoU below 0.5, four box-count disagreements, and 36 cases with at least one low-confidence annotation; reasons overlap."
    ]
    story.extend(p(x, body) for x in results_paras)

    story += [p("External confirmatory evaluation", h2), p("The frozen policies were applied once to all 951 reviewer-resolved cases. Of 951 post-credential responses, 940 parsed successfully and 11 failed closed: six had degenerate or reversed boxes and five had Choice probabilities that did not sum to one. No automatic retries were used. The log contains 1,022 records because 71 earlier requests were rejected during credential setup and used no tokens. Billable responses used 3,160,605 input and 72,436 output tokens, for estimated cost $0.132745. Latency across records was 456 ms mean and 625 ms p95.", body)]
    external_data = [["Policy", "Accept", "Coverage", "Errors", "Risk", "Unique auto."],
                     ["Box confidence B", "127", "13.4%", "61", "48.0%", "32.0%"],
                     ["Presence + Box C", "95", "10.0%", "37", "38.9%", "28.2%"],
                     ["Three-signal D", "92", "9.7%", "16", "17.4%", "36.9%"],
                     ["Logistic E", "69", "7.3%", "0", "0.0%", "33.5%"],
                     ["Uniqueness only", "73", "7.7%", "1", "1.4%", "35.0%"]]
    external_table = Table(external_data, colWidths=[42*mm, 20*mm, 25*mm, 18*mm, 22*mm, 30*mm], repeatRows=1)
    external_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1F2937")),
                               ("TEXTCOLOR",(0,0),(-1,0),colors.white), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                               ("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
                               ("ALIGN",(1,1),(-1,-1),"CENTER"), ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D1D5DB")),
                               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F9FAFB")]),
                               ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story += [external_table, p("Table 2. External frozen-policy results (n=951). Unique automation uses 206 eligible unique cases.", caption),
              p("D reduced absent false accepts from 15/640 under B to 7/640 (case-weighted difference -1.25 percentage points; Holm-adjusted cluster-sign p=0.0225). It reduced multiple-target wrong accepts from 21/54 to 0/54 (difference -38.9 points; adjusted p=0.00020). E accepted 69 unique cases and no negative case. Zero observed errors among 69 accepts gives an optimistic independent-sampling 95% rule-of-three upper bound of 4.3%; clustering and policy selection prevent treating this as a certified guarantee.", body)]

    policy_fig = ROOT / "results" / "live_policy_comparison.png"
    story += [Image(str(policy_fig), width=155*mm, height=94*mm),
              p("Figure 2. Coverage and selective risk of the frozen held-out synthetic policies.", caption)]

    tail = [
        ("7. Error Analysis", [
            "Box confidence accepted five duplicated and five occluded cases. Presence removed occluded errors but retained duplicates. Match count removed duplicates and, in this cohort, rejected every other negative state. The four D false rejections and one E false rejection were toolbar unique targets with IoU 0.778-0.803, indicating conservative semantic thresholds rather than poor localization.",
            "One development response had left equal to right. In the external study, six responses had degenerate or reversed boxes and five had malformed Choice probability sums. Retaining these cases in denominators while failing closed demonstrates that HTTP success is not equivalent to actionable localization."
        ]),
        ("8. Discussion", [
            "The main empirical lesson is simpler than the initial three-signal hypothesis: native match count carried nearly all useful discrimination on the authored pilot. Joint gates improved markedly over Box confidence but did not improve over uniqueness-only. Future evaluation should treat uniqueness-only as a first-class baseline.",
            "Zero observed errors among 26-30 accepted actions provide weak assurance. Under optimistic independent sampling, zero errors in 26 accepts gives a one-sided 95% rule-of-three upper bound near 11.5%; clustering and policy selection make that illustration optimistic.",
            "The external result changes the practical interpretation of the pilot. The conservative policy ordering transferred, and match-count gating again removed every multiple-target wrong accept. Unique localization accuracy at IoU at least 0.5 was 56.3%, while the zero-error policy covered only 7.3% of all cases. Safety gains therefore came with substantial abstention. The human study also shows label ambiguity; freezing resolution before prediction avoids outcome-dependent adjudication."
        ]),
        ("9. Limitations", [
            "The synthetic interfaces share one generator and vocabulary, and only two layout families are held out. External ground truth uses reviewer-approved Annotator B for 259 flagged cases, which is less independent than a separate third adjudicator. The external cohort is dominated by absent cases (640/951), so aggregate metrics depend on composition. Eleven malformed HTTP-200 outputs were fail-closed abstentions. There is no independent grounding-model baseline. Simulated clicks do not measure downstream harm, and zero observed errors cannot certify true zero risk. Findings apply to one version, prompt, and collection date."
        ]),
        ("10. Ethics and Reproducibility", [
            "Synthetic data contain no personal information. External images retain source and license metadata and require privacy review before release. No real application actions were executed. Credentials remain environment variables and are excluded from logs and archives.",
            "The artifact includes generation code, strict parsing, all 200 synthetic-study API records, all 1,022 external collection records including setup failures, frozen policies and SHA-256 digests, corrected Label Studio exports, final frozen labels, and deterministic evaluation scripts. Seed is 1729; model and prompt are pinned to jev-1.14.0 and presence-count-box-v1."
        ]),
        ("11. Conclusion", [
            "On 80 held-out synthetic cases, Jev 1.14's match-count signal separated unique from non-unique targets more effectively than Box confidence. On 951 external cases, the frozen three-signal gate reduced multiple-target wrong accepts from 21/54 to zero and absent false accepts from 15/640 to 7/640; both cluster-sign comparisons remained significant after Holm correction. The logistic gate accepted 69 cases with no observed incorrect accepts, at 7.3% coverage. This confirms conservative transfer for the evaluated interface while leaving deployment safety unresolved."
        ])
    ]
    for heading, paras in tail:
        story.append(p(heading, h1)); story.extend(p(x, body) for x in paras)

    story.append(p("References", h1))
    refs = [
        "[1] K. Cheng et al. SeeClick: Harnessing GUI Grounding for Advanced Visual GUI Agents. ACL, 2024. arXiv:2401.10935.",
        "[2] Z. Wu et al. OS-ATLAS: A Foundation Action Model for Generalist GUI Agents. ICLR, 2025. arXiv:2410.23218.",
        "[3] K. Li et al. ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use. arXiv:2504.07981, 2025.",
        "[4] Q. Wang, Y. Fan, and X. E. Wang. SafeGround: Know When to Trust GUI Grounding Models via Uncertainty Calibration. arXiv:2602.02419, 2026.",
        "[5] D. Kumar et al. Uncertainty Quantification for Computer-Use Agents. NeurIPS, 2026. arXiv:2606.25760.",
        "[6] Y. Feng et al. CORA: Conformal Risk-Controlled Agents for Safeguarded Mobile GUI Automation. arXiv:2604.09155, 2026.",
        "[7] TypeSafe AI. Jev 1.14 model and Box interface documentation. https://www.jevtypesafeai.com/jev-1-14, 2026."
    ]
    story.extend(p(x, ref) for x in refs)
    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
