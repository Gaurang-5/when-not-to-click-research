"""Journal manuscript presentation based on the professor's supplied example.

Local format only: no publisher logo, DOI, acceptance or license assertion.
Scientific prose and numerical evidence remain in paper_content.py.
"""
import copy,re

HEADINGS={
 '1. Introduction and research questions':[(1,'','Introduction')],
 '2. Related work and evidence boundaries':[(1,'','Related work')],
 '3. Model interface, policies and mathematical setup':[(1,'','Materials and methods'),(2,'','Native confidence and selective execution')],
 '4. Data, annotation and provenance audit':[(2,'','Data, annotation and provenance')],
 '5. Evaluation and uncertainty protocol':[(2,'','Evaluation and uncertainty protocol')],
 '6. Results: real-interface usefulness and base localization':[(1,'','Results'),(2,'','Frozen-policy transfer and localization')],
 '7. Diagnostics and mathematical decision analysis':[(2,'','Calibration and decision analysis')],
 '8. Same-input model comparison, latency and cost':[(2,'','Model comparison, latency and cost')],
 '9. Discussion, limitations and research implications':[(1,'','Discussion')],
 '10. Ethics and reproducibility':[(1,'','Ethics, data availability and reproducibility')],
 '11. Conclusion':[(1,'','Conclusion')],
 'Appendix A. Complete subgroup diagnostics':[(1,'A','Additional results and subgroup diagnostics')],
 'Appendix B. Traceable qualitative examples':[(1,'B','Qualitative examples')],
 'Appendix C. Reviewer-driven label, geometry and recalibration experiments':[(1,'C','Label sensitivity and recalibration')],
 'C.1 Label and geometry sensitivity':[(2,'C.1','Label and geometry sensitivity')],
 'C.2 Brier skill and threshold-free ranking':[(2,'C.2','Brier skill and threshold-free ranking')],
 'C.3 Exploratory real-data recovery with source separation':[(2,'C.3','Real-data recalibration')],
 'C.4 New collection protocol and completion status':[(2,'C.4','Repeatability and model comparison')],
 'Appendix D. Historical published VLM and price context':[(1,'D','Published VLM and price context')],
}
# Labels use authors and years already recorded in the scientific source.
CITATIONS={
 '1':('Wu et al.','2024'), '2':('Wang, Fan, and Wang','2026'),
 '3':('Kumar et al.','2026'), '4':('Feng et al.','2026'),
 '5':('Li, Chen, and Zhang','2026'), '6':('OpenAI','2026a'),
 '7':('OpenAI','2026b'), '8':('ScreenSpot-v2-variants','n.d.'),
 '9':('TypeSafe AI','2026'), '10':('Geifman and El-Yaniv','2017'),
 '11':('Angelopoulos et al.','2021'), '12':('Angelopoulos et al.','2024'),
 '13':('Qwen Team','2025'), '14':('Li et al.','2025'), '15':('Qin et al.','2025'),
}
REFERENCE_TEXT={
 '1':'Wu, Z., et al. 2024. OS-ATLAS: A Foundation Action Model for Generalist GUI Agents.',
 '2':'Wang, Q., Y. Fan, and X. E. Wang. 2026. SafeGround: Know When to Trust GUI Grounding Models via Uncertainty Calibration.',
 '3':'Kumar, D., et al. 2026. Uncertainty Quantification for Computer-Use Agents: A Benchmark across Vision-Language Models and GUI Grounding Datasets.',
 '4':'Feng, Y., et al. 2026. CORA: Conformal Risk-Controlled Agents for Safeguarded Mobile GUI Automation.',
 '5':'Li, H., Y. Chen, and Z. Zhang. 2026. GoClick: Lightweight Element Grounding Model for Autonomous GUI Interaction. Table 3 and Section 4.1.2.',
 '6':'OpenAI. 2026a. GPT-4o model documentation and pricing. Accessed 23 October 2026.',
 '7':'OpenAI. 2026b. Images and vision: tile-based image tokenization. Accessed 23 October 2026.',
 '8':'ScreenSpot-v2-variants. n.d. Dataset repository. Pinned source revision aa4d83b6833d77d3bb3b7cb769951e2db80052b6.',
 '9':'TypeSafe AI. 2026. Introducing System One Models and Jev. Public input/output pricing. Accessed 23 October 2026.',
 '10':'Geifman, Y., and R. El-Yaniv. 2017. Selective Classification for Deep Neural Networks. NeurIPS.',
 '11':'Angelopoulos, A. N., S. Bates, E. J. Candes, M. I. Jordan, and L. Lei. 2021. Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control. arXiv preprint (2021/2022 version history).',
 '12':'Angelopoulos, A. N., S. Bates, A. Fisch, L. Lei, and T. Schuster. 2024. Conformal Risk Control. ICLR.',
 '13':'Qwen Team. 2025. Qwen2.5-VL Technical Report.',
 '14':'Li, K., et al. 2025. ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use.',
 '15':'Qin, Y., et al. 2025. UI-TARS: Pioneering Automated GUI Interaction with Native Agents.',
}
CITATION_PATTERN=r'\[(\d{1,2})(?:,\s*([^\]]+))?\]'

def citation_label(number,locator=None):
 author,year=CITATIONS[str(number)]
 return '('+author+' '+year+(', '+locator if locator else '')+')'

def equation_lines(tex):
 if tex.startswith(r'\widehat C(t)'):return tex.split(r',\quad ')
 if tex.startswith(r'\widehat C_{TP}'):return tex.split(r',\quad')
 return [tex]

def journal_blocks(source):
 doc=copy.deepcopy(source)
 appendix=next(i for i,x in enumerate(doc) if x.get('text','').startswith('Appendix A.'))
 refs=next(i for i,x in enumerate(doc) if x.get('text')=='References')
 ethics=next(i for i,x in enumerate(doc) if x.get('text','').startswith('10. Ethics'))
 conclusion=next(i for i,x in enumerate(doc) if x.get('text','').startswith('11. Conclusion'))
 refitems=sorted((x for x in doc[refs:] if x['kind']=='reference'),key=lambda x:REFERENCE_TEXT[x['number']].lower())
 ordered=doc[:ethics]+doc[conclusion:appendix]+doc[ethics:conclusion]+[doc[refs]]+refitems+doc[appendix:refs]
 result=[];table=figure=equation=0
 for x in ordered:
  if x['kind']=='page':continue
  if x['kind']=='heading':
   if x['text'] in ['Abstract','References']:
    result.append(dict(x,level=1,number='',title=x['text']));continue
   for level,number,title in HEADINGS[x['text']]:
    if number=='A':result.append({'kind':'page'})
    display=('Appendix '+number+'. ' if len(number)==1 and number else number+' ' if number else '')+title
    result.append({'kind':'heading','level':level,'number':number,'title':title,'text':display})
   continue
  if x['kind']=='table':table+=1;x['number']=table
  elif x['kind']=='figure':
   figure+=1;x['number']=figure;x['caption']=re.sub(r'^Figure\s+\d+\.\s*','',x['caption'])
  elif x['kind']=='equation':equation+=1;x['number']=equation;x['lines']=equation_lines(x['tex'])
  elif x['kind']=='reference':x['display_text']=REFERENCE_TEXT[x['number']]
  for key in ['text','caption']:
   if key in x and x['kind']!='reference':
    for old,new in [('Section 8','the "Model comparison, latency and cost" subsection'),('Section 7','the "Calibration and decision analysis" subsection'),('Section 6','the "Frozen-policy transfer and localization" subsection'),('Section 3','the "Native confidence and selective execution" subsection')]:x[key]=x[key].replace(old,new)
  result.append(x)
 return result

# Retain the import used by the equation renderer and offline reproduction.
conference_blocks=journal_blocks

STYLE=r'''% Local journal manuscript layout based on the supplied published example.
% No publisher branding, DOI, license or acceptance is asserted.
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{jev_journal}[2026/11/01 Journal manuscript layout]
\RequirePackage[paperwidth=210mm,paperheight=280mm,left=25.4mm,right=23.6mm,top=18mm,bottom=18mm,headheight=10pt,headsep=12pt,footskip=18pt]{geometry}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathptmx,helvet,xcolor,fancyhdr}
\definecolor{journalblue}{HTML}{171669}
\definecolor{abstractshade}{HTML}{E8E7F0}
\setlength{\parindent}{12pt}
\setlength{\parskip}{0pt}
\setlength{\abovecaptionskip}{5pt}
\setlength{\belowcaptionskip}{6pt}
\setlength{\tabcolsep}{3.5pt}
\setlength{\LTpre}{5pt}
\setlength{\LTpost}{9pt}
\renewcommand{\arraystretch}{1.05}
\renewcommand{\theequation}{\arabic{equation}}
\makeatletter
\renewcommand{\section}{\@startsection{section}{1}{\z@}{-2.4ex plus -0.5ex minus -0.2ex}{1.2ex plus 0.2ex}{\normalfont\sffamily\fontsize{11}{13}\selectfont\bfseries\color{journalblue}}}
\renewcommand{\subsection}{\@startsection{subsection}{2}{\z@}{-2ex plus -0.4ex minus -0.2ex}{0.9ex plus 0.2ex}{\normalfont\sffamily\fontsize{10.5}{12.5}\selectfont\bfseries\itshape\color{journalblue}}}
\renewcommand{\maketitle}{\par\begingroup
{\sffamily\fontsize{8}{10}\selectfont RESEARCH MANUSCRIPT\par}\vspace{6pt}
{\color{journalblue}\hrule height 0.6pt}\vspace{18pt}
{\sffamily\fontsize{14}{17}\selectfont\bfseries\color{journalblue}\@title\par}
\vspace{8pt}{\sffamily\fontsize{10.5}{12.5}\selectfont\@author\par}\vspace{14pt}
\endgroup}
\renewenvironment{abstract}{\par\begingroup\sffamily\fontsize{9}{10.5}\selectfont\setlength{\fboxsep}{10pt}\noindent\colorbox{abstractshade}\bgroup\begin{minipage}{0.75\textwidth}\textbf{\color{journalblue}ABSTRACT}\par\smallskip\setlength{\parindent}{0pt}}{\end{minipage}\egroup\endgroup\par\vspace{17pt}}
\long\def\@makecaption#1#2{\vskip\abovecaptionskip{\sffamily\fontsize{9}{10.5}\selectfont #1. #2\par}\vskip\belowcaptionskip}
\makeatother
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyhead[L]{\sffamily\fontsize{7.5}{9}\selectfont WHEN NOT TO CLICK}
\fancyhead[R]{\sffamily\fontsize{7.5}{9}\selectfont\thepage}
\fancypagestyle{plain}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}\fancyfoot[R]{\sffamily\fontsize{7.5}{9}\selectfont\thepage}}
\AtBeginDocument{\fontsize{10.5}{12.5}\selectfont}
'''
