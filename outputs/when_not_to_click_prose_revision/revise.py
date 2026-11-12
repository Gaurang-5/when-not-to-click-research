from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from difflib import SequenceMatcher
from copy import deepcopy
import json, re, subprocess

ROOT = Path(__file__).parent
SOURCE = Path('/Users/gaurangbhatia/Downloads/When_Not_to_Click_TFf.docx')
OUTPUT = ROOT / 'When_Not_to_Click_TFf_Revised.docx'
PY = '/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
NODE = '/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
SKILLS = Path('/Users/gaurangbhatia/.codex/skills')
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main', 'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
edits = {
 7: [('returns three things in a single request', 'returns three outputs per request')],
 13: [('The structure of the paper is as follows. ', '')],
 17: [('Published VLM performance is given as context in Appendix D rather than treated as an experiment on our labels.', 'Appendix D gives published VLM performance as context rather than as an experiment on our labels.')],
 190: [('These repetitions diagnose prediction stability; they do not multiply the number of independent source images.', 'These repetitions assess prediction stability; they do not increase the number of independent source images.')],
 202: [('it additionally requires', 'it also requires')],
 247: [('These interface and deployment choices delimit the comparison.', 'The comparison is limited to these interface and deployment choices.')],
 286: [('The present work supplies no formal risk control under distribution shift.', 'This study provides no formal risk control under distribution shift.')],
 950: [('It adds explicit diagnosis of the base grounder, the gate and annotation sensitivity.', 'It examines the base grounder, the gate and sensitivity to annotation.')],
 1236: [('The local compute and energy price is unmeasured, so API charge and total economic cost are not equated.', 'Local compute and energy costs are unmeasured, so the API charge is not treated as the total economic cost.')],
}

def text(p): return ''.join(p.xpath('.//w:t/text()', namespaces=NS))
with ZipFile(SOURCE) as z:
    original = E.fromstring(z.read('word/document.xml'))
    root = deepcopy(original)
    ps = root.xpath('//w:p', namespaces=NS)
    before, after, audit = [], [], []
    for i, changes in edits.items():
        p = ps[i]
        assert not p.xpath('ancestor::w:tbl', namespaces=NS)
        old = text(p)
        new = old
        for a, b in changes:
            assert new.count(a) == 1, (i, a)
            new = new.replace(a,b)
        before.append(old)
        after.append(new)
        audit.append({'paragraph':i, 'before':old, 'after':new})
    (ROOT/'edited_before.txt').write_text('\n\n'.join(before))
    (ROOT/'edited_after.txt').write_text('\n\n'.join(after))
    # Hygiene and quote checks operate only on editable prose, never the DOCX container.
    for name in ['edited_before', 'edited_after']:
        subprocess.run([PY, str(SKILLS/'clean-user-facing-text/scripts/clean_text.py'), str(ROOT/f'{name}.txt'), '-o', str(ROOT/f'{name}.cleaned.txt'), '--no-normalize-spaces', '--stats'], check=True)
        assert (ROOT/f'{name}.txt').read_text() == (ROOT/f'{name}.cleaned.txt').read_text()
    subprocess.run([NODE, str(SKILLS/'avoid-ai-writing/scripts/normalize-quotes.js'), str(ROOT/'edited_after.txt'), '--reference', str(ROOT/'edited_before.txt'), '--write'], check=True)
    normalized = (ROOT/'edited_after.txt').read_text().split('\n\n')
    assert normalized == after
    for (i,_), old, new in zip(edits.items(), before, after):
        nodes = ps[i].xpath('.//w:t', namespaces=NS)
        starts, pos = [], 0
        for node in nodes:
            starts.append(pos)
            pos += len(node.text or '')
        # Apply character edits backwards so run formatting and nontext XML survive.
        for op, a, b, c, d in reversed(SequenceMatcher(None, old, new, autojunk=False).get_opcodes()):
            if op == 'equal': continue
            left = max(j for j,s in enumerate(starts) if s <= a)
            right = max(j for j,s in enumerate(starts) if s < b) if b > a else left
            lpos, rpos = a-starts[left], b-starts[right]
            if left == right:
                t = nodes[left].text or ''
                nodes[left].text = t[:lpos] + new[c:d] + t[rpos:]
            else:
                nodes[left].text = (nodes[left].text or '')[:lpos]+new[c:d]
                for j in range(left+1,right): nodes[j].text = ''
                nodes[right].text = (nodes[right].text or '')[rpos:]
        assert text(ps[i]) == new
        for node in nodes:
            if node.text and (node.text[0].isspace() or node.text[-1].isspace()):
                node.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    original_ps = original.xpath('//w:p', namespaces=NS)
    assert len(original_ps) == len(ps)
    for i,(a,b) in enumerate(zip(original_ps,ps)):
        if i not in edits: assert E.tostring(a) == E.tostring(b)
    def serials(tree,xpath): return [E.tostring(x) for x in tree.xpath(xpath,namespaces=NS)]
    for xp in ['//m:oMath','//w:tbl','//w:drawing','//w:pPr','//w:rPr','//w:hyperlink']:
        assert serials(original,xp) == serials(root,xp), xp
    old_text = '\n'.join(map(text,original_ps))
    new_text = '\n'.join(map(text,ps))
    assert re.findall(r'\d+(?:[.,]\d+)*',old_text) == re.findall(r'\d+(?:[.,]\d+)*',new_text)
    # Every package member other than the main document is copied byte for byte.
    with ZipFile(OUTPUT,'w') as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == 'word/document.xml':
                data = E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
            out.writestr(info,data)
    (ROOT/'after.txt').write_text(new_text)
    (ROOT/'prose_after.txt').write_text('\n'.join(text(p) for p in ps if not p.xpath('ancestor::w:tbl',namespaces=NS) and text(p)))
    (ROOT/'edit_log.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    report = {'edited_paragraphs':len(edits), 'editing_passes':1,'math_objects_unchanged':len(original.xpath('//m:oMath',namespaces=NS)), 'tables_unchanged':len(original.xpath('//w:tbl',namespaces=NS)), 'drawings_unchanged':len(original.xpath('//w:drawing',namespaces=NS)), 'all_numeric_tokens_unchanged':True,'all_other_package_parts_unchanged':True,'original_preserved':str(SOURCE), 'output':str(OUTPUT)}
    (ROOT/'preservation_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
