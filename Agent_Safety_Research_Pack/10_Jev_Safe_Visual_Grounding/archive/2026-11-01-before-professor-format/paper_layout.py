"""Conference presentation of the unchanged experimental manuscript blocks.

Proportions follow the single-column NIPS 2017 visual reference. This is a
local preprint layout, not an official venue template or acceptance claim.
"""
import copy,re

HEADINGS={
 '1. Introduction and research questions':[(1,'1','Introduction')],
 '2. Related work and evidence boundaries':[(1,'2','Related Work')],
 '3. Model interface, policies and mathematical setup':[(1,'3','Native Confidence and Selective Execution')],
 '4. Data, annotation and provenance audit':[(1,'4','Experimental Setup'),(2,'4.1','Data, Annotation, and Provenance')],
 '5. Evaluation and uncertainty protocol':[(2,'4.2','Evaluation Protocol')],
 '6. Results: real-interface usefulness and base localization':[(1,'5','Results'),(2,'5.1','Frozen-Policy Transfer and Localization')],
 '7. Diagnostics and mathematical decision analysis':[(2,'5.2','Calibration and Decision Analysis')],
 '8. Same-input model comparison, latency and cost':[(2,'5.3','Model Comparison, Latency, and Cost')],
 '9. Discussion, limitations and research implications':[(1,'6','Discussion and Limitations')],
 '10. Ethics and reproducibility':[(2,'6.1','Ethics and Reproducibility')],
 '11. Conclusion':[(1,'7','Conclusion')],
 'Appendix A. Complete subgroup diagnostics':[(1,'A','Additional Results and Subgroup Diagnostics')],
 'Appendix B. Traceable qualitative examples':[(1,'B','Qualitative Examples')],
 'Appendix C. Reviewer-driven label, geometry and recalibration experiments':[(1,'C','Label Sensitivity and Recalibration')],
 'C.1 Label and geometry sensitivity':[(2,'C.1','Label and Geometry Sensitivity')],
 'C.2 Brier skill and threshold-free ranking':[(2,'C.2','Brier Skill and Threshold-Free Ranking')],
 'C.3 Exploratory real-data recovery with source separation':[(2,'C.3','Real-Data Recalibration')],
 'C.4 New collection protocol and completion status':[(2,'C.4','Repeatability and Model Comparison')],
 'Appendix D. Historical published VLM and price context':[(1,'D','Published VLM and Price Context')],
}
# Line breaking is typographic only: the original expressions remain in `tex`.
def equation_lines(tex):
 if tex.startswith(r'\widehat C(t)'):
  return tex.split(r',\quad ')
 if tex.startswith(r'\widehat C_{TP}'):
  return tex.split(r',\quad')
 return [tex]

def conference_blocks(source):
 doc=copy.deepcopy(source)
 appendix=next(i for i,x in enumerate(doc) if x.get('text','').startswith('Appendix A.'))
 refs=next(i for i,x in enumerate(doc) if x.get('text')=='References')
 ordered=doc[:appendix]+doc[refs:]+doc[appendix:refs]
 result=[];table=figure=equation=0;in_appendix=False
 for x in ordered:
  if x['kind']=='page':continue
  if x['kind']=='heading':
   if x['text'] in ['Abstract','References']:
    result.append(dict(x,level=1,number='',title=x['text']));continue
   for level,number,title in HEADINGS[x['text']]:
    if number=='A':result.append({'kind':'page'})
    result.append({'kind':'heading','level':level,'number':number,'title':title,'text':number+'  '+title})
   continue
  if x['kind']=='table':
   table+=1;x['number']=table
  elif x['kind']=='figure':
   figure+=1;x['number']=figure;x['caption']=re.sub(r'^Figure\s+\d+\.\s*','',x['caption'])
  elif x['kind']=='equation':
   equation+=1;x['number']=equation;x['lines']=equation_lines(x['tex'])
  for key in ['text','caption']:
   if key in x:
    for old,new in [('Section 8','Section 5.3'),('Section 7','Section 5.2'),('Section 6','Section 5.1')]:x[key]=x[key].replace(old,new)
  result.append(x)
 return result

STYLE=r'''% Local single-column research preprint style, inspired by NIPS 2017.
% It is not an official venue template and asserts no conference acceptance.
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{jev_conference}[2026/10/24 Research preprint layout]
\RequirePackage[letterpaper,textwidth=5.5in,textheight=9in,top=1in,headheight=12pt,headsep=25pt,footskip=30pt]{geometry}
\RequirePackage[T1]{fontenc}
\RequirePackage{mathptmx}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\setlength{\columnsep}{0.25in}
\setlength{\abovecaptionskip}{5pt}
\setlength{\belowcaptionskip}{6pt}
\setlength{\tabcolsep}{3.5pt}
\setlength{\LTpre}{4pt}
\setlength{\LTpost}{8pt}
\renewcommand{\arraystretch}{1.05}
\makeatletter
\renewcommand{\section}{\@startsection{section}{1}{\z@}{-2.2ex plus -0.5ex minus -0.2ex}{1.1ex plus 0.2ex}{\normalfont\fontsize{12}{14}\selectfont\bfseries}}
\renewcommand{\subsection}{\@startsection{subsection}{2}{\z@}{-1.8ex plus -0.4ex minus -0.2ex}{0.8ex plus 0.2ex}{\normalfont\fontsize{10}{12}\selectfont\bfseries}}
\renewcommand{\maketitle}{\par\begingroup\centering
\hrule height 4pt\vskip 0.18in
{\fontsize{17}{20}\selectfont\bfseries\@title\par}
\vskip 0.15in\hrule height 0.5pt\vskip 0.28in
{\normalsize\bfseries\@author\par}\vskip 0.26in
\endgroup}
\renewenvironment{abstract}{\begin{center}\large\bfseries Abstract\end{center}\vspace{-3pt}\begin{list}{}{\leftmargin=0.5in\rightmargin=0.5in}\item\relax}{\end{list}\vspace{8pt}}
\long\def\@makecaption#1#2{\vskip\abovecaptionskip{\small #1: #2\par}\vskip\belowcaptionskip}
\makeatother
\pagestyle{plain}
'''
