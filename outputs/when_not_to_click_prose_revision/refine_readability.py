from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
from collections import Counter
from difflib import SequenceMatcher
import json,re,subprocess
R=Path(__file__).parent
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
PY='/Users/gaurangbhatia/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
S=Path('/Users/gaurangbhatia/.codex/skills/clean-user-facing-text/scripts')
def txt(p):return ''.join(p.xpath('.//w:t/text()',namespaces=ns))
with ZipFile(R/'When_Not_to_Click_TFf_Prose_Revised.docx') as z:
 original=E.fromstring(z.read('word/document.xml'));root=deepcopy(original);ps=root.xpath('//w:p',namespaces=ns)
 edits={
4:txt(ps[4]).replace('A graphical user interface (GUI) agent needs to establish that a requested control is present and uniquely identified before deciding where to click.', 'Before a graphical user interface (GUI) agent clicks, it must check that the requested control is present. It must also identify that control uniquely.').replace('We examine the native scores returned by a pinned visual interface, Jev 1.14: a visible-presence probability, a match-count distribution and one bounding box per request. These scores form the basis of frozen selective-execution policies.', 'We test frozen selective-execution policies using the native outputs of a pinned visual interface, Jev 1.14. For each request, it returns a visible-presence probability, a match-count distribution and one bounding box.').replace('We contribute a reproducible audit of transfer failure, the dependence of safety metrics on their denominators, and cohort provenance.', 'Our audit documents the transfer failure and cohort provenance. It also shows how the denominators affect the interpretation of safety metrics.'),
206:'The repeat study shows similarly low coverage. In five passes with the original prompt, D accepts 21–26 real cases, with conditional risk of 57.1–71.4%. E accepts 0–1 cases. Under either prewritten prompt variant, E accepts none. These repeats let us assess prediction stability; they do not add independent source images. Appendix C.4 reports the metrics, failures and additional cost for each pass.',
216:txt(ps[216]).replace('This is a deterministic finite-cohort bound, not a population guarantee or a human ceiling; a different grounder or scoring rule changes it.', 'The bound is deterministic and applies to this finite cohort. It gives no population guarantee and sets no ceiling on human performance. It changes if the grounder or scoring rule changes.'),
219:'Probability quality. Original E has a Brier loss of 0.06125, compared with 0.05234 for the retrospective constant-prevalence predictor. E therefore has a Brier skill of −0.170 (Equation C1). Its low expected calibration error (ECE) does not, on its own, show that the probabilities are useful. The extra native signals also add little discrimination. On the real cohort, B and E have nearly the same AUROC, and their source-cluster intervals overlap. The full ranking and Brier results appear in Appendix C.2.',
316:'Native presence and uniqueness signals substantially improve selective clicking on authored synthetic layouts. We do not find comparable evidence of usefulness on real interfaces. After removing the 200 reused pilot cases, the frozen logistic gate accepts just one of 751 real cases. The three-signal policy still has a conditional risk of 61.5%. The study documents this failure to transfer, traces the cohort provenance and shows how denominators affect the interpretation of safety metrics. In tests with the same interface, the quantized Qwen baseline has lower strict localization accuracy. For both models, acceptance remains unreliable under the semantic one-label rule. These results do not establish broader model superiority, formal safety or practical utility.',
1121:'Both annotators label 98 real cases unique. Their boxes have a mean IoU of 0.512 across these cases. IoU is at least 0.3 in 79.6% of cases, at least 0.5 in 61.2%, and at least 0.75 in 19.4%. A’s box centre lies inside B’s box in 81.6% of cases. B’s box centre lies inside A’s in 88.8%. These rates give a conditional reference for annotation agreement. They exclude cases in which the annotators disagree on status, and there are no independently verified true boxes. They therefore set no absolute ceiling on human or model performance.',
1342:txt(ps[1342]).replace('The assumed prompt lengths were not measured, and this scenario supplies neither a GPT-4o bill nor an accuracy result.', 'We did not measure these prompt lengths. The scenario is a cost estimate; it reports neither an actual GPT-4o bill nor an accuracy result.')
 }
 before='\n\n'.join(txt(ps[i]) for i in edits);after='\n\n'.join(edits.values())
 (R/'readability_before.txt').write_text(before);(R/'readability_after.txt').write_text(after)
 for name in ['before','after']:
  inp=R/f'readability_{name}.txt'
  subprocess.run([PY,str(S/'inspect_text.py'),'--stylometry','--json',str(inp)],stdout=open(R/f'readability_{name}.score.json','w'))
  clean=R/f'readability_{name}.cleaned.txt'
  subprocess.run([PY,str(S/'clean_text.py'),str(inp),'-o',str(clean),'--no-normalize-spaces','--stats'],check=True)
  assert inp.read_text()==clean.read_text()
 for i,new in edits.items():
  p=ps[i];old=txt(p)
  assert not p.xpath('ancestor::w:tbl | .//m:oMath | .//w:hyperlink',namespaces=ns)
  assert Counter(re.findall(r'\d+(?:[.,]\d+)*',old))==Counter(re.findall(r'\d+(?:[.,]\d+)*',new)),i
  nodes=p.xpath('.//w:t',namespaces=ns);starts=[];pos=0
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
  assert txt(p)==new
  for n in nodes:
   if n.text and (n.text[0].isspace() or n.text[-1].isspace()):n.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 for xp in ['//m:oMath','//w:tbl','//w:drawing','//w:hyperlink','//w:pPr','//w:rPr']:
  assert [E.tostring(x) for x in original.xpath(xp,namespaces=ns)]==[E.tostring(x) for x in root.xpath(xp,namespaces=ns)],xp
 for i,(a,b) in enumerate(zip(original.xpath('//w:p',namespaces=ns),ps)):
  if i not in edits:assert E.tostring(a)==E.tostring(b),i
 out=R/'When_Not_to_Click_Readability_Revised.docx'
 with ZipFile(out,'w') as zo:
  for info in z.infolist():zo.writestr(info,E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else z.read(info.filename))
 (R/'readability_edits.json').write_text(json.dumps([{'paragraph':i,'before':txt(original.xpath('//w:p',namespaces=ns)[i]),'after':s} for i,s in edits.items()],indent=2,ensure_ascii=False))
 print('Saved:',out,'; paragraphs edited:',len(edits),'Math objects unchanged:',len(root.xpath('//m:oMath',namespaces=ns)))
