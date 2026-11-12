from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from difflib import SequenceMatcher
from collections import Counter
from lxml import etree as E
import json,re,subprocess

ROOT=Path(__file__).parent
SOURCE=ROOT/'When_Not_to_Click_TFf_Formatted.docx'
OUTPUT=ROOT/'When_Not_to_Click_TFf_Prose_Revised.docx'
ORIGINAL=Path('/Users/gaurangbhatia/Downloads/When_Not_to_Click_TFf.docx')
PY='/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
NODE='/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
SKILLS=Path('/Users/gaurangbhatia/.codex/skills')
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def text(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def numbers(s):return Counter(re.findall(r'\d+(?:[.,]\d+)*',s))
def serialize(r,x):return [E.tostring(n) for n in r.xpath(x,namespaces=NS)]

rewrites=json.loads((ROOT/'prose_rewrite.json').read_text())
rewrites['355']=rewrites['355'].replace('For multiple targets, moving from B to D reduces acceptance by −50 percentage points','For multiple targets, the difference from B to D is −50 percentage points')
(ROOT/'prose_rewrite.json').write_text(json.dumps(rewrites,ensure_ascii=False,indent=2))
op={int(line.split(': ',1)[0]):line.split(': ',1)[1] for line in (ROOT/'prose_indexed.txt').read_text().splitlines()}
prior={x['paragraph']:x['after'] for x in json.loads((ROOT/'edit_log.json').read_text())}
with ZipFile(SOURCE) as zin:
    original=E.fromstring(zin.read('word/document.xml'));root=deepcopy(original)
    allps=root.xpath('//w:p',namespaces=NS)
    targets=[]
    for id,new in rewrites.items():
        id=int(id);old=prior.get(id,op[id])
        ps=[p for p in allps if text(p)==old]
        assert len(ps)==1,(id,len(ps))
        p=ps[0]
        assert not p.xpath('ancestor::w:tbl | .//m:oMath | .//w:hyperlink',namespaces=NS),id
        assert numbers(old)==numbers(new),(id,numbers(old)-numbers(new),numbers(new)-numbers(old))
        # Inline author-year citations and URLs are retained as supplied.
        citations=re.findall(r'\([^()]*\b(?:19|20)\d{2}[a-z]?[^()]*\)',old)
        for cite in citations:assert cite in new,(id,cite)
        targets.append((id,p,old,new))
    (ROOT/'narrative_before.txt').write_text('\n\n'.join(x[2] for x in targets))
    (ROOT/'narrative_after.txt').write_text('\n\n'.join(x[3] for x in targets))
    for name in ['narrative_before','narrative_after']:
        subprocess.run([PY,str(SKILLS/'clean-user-facing-text/scripts/inspect_text.py'),'--stylometry','--json',str(ROOT/f'{name}.txt')],stdout=open(ROOT/f'{name}.score.json','w'),check=False)
        subprocess.run([PY,str(SKILLS/'clean-user-facing-text/scripts/clean_text.py'),str(ROOT/f'{name}.txt'),'-o',str(ROOT/f'{name}.cleaned.txt'),'--no-normalize-spaces','--stats'],check=True)
        assert (ROOT/f'{name}.txt').read_text()==(ROOT/f'{name}.cleaned.txt').read_text()
    subprocess.run([NODE,str(SKILLS/'avoid-ai-writing/scripts/normalize-quotes.js'),str(ROOT/'narrative_after.txt'),'--reference',str(ROOT/'narrative_before.txt'),'--write'],check=True)
    normalized=(ROOT/'narrative_after.txt').read_text().split('\n\n')
    assert len(normalized)==len(targets)
    changes=[]
    for (id,p,old,_),new in zip(targets,normalized):
        nodes=p.xpath('.//w:t',namespaces=NS)
        starts=[];pos=0
        for n in nodes:starts.append(pos);pos+=len(n.text or '')
        for typ,a,b,c,d in reversed(SequenceMatcher(None,old,new,autojunk=False).get_opcodes()):
            if typ=='equal':continue
            left=max(j for j,s in enumerate(starts) if s<=a)
            right=max(j for j,s in enumerate(starts) if s<b) if b>a else left
            lpos=a-starts[left];rpos=b-starts[right]
            if left==right:
                s=nodes[left].text or '';nodes[left].text=s[:lpos]+new[c:d]+s[rpos:]
            else:
                nodes[left].text=(nodes[left].text or '')[:lpos]+new[c:d]
                for j in range(left+1,right):nodes[j].text=''
                nodes[right].text=(nodes[right].text or '')[rpos:]
        assert text(p)==new,id
        for n in nodes:
            if n.text and (n.text[0].isspace() or n.text[-1].isspace()):n.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        changes.append({'original_paragraph':id,'before':old,'after':new})
    for xp in ['//m:oMath','//w:tbl','//w:drawing','//w:hyperlink','//w:pPr','//w:rPr']:
        assert serialize(original,xp)==serialize(root,xp),xp
    changedids={p for _,p,_,_ in targets}
    for a,b in zip(original.xpath('//w:p',namespaces=NS),allps):
        if b not in changedids:assert E.tostring(a)==E.tostring(b)
    with ZipFile(OUTPUT,'w') as zout:
        for info in zin.infolist():
            data=zin.read(info.filename)
            if info.filename=='word/document.xml':data=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
            zout.writestr(info,data)
    (ROOT/'narrative_edit_log.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
    (ROOT/'narrative_final.txt').write_text('\n'.join(text(p) for p in allps))
    report={'rewritten_paragraphs':len(targets),'editing_passes':1,'editable_math_objects_unchanged':len(root.xpath('//m:oMath',namespaces=NS)),'all_tables_unchanged':True,'all_numerical_values_preserved':True,'all_paragraph_and_run_formatting_preserved':True,'all_other_package_parts_unchanged':True,'authorship_or_detector_claim':None,'output':str(OUTPUT)}
    (ROOT/'narrative_preservation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
