#!/usr/bin/env python3
"""Build a serif, single-column conference preprint and matching editable TeX.

All scientific content still comes from paper_content.blocks(). Formatting
follows the visual proportions of Attention Is All You Need, not its prose.
"""
import sys,re,json,html,shutil
from pathlib import Path
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,LongTable,TableStyle,PageBreak,KeepTogether,Flowable,HRFlowable,BaseDocTemplate,Frame,PageTemplate
from PIL import Image as PILImage
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_content import blocks,TITLE,ROOT
from paper_layout import conference_blocks,STYLE
OUT=ROOT.parent/'output/pdf/jev_safe_visual_grounding_paper.pdf'
TEXT_WIDTH=5.5*inch
BODY_FONT,BOLD_FONT='Times-Roman','Times-Bold'
# Embed locally installed serif fonts so PDF viewers preserve real bold/italic.
serif=Path('/System/Library/Fonts/Supplemental')
fontfiles={'PaperSerif':'Times New Roman.ttf','PaperSerifBold':'Times New Roman Bold.ttf','PaperSerifItalic':'Times New Roman Italic.ttf','PaperSerifBoldItalic':'Times New Roman Bold Italic.ttf'}
if all((serif/f).exists() for f in fontfiles.values()):
 for name,filename in fontfiles.items():pdfmetrics.registerFont(TTFont(name,str(serif/filename)))
 pdfmetrics.registerFontFamily('PaperSerif',normal='PaperSerif',bold='PaperSerifBold',italic='PaperSerifItalic',boldItalic='PaperSerifBoldItalic')
 BODY_FONT,BOLD_FONT='PaperSerif','PaperSerifBold'
TOKENS={'E_real_fit':(r'$E_{\mathrm{real}}$','<i>E</i><sub>real</sub>'),'y_i':(r'$y_i$','<i>y</i><sub>i</sub>'),'a_i':(r'$a_i$','<i>a</i><sub>i</sub>'),'pi_correct':(r'$\widehat\pi_{\mathrm{correct}}$','<i>π</i><sub>correct</sub>'),'U_B':(r'$U_B$','<i>U</i><sub>B</sub>'),'U_D':(r'$U_D$','<i>U</i><sub>D</sub>'),'U_E':(r'$U_E$','<i>U</i><sub>E</sub>')}


def esc(t):
 return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(t))

def textext(t):
 s=esc(t)
 for token,(latex,markup) in TOKENS.items():s=s.replace(esc(token),latex)
 return re.sub(r'\[(\d{1,2})\]',lambda m:r'\cite{ref'+m[1]+'}',s)

def widths(n):
 if n==3:return [.22,.56,.22]
 if n<=2:return [1/n]*n
 return [.22]+[.78/(n-1)]*(n-1)

def tex(doc):
 lines=[r'\documentclass[10pt]{article}',r'\usepackage{graphicx,booktabs,longtable,array,amsmath,microtype,hyperref}',r'\usepackage{jev_conference}',r'\hypersetup{hidelinks}',r'\title{'+esc(TITLE)+r'}',r'\author{Anonymous Authors}',r'\date{}',r'\begin{document}',r'\maketitle']
 references=False;appendix=False;i=0
 while i<len(doc):
  x=doc[i];k=x['kind']
  if k=='heading':
   if x['title']=='Abstract':
    i+=1;lines += [r'\begin{abstract}',textext(doc[i]['text']),r'\end{abstract}']
   elif x['title']=='References':
    lines.append(r'\begin{thebibliography}{99}');references=True
   else:
    if references:lines.append(r'\end{thebibliography}');references=False
    if x['number']=='A' and not appendix:lines.append(r'\appendix');appendix=True
    command='section' if x['level']==1 else 'subsection';lines.append('\\'+command+'{'+esc(x['title'])+'}')
  elif k=='paragraph':lines.append(textext(x['text'])+'\n')
  elif k=='equation':
   expression=x['tex'] if len(x['lines'])==1 else r'\begin{gathered}'+r'\\[3pt]'.join(x['lines'])+r'\end{gathered}'
   lines += [r'\begin{equation}',expression,r'\label{eq:'+str(x['number'])+'}',r'\end{equation}']
  elif k=='page':
   if references:lines.append(r'\end{thebibliography}');references=False
   lines.append(r'\clearpage')
  elif k=='reference':lines.append(r'\bibitem{ref'+x['number']+'} '+esc(x['text'])+r' \url{'+x['url']+'}')
  elif k=='figure':
   path='figures/extended/'+Path(x['path']).name
   lines += [r'\begin{figure}[htbp]',r'\centering',r'\includegraphics[width=\linewidth,height=3.3in,keepaspectratio]{'+path+r'}',r'\caption{'+textext(x['caption'])+r'}',r'\label{fig:'+str(x['number'])+'}',r'\end{figure}']
  elif k=='table':
   n=len(x['heads']);cols=''.join(r'>{\raggedright\arraybackslash}p{\dimexpr'+f'{w:.4f}'+r'\textwidth-2\tabcolsep\relax}' for w in widths(n))
   lines += [r'\begingroup\fontsize{8.5}{10}\selectfont',r'\begin{longtable}{'+cols+r'}',r'\caption{'+textext(x['caption'])+r'}\label{tab:'+str(x['number'])+r'}\\',r'\toprule',' & '.join(r'\textbf{'+esc(h)+'}' for h in x['heads'])+r'\\\midrule',r'\endfirsthead',r'\multicolumn{'+str(n)+r'}{l}{\small Table \thetable: continued}\\\toprule',' & '.join(r'\textbf{'+esc(h)+'}' for h in x['heads'])+r'\\\midrule',r'\endhead']
   lines += [' & '.join(textext(v) for v in row)+r'\\' for row in x['data']]
   lines += [r'\bottomrule\end{longtable}\endgroup']
  i+=1
 if references:lines.append(r'\end{thebibliography}')
 lines.append(r'\end{document}')
 return '\n'.join(lines)+'\n'

class NumberedEquation(Flowable):
 def __init__(self,path,number):
  super().__init__();self.path=str(path);self.number=number
  with PILImage.open(path) as im:w,h=im.size
  nw,nh=w*72/250,h*72/250;scale=min(1,(TEXT_WIDTH-30)/nw,55/nh)
  self.iw,self.ih=nw*scale,nh*scale;self.width=TEXT_WIDTH;self.height=self.ih+12
 def draw(self):
  self.canv.drawImage(self.path,(self.width-24-self.iw)/2,6,width=self.iw,height=self.ih,mask='auto')
  self.canv.setFont(BODY_FONT,10);self.canv.drawRightString(self.width,(self.height-10)/2,'('+str(self.number)+')')

def footer(c,d):
 c.setFillColor(colors.black);c.setFont(BODY_FONT,10);c.drawCentredString(letter[0]/2,.48*inch,str(d.page))

def main():
 source=blocks();doc=conference_blocks(source);styles=getSampleStyleSheet()
 body=ParagraphStyle('PaperBody',parent=styles['BodyText'],fontName=BODY_FONT,fontSize=10,leading=11.5,alignment=TA_JUSTIFY,spaceAfter=5,allowWidows=0,allowOrphans=0,textColor=colors.black)
 heading=ParagraphStyle('PaperHeading',parent=body,fontName=BOLD_FONT,fontSize=12,leading=14,alignment=TA_LEFT,spaceBefore=14,spaceAfter=7,keepWithNext=True)
 subheading=ParagraphStyle('PaperSubheading',parent=heading,fontSize=10,leading=12,spaceBefore=10,spaceAfter=5)
 abstract=ParagraphStyle('PaperAbstract',parent=body,leftIndent=.5*inch,rightIndent=.5*inch,spaceAfter=9)
 small=ParagraphStyle('PaperSmall',parent=body,fontSize=8.5,leading=10,alignment=TA_LEFT,spaceAfter=5)
 cell=ParagraphStyle('PaperCell',parent=small,spaceAfter=0)
 cellhead=ParagraphStyle('PaperCellHead',parent=cell,fontName=BOLD_FONT)
 title=ParagraphStyle('PaperTitle',parent=heading,fontSize=17,leading=20,alignment=TA_CENTER,spaceBefore=0,spaceAfter=0)
 centered=ParagraphStyle('PaperCentered',parent=body,fontName=BOLD_FONT,alignment=TA_CENTER)
 caption=ParagraphStyle('PaperCaption',parent=small,fontSize=9,leading=10.5,spaceAfter=8)
 def xml(t):
  t=html.escape(str(t))
  for token,(latex,markup) in TOKENS.items():t=re.sub(r'\b'+re.escape(token)+r'\b',lambda m:markup,t)
  return re.sub(r'\[(\d{1,2})\]',lambda m:'<link href="#ref'+m[1]+'" color="black">['+m[1]+']</link>',t)
 def P(t,style=body):return Paragraph(xml(t),style)
 story=[HRFlowable(width=TEXT_WIDTH,thickness=4,color=colors.black,lineCap='butt'),Spacer(1,13),P(TITLE,title),Spacer(1,11),HRFlowable(width=TEXT_WIDTH,thickness=.5,color=colors.black,lineCap='butt'),Spacer(1,20),P('Anonymous Authors',centered),Spacer(1,17)]
 eqindex=0;i=0
 while i<len(doc):
  x=doc[i];k=x['kind']
  if k=='heading':
   if x['title']=='Abstract':
    story += [P('Abstract',ParagraphStyle('AbstractHead',parent=heading,alignment=TA_CENTER,spaceBefore=0,spaceAfter=10))];i+=1;story += [P(doc[i]['text'],abstract),Spacer(1,5)]
   else:story.append(P(x['text'],heading if x['level']==1 else subheading))
  elif k=='paragraph':story.append(P(x['text']))
  elif k=='equation':
   story.append(NumberedEquation(ROOT/'results/extended/math'/f'equation_{eqindex}.png',x['number']));eqindex+=1
  elif k=='page':story.append(PageBreak())
  elif k=='reference':
   content='<a name="ref'+x['number']+'"/>['+x['number']+'] '+html.escape(x['text'])+' <link href="'+html.escape(x['url'],quote=True)+'" color="black">'+html.escape(x['url'])+'</link>'
   story.append(Paragraph(content,small))
  elif k=='figure':
   path=ROOT/x['path']
   with PILImage.open(path) as im:w,h=im.size
   scale=min(TEXT_WIDTH/w,235/h)
   story.append(KeepTogether([Spacer(1,5),Image(str(path),width=w*scale,height=h*scale),Spacer(1,5),Paragraph('<b>Figure '+str(x['number'])+':</b> '+xml(x['caption']),caption)]))
  elif k=='table':
   n=len(x['heads']);cap=Paragraph('<b>Table '+str(x['number'])+':</b> '+xml(x['caption']),caption)
   data=[[cap]+['']*(n-1),[P(h,cellhead) for h in x['heads']]]+[[P(v,cell) for v in row] for row in x['data']]
   table=LongTable(data,colWidths=[TEXT_WIDTH*f for f in widths(n)],repeatRows=2,hAlign='CENTER')
   table.setStyle(TableStyle([('SPAN',(0,0),(-1,0)),('NOSPLIT',(0,0),(-1,2)),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,1),(-1,1),.75,colors.black),('LINEBELOW',(0,1),(-1,1),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.75,colors.black),('LEFTPADDING',(0,0),(-1,-1),3.5),('RIGHTPADDING',(0,0),(-1,-1),3.5),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),('LEFTPADDING',(0,0),(-1,0),0),('RIGHTPADDING',(0,0),(-1,0),0)]))
   story += [table,Spacer(1,8)]
  i+=1
 OUT.parent.mkdir(parents=True,exist_ok=True)
 output_doc=BaseDocTemplate(str(OUT),pagesize=letter,leftMargin=1.5*inch,rightMargin=1.5*inch,topMargin=inch,bottomMargin=inch,title=TITLE,author='Anonymous Authors')
 # Explicit zero frame padding preserves the reference's true 5.5in text block.
 frame=Frame(output_doc.leftMargin,output_doc.bottomMargin,output_doc.width,output_doc.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='body')
 output_doc.addPageTemplates(PageTemplate(id='paper',frames=[frame],onPage=footer));output_doc.build(story)
 paper=ROOT.parent/'paper';figures=paper/'figures/extended';figures.mkdir(parents=True,exist_ok=True)
 for x in doc:
  if x['kind']=='figure':shutil.copy2(ROOT/x['path'],figures/Path(x['path']).name)
 (paper/'jev_conference.sty').write_text(STYLE)
 source_tex=tex(doc);(paper/'main.tex').write_text(source_tex);(ROOT/'reports/submission_manuscript.tex').write_text(source_tex)
 (ROOT/'reports/manuscript_content.json').write_text(json.dumps(doc,indent=2)+'\n')
 # Scientific tables, formulas, references and figures must survive reformatting.
 for kind,key in [('table','data'),('equation','tex'),('reference','url'),('figure','path')]:
  assert [x[key] for x in source if x['kind']==kind]==[x[key] for x in doc if x['kind']==kind],kind
 print(OUT)
if __name__=='__main__':main()
