#!/usr/bin/env python3
"""Build audited PDF and TeX from the same offline manuscript content."""
import sys,re,json,html,shutil
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,LongTable,TableStyle,PageBreak,KeepTogether
from PIL import Image as PILImage
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_content import blocks,TITLE,ROOT
OUT=ROOT.parent/'output/pdf/jev_safe_visual_grounding_paper.pdf'
def esc(t):
 return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(t))
def tex(doc):
 lines=[r'\documentclass[10pt]{article}',r'\usepackage[a4paper,margin=0.72in]{geometry}',r'\usepackage{graphicx,booktabs,longtable,array,amsmath,microtype,hyperref,xcolor}',r'\hypersetup{colorlinks=true,urlcolor=blue!50!black}',r'\setlength{\parskip}{4pt}',r'\setlength{\parindent}{0pt}',r'\setlength{\LTpre}{4pt}',r'\setlength{\LTpost}{6pt}',r'\title{\textbf{'+esc(TITLE)+r'}}',r'\author{Anonymous Authors}',r'\date{}',r'\begin{document}',r'\maketitle',r'\begin{center}\small Audited research manuscript, 23 October 2026. Post-hoc analyses are identified explicitly.\end{center}']
 for x in doc:
  k=x['kind']
  if k=='heading':lines.append(r'\section*{'+esc(x['text'])+'}')
  elif k=='paragraph':lines.append(esc(x['text'])+'\n')
  elif k=='equation':lines.append(r'\['+x['tex']+r'\]')
  elif k=='page':lines.append(r'\clearpage')
  elif k=='reference':lines.append('['+x['number']+'] '+esc(x['text'])+r' \url{'+x['url']+r'}\par')
  elif k=='figure':
   path='figures/extended/'+Path(x['path']).name;lines += [r'\begin{center}',r'\includegraphics[width=0.95\textwidth,height='+str(x['height'])+r'mm,keepaspectratio]{'+path+r'}',r'\par\small '+esc(x['caption']),r'\end{center}']
  elif k=='table':
   n=len(x['heads']);widths=[.22]+[.78/(n-1)]*(n-1) if n>3 else [1/n]*n
   # subtract column padding from each proportional text width
   cols=''.join(r'>{\raggedright\arraybackslash}p{\dimexpr'+f'{w:.4f}'+r'\textwidth-2\tabcolsep\relax}' for w in widths)
   lines += [r'\begingroup\small',r'\textbf{'+esc(x['caption'])+r'}',r'\begin{longtable}{'+cols+r'}',r'\toprule',' & '.join(r'\textbf{'+esc(h)+'}' for h in x['heads'])+r'\\\midrule',r'\endfirsthead',r'\toprule',' & '.join(esc(h) for h in x['heads'])+r'\\\midrule',r'\endhead']
   lines += [' & '.join(esc(v) for v in row)+r'\\' for row in x['data']]
   lines += [r'\bottomrule\end{longtable}\endgroup']
 lines.append(r'\end{document}')
 return '\n'.join(lines)+'\n'
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#64748b'));c.drawString(18*mm,10*mm,'When Not to Click | audited anonymous manuscript');c.drawRightString(192*mm,10*mm,str(d.page))
def main():
 doc=blocks();styles=getSampleStyleSheet()
 body=ParagraphStyle('ResearchBody',parent=styles['BodyText'],fontName='Helvetica',fontSize=9.2,leading=12.0,alignment=TA_JUSTIFY,spaceAfter=5,allowWidows=0,allowOrphans=0)
 heading=ParagraphStyle('ResearchHeading',parent=styles['Heading1'],fontSize=14,leading=17,spaceBefore=12,spaceAfter=6,keepWithNext=True,textColor=colors.HexColor('#16324a'))
 small=ParagraphStyle('ResearchSmall',parent=body,fontSize=8,leading=10,alignment=0)
 cell=ParagraphStyle('Cell',parent=body,fontSize=8,leading=10,alignment=0,spaceAfter=0)
 title=ParagraphStyle('ResearchTitle',parent=styles['Title'],fontSize=20,leading=24,alignment=TA_CENTER,spaceAfter=12)
 cap=ParagraphStyle('Caption',parent=small,alignment=TA_CENTER,spaceAfter=10)
 def P(t,style=body):return Paragraph(html.escape(str(t)),style)
 story=[P(TITLE,title),P('Anonymous Authors',ParagraphStyle('Author',parent=body,alignment=TA_CENTER)),P('Audited research manuscript | 23 October 2026 | Post-hoc analyses identified explicitly',small),Spacer(1,4*mm)]
 width=174*mm
 equation_index=0
 for x in doc:
  k=x['kind']
  if k=='heading':story.append(P(x['text'],heading))
  elif k=='paragraph':story.append(P(x['text']))
  elif k=='equation':
   eqpath=ROOT/'results/extended/math'/f'equation_{equation_index}.png';equation_index+=1
   im=PILImage.open(eqpath);w,h=im.size;scale=min(width/w,13*mm/h)
   story.append(Image(str(eqpath),width=w*scale,height=h*scale));story.append(Spacer(1,2*mm))
  elif k=='page':story.append(PageBreak())
  elif k=='reference':story.append(Paragraph('['+x['number']+'] '+html.escape(x['text'])+'<br/><link href="'+x['url']+'" color="#245282">'+html.escape(x['url'])+'</link>',small))
  elif k=='figure':
   path=ROOT/x['path'];im=PILImage.open(path);w,h=im.size;scale=min(width/w,x['height']*mm/h)
   story.append(KeepTogether([Spacer(1,2*mm),Image(str(path),width=w*scale,height=h*scale),P(x['caption'],cap)]))
  elif k=='table':
   n=len(x['heads']);fractions=[.22]+[.78/(n-1)]*(n-1) if n>3 else [1/n]*n
   data=[[P(h,ParagraphStyle('Head',parent=cell,textColor=colors.white,fontName='Helvetica-Bold')) for h in x['heads']]]+[[P(v,cell) for v in row] for row in x['data']]
   table=LongTable(data,colWidths=[width*f for f in fractions],repeatRows=1,hAlign='CENTER')
   table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16324a')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f5f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbd5e1')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
   story += [P(x['caption'],ParagraphStyle('TableCaption',parent=small,keepWithNext=True,spaceBefore=6)),table,Spacer(1,3*mm)]
 OUT.parent.mkdir(parents=True,exist_ok=True)
 SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=16*mm,bottomMargin=17*mm,title=TITLE,author='Anonymous Authors').build(story,onFirstPage=footer,onLaterPages=footer)
 figure_dir=ROOT.parent/'paper/figures/extended';figure_dir.mkdir(parents=True,exist_ok=True)
 for x in doc:
  if x['kind']=='figure':shutil.copy2(ROOT/x['path'],figure_dir/Path(x['path']).name)
 source=tex(doc);(ROOT.parent/'paper/main.tex').write_text(source);(ROOT/'reports/submission_manuscript.tex').write_text(source)
 (ROOT/'reports/manuscript_content.json').write_text(json.dumps(doc,indent=2)+'\n')
 print(OUT)
if __name__=='__main__':main()
