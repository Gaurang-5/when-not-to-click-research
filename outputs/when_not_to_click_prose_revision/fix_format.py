from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import json

ROOT=Path(__file__).parent
SOURCE=ROOT/'When_Not_to_Click_TFf_Revised.docx'
OUTPUT=ROOT/'When_Not_to_Click_TFf_Formatted.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M='http://schemas.openxmlformats.org/officeDocument/2006/math'
NS={'w':W,'m':M}
def tag(name):
    prefix,local=name.split(':');return '{'+NS[prefix]+'}'+local
def el(name,**attrs):
    node=E.Element(tag(name))
    for k,v in attrs.items():node.set(tag(name.split(':')[0]+':'+k),str(v))
    return node
def ensure(parent,name,**attrs):
    node=parent.find(tag(name))
    if node is None:
        node=el(name);parent.append(node)
    for k,v in attrs.items():node.set(tag(name.split(':')[0]+':'+k),str(v))
    return node
def ppr(p):
    node=p.find(tag('w:pPr'))
    if node is None:node=el('w:pPr');p.insert(0,node)
    return node
def txt(node):return ''.join(node.xpath('.//w:t/text()',namespaces=NS))
def signature(n):return (n.tag, sorted(n.attrib.items()), n.text, n.tail, tuple(signature(c) for c in n))
def mathxml(root):return [E.tostring(x) for x in root.xpath('//m:oMath',namespaces=NS)]

with ZipFile(SOURCE) as zin:
    original=E.fromstring(zin.read('word/document.xml'))
    root=deepcopy(original)
    data_tables=root.xpath('//w:tbl',namespaces=NS)
    text_before=root.xpath('//w:t/text()',namespaces=NS)
    original_math=mathxml(root)
    width=9317
    # Use the available page width, giving descriptive columns more room.
    ratios={
      0:[29,48,23],1:[25,12,12,13,13,13,12],2:[20,15,12,16,15,22],
      3:[10,28,31,31],4:[40,30,30],5:[23,37,20,20],
      6:[21,11,14,13,12,12,17],7:[20,18,18,18,26],8:[20,16,17,14,17,16],
      16:[29,12,12,17,14,16],17:[22,12,24,15,12,15],
      18:[22,12,13,18,14,21],19:[16,42,42],20:[16,29,27,28],
      21:[18,28,28,26],22:[14,11,21,18,16,20],23:[24,13,20,21,22],24:[25,27,23,25]
    }
    for i,t in enumerate(data_tables):
        pr=t.find(tag('w:tblPr'))
        ensure(pr,'w:tblW',type='dxa',w=width)
        ensure(pr,'w:jc',val='center')
        ensure(pr,'w:tblLayout',type='fixed')
        ensure(pr,'w:tblInd',type='dxa',w=0)
        mar=ensure(pr,'w:tblCellMar')
        for side in ['left','right']:ensure(mar,'w:'+side,type='dxa',w=95)
        for side in ['top','bottom']:ensure(mar,'w:'+side,type='dxa',w=65)
        grid=t.find(tag('w:tblGrid')); cols=grid.findall(tag('w:gridCol'))
        weights=ratios.get(i,[32,11,9,13,10,13,12])
        assert len(weights)==len(cols),(i,len(weights),len(cols))
        widths=[round(width*x/sum(weights)) for x in weights]
        widths[-1]+=width-sum(widths)
        for c,ww in zip(cols,widths):c.set(tag('w:w'),str(ww))
        for ri,row in enumerate(t.findall(tag('w:tr'))):
            rp=ensure(row,'w:trPr');ensure(rp,'w:cantSplit')
            if ri==0:ensure(rp,'w:tblHeader')
            for ci,cell in enumerate(row.findall(tag('w:tc'))):
                cp=ensure(cell,'w:tcPr')
                ensure(cp,'w:tcW',type='dxa',w=widths[ci])
                ensure(cp,'w:vAlign',val='center')
                for p in cell.findall(tag('w:p')):
                    pp=ppr(p)
                    ensure(pp,'w:jc',val='left' if ci==0 or i in [0,24] or (i==5 and ci==1) else 'center')
                    ensure(pp,'w:spacing',before=0,after=0,line=240,lineRule='auto')
                    ensure(pp,'w:ind',left=0,right=0,firstLine=0)
                    ensure(pp,'w:keepLines')
                    ensure(pp,'w:keepNext',val=1 if ri==0 else 0)
                    for r in p.findall(tag('w:r')):
                        rr=r.find(tag('w:rPr'))
                        if rr is None:rr=el('w:rPr');r.insert(0,rr)
                        ensure(rr,'w:sz',val=20)
                        if ri==0:ensure(rr,'w:b')
        # Caption belongs to the header and at least the first data row.
        prev=t.getprevious()
        if prev is not None and prev.tag==tag('w:p'):
            ensure(ppr(prev),'w:keepNext')
    equation_count=0
    formula_checks=[]
    for p in list(root.xpath('//w:p[m:oMathPara]',namespaces=NS)):
        mp=p.find(tag('m:oMathPara'));math=mp.find(tag('m:oMath'))
        formula_before=deepcopy(math)
        label=math[-1]
        assert label.tag==tag('m:d')
        number=''.join(label.xpath('.//m:t/text()',namespaces=NS))
        assert number in ['1','2','3','4','5','6a','6b','6c','7a','7b','8','9','10','11','C1','C2']
        math.remove(label)
        assert ''.join(math[-1].itertext()).isspace()
        spacer=math[-1];math.remove(spacer)
        expected=deepcopy(formula_before);expected.remove(expected[-1]);expected.remove(expected[-1])
        assert signature(expected)==signature(math)
        formula_checks.append(number)
        # Symmetric side cells keep the formula centered independently of its number.
        table=el('w:tbl');pr=el('w:tblPr');table.append(pr)
        pr.append(el('w:tblW',type='dxa',w=width));pr.append(el('w:jc',val='center'))
        pr.append(el('w:tblLayout',type='fixed'))
        borders=el('w:tblBorders');pr.append(borders)
        for side in ['top','left','bottom','right','insideH','insideV']:borders.append(el('w:'+side,val='nil'))
        mar=el('w:tblCellMar');pr.append(mar)
        for side in ['top','bottom','left','right']:mar.append(el('w:'+side,type='dxa',w=0))
        widths=[750,width-1500,750]
        grid=el('w:tblGrid');table.append(grid)
        for ww in widths:grid.append(el('w:gridCol',w=ww))
        row=el('w:tr');table.append(row);rp=el('w:trPr');row.append(rp);rp.append(el('w:cantSplit'))
        for ci,ww in enumerate(widths):
            cell=el('w:tc');row.append(cell);cp=el('w:tcPr');cell.append(cp)
            cp.append(el('w:tcW',type='dxa',w=ww));cp.append(el('w:vAlign',val='center'))
            ppnode=el('w:p');cell.append(ppnode);pp=ppr(ppnode)
            pp.append(el('w:jc',val='right' if ci==2 else 'center'))
            pp.append(el('w:ind',left=0,right=0,firstLine=0))
            pp.append(el('w:spacing',before=100,after=100,line=240,lineRule='auto'))
            pp.append(el('w:keepLines'))
            if ci==1:
                mp.remove(math)
                newmp=el('m:oMathPara');mpr=el('m:oMathParaPr');mpr.append(el('m:jc',val='center'))
                newmp.append(mpr);newmp.append(math);ppnode.append(newmp)
            elif ci==2:
                r=el('w:r');ppnode.append(r);rr=el('w:rPr');r.append(rr)
                rr.append(el('w:rFonts',ascii='Times New Roman',hAnsi='Times New Roman'))
                rr.append(el('w:sz',val=21));tt=el('w:t');tt.text='('+number+')';r.append(tt)
        prev=p.getprevious()
        if prev is not None and prev.tag==tag('w:p'):
            ensure(ppr(prev),'w:keepNext')
        p.getparent().replace(p,table)
        equation_count+=1
    # Keep headings and captions with their associated content, and images with captions.
    in_references=False
    for p in root.xpath('//w:body/w:p',namespaces=NS):
        pp=ppr(p);style=pp.find(tag('w:pStyle'))
        sid=style.get(tag('w:val')) if style is not None else ''
        t=txt(p)
        if t=='References':in_references=True
        elif t=='Appendices':in_references=False
        elif in_references:
            ensure(pp,'w:jc',val='left')
            ensure(pp,'w:keepLines')
        if t.startswith('Table '):
            ensure(pp,'w:spacing',before=140,after=80)
        if t.startswith('Native uniqueness and presence signals substantially improve'):
            ensure(pp,'w:keepLines')
        if sid.startswith('Heading') or t.startswith('Table ') or p.xpath('.//w:drawing',namespaces=NS):ensure(pp,'w:keepNext')
        ensure(pp,'w:widowControl')
        if t.startswith('Figure '):
            ensure(pp,'w:keepLines')
            ensure(pp,'w:spacing',before=80,after=120)
    # Assert that every prose string and every data-table cell value survives exactly.
    added_numbers={'('+s+')' for s in formula_checks}
    new_text=[s for s in root.xpath('//w:t/text()',namespaces=NS) if s not in added_numbers]
    assert text_before==new_text
    for before,after in zip(original.xpath('//w:tbl',namespaces=NS),data_tables):
        assert before.xpath('.//w:t/text()',namespaces=NS)==after.xpath('.//w:t/text()',namespaces=NS)
    assert len(root.xpath('//m:oMath',namespaces=NS))==len(original_math)
    for xp in ['//w:drawing','//w:hyperlink']:
        assert [E.tostring(x) for x in original.xpath(xp,namespaces=NS)]==[E.tostring(x) for x in root.xpath(xp,namespaces=NS)]
    with ZipFile(OUTPUT,'w') as out:
        for info in zin.infolist():
            data=zin.read(info.filename)
            if info.filename=='word/document.xml':data=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
            out.writestr(info,data)
    report={'display_equations_centered':equation_count,'equation_numbers_separated':formula_checks,'formula_content_preserved':True,'all_prose_preserved':True,'data_tables_reformatted':len(data_tables),'data_table_values_preserved':True,'output':str(OUTPUT)}
    (ROOT/'format_preservation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
