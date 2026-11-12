#!/usr/bin/env python3
"""Normalize frozen external cases to the Jev image contract without changing aspect ratio."""

import argparse, json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ROUND=ROOT/'data/academic_2000/annotation_round_1'

def source_path(url):
    rel=parse_qs(urlparse(url).query).get('d',[''])[0]
    if not rel: raise ValueError(f'unsupported image URL: {url}')
    return ROOT/rel

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--labels',type=Path,default=ROUND/'frozen_labels/final_labels.jsonl')
    ap.add_argument('--output-dir',type=Path,default=ROUND/'external_confirmatory')
    args=ap.parse_args()
    if not args.labels.exists(): raise SystemExit('Frozen labels are missing. Complete and export all 259 adjudications first.')
    rows=[json.loads(x) for x in args.labels.read_text().splitlines() if x.strip()]
    images=args.output_dir/'images'; images.mkdir(parents=True,exist_ok=True)
    out=[]
    for row in rows:
        src=source_path(row['image'])
        with Image.open(src) as original: im=original.convert('RGB')
        ow,oh=im.size
        scale=min(1568/ow,1568/oh,1.0)
        nw,nh=max(1,round(ow*scale)),max(1,round(oh*scale))
        im=im.resize((nw,nh),Image.Resampling.LANCZOS) if (nw,nh)!=(ow,oh) else im
        cw,ch=max(280,nw),max(280,nh)
        left=(cw-nw)//2; top=(ch-nh)//2
        canvas=Image.new('RGB',(cw,ch),'white'); canvas.paste(im,(left,top))
        dest=images/f"{row['case_id']}.jpg"; canvas.save(dest,quality=92,optimize=True)
        boxes=[[round(x1*scale+left,3),round(y1*scale+top,3),round(x2*scale+left,3),round(y2*scale+top,3)] for x1,y1,x2,y2 in row['boxes_xyxy']]
        try: screenshot_path=dest.relative_to(ROOT).as_posix()
        except ValueError: screenshot_path=str(dest.resolve())
        out.append({'case_id':row['case_id'],'instruction':row['instruction'],
                    'screenshot_path':screenshot_path,'source_image':row['image'],
                    'target_status':row['target_status'],'ground_truth_boxes':boxes,
                    'localization_eligibility':row['target_status']=='unique','width':cw,'height':ch,
                    'transform':{'source_size':[ow,oh],'scale':scale,'pad_left':left,'pad_top':top}})
    manifest=args.output_dir/'cases.jsonl'
    manifest.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in out))
    print(json.dumps({'state':'READY','cases':len(out),'manifest':str(manifest)}))
if __name__=='__main__': main()
