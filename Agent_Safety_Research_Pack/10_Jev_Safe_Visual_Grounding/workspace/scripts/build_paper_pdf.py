#!/usr/bin/env python3
"""Build a journal manuscript PDF and matching editable LaTeX project.

Layout follows the professor-supplied Taylor & Francis article example.
Experimental records, equations and scientific claims are not changed.
"""
import sys,re,json,html,shutil
from pathlib import Path
from collections import Counter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY,TA_LEFT
from reportlab.lib.units import inch,mm
from reportlab.platypus import Paragraph,Spacer,Image,LongTable,Table,TableStyle,PageBreak,KeepTogether,Flowable,BaseDocTemplate,Frame,PageTemplate
from PIL import Image as PILImage
from pypdf import PdfReader,PdfWriter,Transformation
EQUATION_PLACEMENTS=[]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from paper_content import blocks,TITLE,ROOT
from paper_layout import journal_blocks,STYLE,CITATIONS,CITATION_PATTERN,citation_label
OUT=ROOT.parent/'output/pdf/jev_safe_visual_grounding_paper.pdf'
PAGE_WIDTH,PAGE_HEIGHT=210*mm,280*mm
LEFT,RIGHT=25.4*mm,23.6*mm
TOP,BOTTOM=18*mm,18*mm
TEXT_WIDTH=PAGE_WIDTH-LEFT-RIGHT
BLUE=colors.HexColor('#171669')
SHADE=colors.HexColor('#E8E7F0')
BODY_FONT,BOLD_FONT='Times-Roman','Times-Bold'
SANS_FONT,SANS_BOLD,SANS_BOLDITALIC='Helvetica','Helvetica-Bold','Helvetica-BoldOblique'
serif=Path('/System/Library/Fonts/Supplemental')
fontfiles={'PaperSerif':'Times New Roman.ttf','PaperSerifBold':'Times New Roman Bold.ttf','PaperSerifItalic':'Times New Roman Italic.ttf','PaperSerifBoldItalic':'Times New Roman Bold Italic.ttf','PaperSans':'Arial.ttf','PaperSansBold':'Arial Bold.ttf','PaperSansItalic':'Arial Italic.ttf','PaperSansBoldItalic':'Arial Bold Italic.ttf'}
if all((serif/f).exists() for f in fontfiles.values()):
 for name,filename in fontfiles.items():pdfmetrics.registerFont(TTFont(name,str(serif/filename)))
 pdfmetrics.registerFontFamily('PaperSerif',normal='PaperSerif',bold='PaperSerifBold',italic='PaperSerifItalic',boldItalic='PaperSerifBoldItalic')
 pdfmetrics.registerFontFamily('PaperSans',normal='PaperSans',bold='PaperSansBold',italic='PaperSansItalic',boldItalic='PaperSansBoldItalic')
 BODY_FONT,BOLD_FONT='PaperSerif','PaperSerifBold'
 SANS_FONT,SANS_BOLD,SANS_BOLDITALIC='PaperSans','PaperSansBold','PaperSansBoldItalic'
TOKENS={'E_real_fit':(r'$E_{\mathrm{real}}$','<i>E</i><sub>real</sub>'),'y_i':(r'$y_i$','<i>y</i><sub>i</sub>'),'a_i':(r'$a_i$','<i>a</i><sub>i</sub>'),'pi_correct':(r'$\widehat\pi_{\mathrm{correct}}$','<i>π</i><sub>correct</sub>'),'U_B':(r'$U_B$','<i>U</i><sub>B</sub>'),'U_D':(r'$U_D$','<i>U</i><sub>D</sub>'),'U_E':(r'$U_E$','<i>U</i><sub>E</sub>')}

def esc(t):
 return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(t))

def textext(t):
 # Replace citations before escaping underscores or optional locators.
 result=[];pos=0
 for match in re.finditer(CITATION_PATTERN,str(t)):
  result.append(esc(str(t)[pos:match.start()]))
  locator=match.group(2)
  result.append(r'\citep'+('['+esc(locator)+']' if locator else '')+'{ref'+match.group(1)+'}')
  pos=match.end()
 result.append(esc(str(t)[pos:]));s=''.join(result)
 for token,(latex,markup) in TOKENS.items():s=s.replace(esc(token),latex)
 return s

def widths(n):
 if n==3:return [.22,.56,.22]
 if n<=2:return [1/n]*n
 return [.22]+[.78/(n-1)]*(n-1)

def tex(doc):
 lines=[r'\documentclass[10pt]{article}',r'\usepackage{graphicx,booktabs,longtable,array,amsmath,microtype}',r'\usepackage{jev_journal}',r'\usepackage[round,authoryear]{natbib}',r'\usepackage{hyperref}',r'\hypersetup{colorlinks=true,linkcolor=journalblue,citecolor=journalblue,urlcolor=journalblue}',r'\renewcommand{\bibsection}{\section*{References}}',r'\setlength{\bibsep}{4pt}',r'\title{'+esc(TITLE)+r'}',r'\author{Anonymous Authors}',r'\date{}',r'\begin{document}',r'\maketitle\thispagestyle{plain}']
 references=False;i=0
 while i<len(doc):
  x=doc[i];k=x['kind']
  if k=='heading':
   if x['title']=='Abstract':
    i+=1;lines += [r'\begin{abstract}',textext(doc[i]['text']),r'\end{abstract}']
   elif x['title']=='References':
    lines.append(r'\begin{thebibliography}{99}');references=True
   else:
    if references:lines.append(r'\end{thebibliography}');references=False
    command='section' if x['level']==1 else 'subsection'
    lines.append('\\'+command+'*{'+esc(x['text'])+'}')
  elif k=='paragraph':lines.append(textext(x['text'])+'\n')
  elif k=='equation':
   expression=x['tex'] if len(x['lines'])==1 else r'\begin{gathered}'+r'\\[3pt]'.join(x['lines'])+r'\end{gathered}'
   lines += [r'\begin{equation}',expression,r'\label{eq:'+str(x['number'])+'}',r'\end{equation}']
  elif k=='page':
   if references:lines.append(r'\end{thebibliography}');references=False
   lines.append(r'\clearpage')
  elif k=='reference':
   author,year=CITATIONS[x['number']]
   lines.append(r'\bibitem['+esc(author)+'('+year+')]{ref'+x['number']+'} '+esc(x['display_text'])+r' \url{'+x['url']+'}')
  elif k=='figure':
   path='figures/extended/'+Path(x['path']).name
   lines += [r'\begin{figure}[htbp]',r'\centering',r'\includegraphics[width=\linewidth,height=3.9in,keepaspectratio]{'+path+r'}',r'\caption{'+textext(x['caption'])+r'}',r'\label{fig:'+str(x['number'])+'}',r'\end{figure}']
  elif k=='table':
   n=len(x['heads']);cols=''.join(r'>{\raggedright\arraybackslash}p{\dimexpr'+f'{w:.4f}'+r'\textwidth-2\tabcolsep\relax}' for w in widths(n))
   lines += [r'\begingroup\sffamily\fontsize{8}{9.5}\selectfont',r'\begin{longtable}{'+cols+r'}',r'\caption{'+textext(x['caption'])+r'}\label{tab:'+str(x['number'])+r'}\\',r'\toprule',' & '.join(r'\textbf{'+esc(h)+'}' for h in x['heads'])+r'\\\midrule',r'\endfirsthead',r'\multicolumn{'+str(n)+r'}{l}{\small Table \thetable. Continued}\\\toprule',' & '.join(r'\textbf{'+esc(h)+'}' for h in x['heads'])+r'\\\midrule',r'\endhead']
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
  nw,nh=w*72/250,h*72/250;scale=min(1,(TEXT_WIDTH-30)/nw,72/nh)
  self.iw,self.ih=nw*scale,nh*scale;self.width=TEXT_WIDTH;self.height=self.ih+14
 def draw(self):
  x,y=self.canv.absolutePosition((self.width-24-self.iw)/2,7)
  EQUATION_PLACEMENTS.append((self.canv.getPageNumber()-1,x,y,self.iw,self.ih,Path(self.path).with_suffix('.pdf')))
  self.canv.setFont(BODY_FONT,10.5);self.canv.drawRightString(self.width,(self.height-10)/2,'('+str(self.number)+')')

def running_header(c,d):
 c.saveState();c.setFillColor(colors.black);c.setFont(SANS_FONT,7.5)
 if d.page>1:
  c.drawString(LEFT,PAGE_HEIGHT-29,'WHEN NOT TO CLICK')
  c.drawRightString(PAGE_WIDTH-RIGHT,PAGE_HEIGHT-29,str(d.page))
 else:c.drawRightString(PAGE_WIDTH-RIGHT,29,str(d.page))
 c.restoreState()

def main():
 EQUATION_PLACEMENTS.clear()
 source=blocks();doc=journal_blocks(source);styles=getSampleStyleSheet()
 body=ParagraphStyle('JournalBody',parent=styles['BodyText'],fontName=BODY_FONT,fontSize=10.5,leading=12.5,firstLineIndent=12,alignment=TA_JUSTIFY,spaceAfter=0,allowWidows=0,allowOrphans=0,textColor=colors.black)
 first=ParagraphStyle('JournalFirstParagraph',parent=body,firstLineIndent=0)
 heading=ParagraphStyle('JournalHeading',parent=first,fontName=SANS_BOLD,fontSize=11,leading=13,alignment=TA_LEFT,textColor=BLUE,spaceBefore=16,spaceAfter=8,keepWithNext=True)
 subheading=ParagraphStyle('JournalSubheading',parent=heading,fontName=SANS_BOLDITALIC,fontSize=10.5,leading=12.5,spaceBefore=13,spaceAfter=7)
 abstract=ParagraphStyle('JournalAbstract',parent=first,fontName=SANS_FONT,fontSize=9,leading=10.5,alignment=TA_JUSTIFY)
 abstracthead=ParagraphStyle('JournalAbstractHead',parent=abstract,fontName=SANS_BOLD,fontSize=8,leading=10,textColor=BLUE,spaceAfter=3)
 small=ParagraphStyle('JournalSmall',parent=first,fontSize=9.5,leading=11,alignment=TA_LEFT,spaceAfter=5,leftIndent=12,firstLineIndent=-12)
 cell=ParagraphStyle('JournalCell',parent=first,fontName=SANS_FONT,fontSize=8,leading=9.5,alignment=TA_LEFT,spaceAfter=0)
 cellhead=ParagraphStyle('JournalCellHead',parent=cell,fontName=SANS_BOLD)
 title=ParagraphStyle('JournalTitle',parent=heading,fontSize=14,leading=17,spaceBefore=0,spaceAfter=8)
 author=ParagraphStyle('JournalAuthor',parent=first,fontName=SANS_FONT,fontSize=10.5,leading=12.5)
 caption=ParagraphStyle('JournalCaption',parent=cell,fontSize=9,leading=10.5,spaceAfter=7)
 header=ParagraphStyle('JournalFrontHeader',parent=cell,fontSize=7.5,leading=10)
 def xml(t):
  t=html.escape(str(t))
  for token,(latex,markup) in TOKENS.items():t=re.sub(r'\b'+re.escape(token)+r'\b',lambda m:markup,t)
  return re.sub(CITATION_PATTERN,lambda m:'<link href="#ref'+m[1]+'" color="#171669">'+citation_label(m[1],m[2])+'</link>',t)
 def P(t,style=body):return Paragraph(xml(t),style)
 from reportlab.platypus import HRFlowable
 story=[P('RESEARCH MANUSCRIPT',header),Spacer(1,5),HRFlowable(width=TEXT_WIDTH,thickness=.6,color=BLUE),Spacer(1,18),P(TITLE,title),P('Anonymous Authors',author),Spacer(1,15)]
 eqindex=0;i=0;after_heading=True
 while i<len(doc):
  x=doc[i];k=x['kind']
  if k=='heading':
   after_heading=True
   if x['title']=='Abstract':
    i+=1
    panel=Table([[Paragraph('ABSTRACT',abstracthead)],[P(doc[i]['text'],abstract)]],colWidths=[TEXT_WIDTH*.79],hAlign='LEFT')
    panel.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SHADE),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,0),10),('BOTTOMPADDING',(0,0),(-1,0),2),('TOPPADDING',(0,1),(-1,1),0),('BOTTOMPADDING',(0,1),(-1,1),11)]))
    story += [panel,Spacer(1,6)]
   else:story.append(P(x['text'],heading if x['level']==1 else subheading))
  elif k=='paragraph':
   story.append(P(x['text'],first if after_heading else body));after_heading=False
  elif k=='equation':
   story.append(NumberedEquation(ROOT/'results/extended/math'/f'equation_{eqindex}.png',x['number']));eqindex+=1
  elif k=='page':story.append(PageBreak());after_heading=True
  elif k=='reference':
   content='<a name="ref'+x['number']+'"/>'+html.escape(x['display_text'])+' <link href="'+html.escape(x['url'],quote=True)+'" color="#171669">'+html.escape(x['url'])+'</link>'
   story.append(Paragraph(content,small))
  elif k=='figure':
   path=ROOT/x['path']
   with PILImage.open(path) as im:w,h=im.size
   scale=min(TEXT_WIDTH/w,280/h)
   story.append(KeepTogether([Spacer(1,7),Image(str(path),width=w*scale,height=h*scale),Spacer(1,5),Paragraph('Figure '+str(x['number'])+'. '+xml(x['caption']),caption)]))
  elif k=='table':
   n=len(x['heads']);cap=Paragraph('Table '+str(x['number'])+'. '+xml(x['caption']),caption)
   data=[[cap]+['']*(n-1),[P(h.replace('Calibration-constant','Calibration constant'),cellhead) for h in x['heads']]]+[[P(v,cell) for v in row] for row in x['data']]
   table=LongTable(data,colWidths=[TEXT_WIDTH*f for f in widths(n)],repeatRows=2,hAlign='CENTER')
   table.setStyle(TableStyle([('SPAN',(0,0),(-1,0)),('NOSPLIT',(0,0),(-1,2)),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,1),(-1,1),.65,colors.black),('LINEBELOW',(0,1),(-1,1),.4,colors.black),('LINEBELOW',(0,-1),(-1,-1),.65,colors.black),('LEFTPADDING',(0,0),(-1,-1),3.5),('RIGHTPADDING',(0,0),(-1,-1),3.5),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),3.5),('LEFTPADDING',(0,0),(-1,0),0),('RIGHTPADDING',(0,0),(-1,0),0)]))
   gap=Spacer(1,6);gap.keepWithNext=True
   story += [gap,table,Spacer(1,8)]
  i+=1
 OUT.parent.mkdir(parents=True,exist_ok=True)
 output_doc=BaseDocTemplate(str(OUT),pagesize=(PAGE_WIDTH,PAGE_HEIGHT),leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,title=TITLE,author='Anonymous Authors')
 frame=Frame(output_doc.leftMargin,output_doc.bottomMargin,output_doc.width,output_doc.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='body')
 output_doc.addPageTemplates(PageTemplate(id='paper',frames=[frame],onPage=running_header));output_doc.build(story)
 # Preserve fine mathematical strokes as vector paths, including in small previews.
 reader=PdfReader(OUT);writer=PdfWriter()
 for page in reader.pages:writer.add_page(page)
 for page_index,x,y,iw,ih,equation_path in EQUATION_PLACEMENTS:
  equation=PdfReader(equation_path).pages[0]
  ew,eh=float(equation.mediabox.width),float(equation.mediabox.height)
  transform=Transformation().scale(iw/ew,ih/eh).translate(x,y)
  writer.pages[page_index].merge_transformed_page(equation,transform)
 writer.add_metadata({k:str(v) for k,v in reader.metadata.items() if v is not None})
 staged=OUT.with_suffix('.vector.pdf')
 with staged.open('wb') as stream:writer.write(stream)
 staged.replace(OUT)
 paper=ROOT.parent/'paper';figures=paper/'figures/extended';figures.mkdir(parents=True,exist_ok=True)
 for x in doc:
  if x['kind']=='figure':shutil.copy2(ROOT/x['path'],figures/Path(x['path']).name)
 (paper/'jev_journal.sty').write_text(STYLE)
 source_tex=tex(doc);(paper/'main.tex').write_text(source_tex);(ROOT/'reports/submission_manuscript.tex').write_text(source_tex)
 (ROOT/'reports/manuscript_content.json').write_text(json.dumps(doc,indent=2)+'\n')
 for kind,key in [('table','data'),('equation','tex'),('figure','path')]:
  assert [x[key] for x in source if x['kind']==kind]==[x[key] for x in doc if x['kind']==kind],kind
 assert {x['url'] for x in source if x['kind']=='reference'}=={x['url'] for x in doc if x['kind']=='reference'}
 print(OUT)
if __name__=='__main__':main()
