from pathlib import Path
from copy import deepcopy
import re,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/gaurangbhatia/Downloads/When_Not_to_Click_TF.docx')
d=Document(SOURCE)
BLUE='191877';GRAY='E9E9F1';WIDTH=6.67

def font(run,name,size,color='000000'):
    run.font.name=name;run.font.size=Pt(size);run.font.color.rgb=RGBColor.from_string(color)
    rf=run._element.get_or_add_rPr().get_or_add_rFonts()
    for a in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+a),name)

def remove(el):
    if el.getparent() is not None:el.getparent().remove(el)

def add_after(p,text,style='Body Text'):
    x=OxmlElement('w:p');p._p.addnext(x);q=Paragraph(x,p._parent);q.style=style;q.add_run(text);return q

for p in list(d.paragraphs):
    if p.text.startswith('Old → new numbering:'):remove(p._p)
    elif not p.text.strip() and not p._p.xpath('.//w:drawing | .//m:oMath | .//m:oMathPara'):remove(p._p)
    elif 'Restructured from long to wide format; values unchanged.' in p.text:
        for r in p.runs:r.text=r.text.replace(' Restructured from long to wide format; values unchanged.','')

author=next(p for p in d.paragraphs if p.style.name=='Author')
author.text='Sowmya K S, Garvit Mundra, and Gaurang Bhatia'
q=add_after(author,'B.M.S. College of Engineering', 'Author')
q=add_after(q,'Sowmya K S: sowmyaks.ise@bmsce.ac.in', 'Author')
q=add_after(q,'Garvit Mundra: garvitmundra.cs24@bmsce.ac.in', 'Author')
q=add_after(q,'Gaurang Bhatia: gaurang.cs24@bmsce.ac.in', 'Author')
abstract=next(p for p in d.paragraphs if p.style.name=='Abstract')
keywords=add_after(abstract,'Keywords: GUI grounding; selective prediction; uncertainty calibration; distribution shift; visual agents; abstention')
for p in d.paragraphs:
    if p.text.startswith('CRediT: [AUTHOR 1]'):
        p.text='CRediT: Sowmya K S: [ROLES TO BE CONFIRMED]; Garvit Mundra: [ROLES TO BE CONFIRMED]; Gaurang Bhatia: [ROLES TO BE CONFIRMED].'

sec=d.sections[0]
sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
sec.top_margin=Inches(.72);sec.bottom_margin=Inches(.72)
sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
sec.header_distance=Inches(.3);sec.footer_distance=Inches(.32)
for style in d.styles:
    if style.type==1:
        style.font.name='Times New Roman';style.font.size=Pt(10.5)
        style.font.color.rgb=RGBColor(0,0,0)
        pf=style.paragraph_format;pf.space_before=Pt(0);pf.space_after=Pt(5)
        pf.line_spacing=Pt(13);pf.keep_with_next=False;pf.widow_control=True
        pf.page_break_before=False

refs=False
for p in d.paragraphs:
    pf=p.paragraph_format
    pf.space_before=Pt(0);pf.space_after=Pt(5);pf.line_spacing=Pt(13)
    pf.keep_with_next=False;pf.keep_together=False;pf.widow_control=True;pf.page_break_before=False
    pf.left_indent=Pt(0);pf.right_indent=Pt(0);pf.first_line_indent=Pt(0)
    pp=p._p.get_or_add_pPr()
    for tag in ['w:pBdr','w:shd','w:tabs']:
        for x in pp.findall(qn(tag)):remove(x)
    p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for r in p.runs:font(r,'Times New Roman',10.5)
    st=p.style.name;t=p.text.strip()
    if st=='Title':
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.space_after=Pt(9);pf.line_spacing=Pt(19);pf.keep_with_next=True
        for r in p.runs:font(r,'Arial',16,BLUE);r.bold=True
    elif st=='Author':
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.space_after=Pt(2);pf.line_spacing=Pt(11);pf.keep_with_next=True
        sz=10.5 if p is author else 9
        if p._p is author._p:sz=10.5
        for r in p.runs:font(r,'Arial',sz);r.bold=False
        if t.startswith('Gaurang Bhatia:'):pf.space_after=Pt(9)
    elif st in ['Abstract','AbstractHead']:
        sh=OxmlElement('w:shd');sh.set(qn('w:fill'),GRAY);pp.append(sh)
        pf.left_indent=Inches(.12);pf.right_indent=Inches(.12)
        pf.space_before=Pt(6 if st=='AbstractHead' else 0);pf.space_after=Pt(6 if st=='Abstract' else 2)
        pf.line_spacing=Pt(11.7);pf.keep_with_next=st=='AbstractHead';pf.keep_together=True
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:font(r,'Arial',9.4,BLUE if st=='AbstractHead' else '000000');r.bold=st=='AbstractHead'
    elif st.startswith('Heading'):
        level=int(st.split()[-1]);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        pf.space_before=Pt(12 if level==2 else 9);pf.space_after=Pt(5);pf.line_spacing=Pt(14);pf.keep_with_next=True;pf.keep_together=True
        for r in p.runs:font(r,'Arial',11.5 if level==2 else 10.5,BLUE);r.bold=True;r.italic=level>=3
        if t=='References':refs=True;pf.page_break_before=False
        elif t=='Appendices':refs=False;pf.page_break_before=True
    elif re.match(r'^(Table|Figure)\s+[A-D]?\d',t):
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.line_spacing=Pt(11.3);pf.space_before=Pt(7);pf.space_after=Pt(4);pf.keep_together=True
        pf.keep_with_next=t.startswith('Table')
        for r in p.runs:font(r,'Arial',9)
    elif t.startswith('Keywords:'):
        pf.space_before=Pt(5);pf.space_after=Pt(9);pf.line_spacing=Pt(12);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:font(r,'Times New Roman',9.5)
    elif p._p.xpath('.//w:drawing'):
        pf.line_spacing=1.0
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.space_before=Pt(6);pf.space_after=Pt(0);pf.keep_with_next=True;pf.keep_together=True
    elif p._p.xpath('./m:oMathPara'):
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER;pf.space_before=Pt(6);pf.space_after=Pt(7);pf.line_spacing=1.0;pf.keep_together=True
    elif st=='Compact':
        pf.left_indent=Inches(.18);pf.first_line_indent=Inches(-.12);pf.space_after=Pt(3);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    elif refs:
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.line_spacing=Pt(11.3);pf.space_after=Pt(5);pf.keep_together=True
        pf.left_indent=Inches(.16);pf.first_line_indent=Inches(-.16)
        for r in p.runs:font(r,'Times New Roman',9)

widths={
'1':[.22,.56,.22],'2':[.25,.125,.125,.125,.125,.125,.125],
'3':[.14,.14,.14,.17,.16,.25], '4':[.08,.29,.31,.32], '5':[.42,.29,.29],
'6':[.18,.42,.20,.20],'7':[.20,.11,.14,.13,.10,.10,.22],
'A1':[.17,.17,.17,.17,.32],'A2':[.18,.15,.17,.17,.17,.16],
'A3':[.27,.10,.10,.13,.12,.14,.14],'A4':[.23,.14,.10,.13,.12,.14,.14],
'A5':[.25,.10,.10,.14,.13,.14,.14],'A6':[.20,.11,.10,.15,.13,.155,.155],
'A7':[.31,.08,.09,.13,.11,.14,.14],'A8':[.28,.09,.09,.13,.12,.145,.145],
'A9':[.21,.11,.10,.15,.13,.15,.15],
'C1':[.25,.12,.12,.17,.17,.17],'C2':[.20,.11,.25,.15,.15,.14],
'C3':[.19,.12,.12,.20,.13,.24],'C4':[.17,.415,.415],
'C5':[.20,.29,.24,.27],'C6':[.17,.28,.28,.27],
'C7':[.11,.10,.18,.18,.18,.25],'C8':[.23,.12,.19,.23,.23],
'D1':[.25,.31,.23,.21]}
tableinfo=[]
for table in d.tables:
    prev=table._tbl.getprevious()
    while prev is not None and not ''.join(prev.itertext()).strip():prev=prev.getprevious()
    cap=''.join(prev.xpath('.//w:t/text()')) if prev is not None else ''
    m=re.search(r'Table ([A-D]?\d+)\.',cap);num=m.group(1) if m else '?'
    n=len(table.columns);ws=widths.get(num,[1/n]*n);total=sum(ws);ws=[x/total for x in ws]
    tableinfo.append({'number':num,'rows':len(table.rows),'columns':n})
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    pr=table._tbl.tblPr
    for x in pr.findall(qn('w:tblBorders')):remove(x)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','bottom','left','right','insideH','insideV']:
        el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single' if edge in ['top','bottom'] else 'nil');el.set(qn('w:sz'),'5');el.set(qn('w:color'),'999999');borders.append(el)
    pr.append(borders)
    for j,col in enumerate(table.columns):col.width=Inches(WIDTH*ws[j])
    for i,row in enumerate(table.rows):
        trpr=row._tr.get_or_add_trPr()
        for x in trpr.findall(qn('w:trHeight')):remove(x)
        if trpr.find(qn('w:cantSplit')) is None:trpr.append(OxmlElement('w:cantSplit'))
        if i==0 and trpr.find(qn('w:tblHeader')) is None:trpr.append(OxmlElement('w:tblHeader'))
        for j,cell in enumerate(row.cells):
            cell.width=Inches(WIDTH*ws[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tc=cell._tc.get_or_add_tcPr()
            for tag in ['w:tcMar','w:shd','w:tcBorders']:
                for x in tc.findall(qn(tag)):remove(x)
            mar=OxmlElement('w:tcMar')
            for side,val in [('top',55),('bottom',55),('left',65),('right',65)]:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),str(val));el.set(qn('w:type'),'dxa');mar.append(el)
            tc.append(mar)
            if i==0:
                b=OxmlElement('w:tcBorders');e=OxmlElement('w:bottom');e.set(qn('w:val'),'single');e.set(qn('w:sz'),'5');e.set(qn('w:color'),'999999');b.append(e);tc.append(b)
            for p in cell.paragraphs:
                pf=p.paragraph_format;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.line_spacing=Pt(10.7)
                pf.left_indent=Pt(0);pf.right_indent=Pt(0);pf.first_line_indent=Pt(0);pf.keep_together=True
                pf.keep_with_next=(i<len(table.rows)-1) if len(table.rows)<=9 else (i==0 or i==len(table.rows)-2)
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 or num in ['1','6','7','D1'] else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:font(r,'Arial',8.7);r.bold=i==0

for shape in d.inline_shapes:
    scale=min(Inches(WIDTH)/shape.width,Inches(5.0)/shape.height)
    shape.width=int(shape.width*scale);shape.height=int(shape.height*scale)

for part in [sec.header,sec.footer]:
    for p in part.paragraphs:p.clear()
hp=sec.header.paragraphs[0];hp.text='WHEN NOT TO CLICK';hp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
for r in hp.runs:font(r,'Arial',7.5,'666666')
fp=sec.footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');fp._p.append(fld)
sec.different_first_page_header_footer=True
fp=sec.first_page_footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');fp._p.append(fld)
# Preserve native Office Math while making formula size consistent.
for r in d.element.xpath('.//m:r'):
    rp=r.find(qn('w:rPr'))
    if rp is None:rp=OxmlElement('w:rPr');r.insert(0,rp)
    for x in rp.findall(qn('w:sz')):remove(x)
    sz=OxmlElement('w:sz');sz.set(qn('w:val'),'21');rp.append(sz)
replacement=ROOT/'tmp/figure7.png'
if replacement.exists():
    shape=d.inline_shapes[6]
    rid=shape._inline.xpath('.//a:blip')[0].get(qn('r:embed'))
    d.part.related_parts[rid]._blob=replacement.read_bytes()
    shape.width=Inches(WIDTH);shape.height=Inches(WIDTH*800/1600)
d.save(ROOT/'When_Not_to_Click_Formatted.docx')
(ROOT/'tmp/table_inventory.json').write_text(json.dumps(tableinfo,indent=2))
print('Saved',len(d.tables),'tables;',len(d.inline_shapes),'figures')
