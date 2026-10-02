#!/usr/bin/env python3
from pathlib import Path
import csv, struct

ROOT=Path(__file__).resolve().parents[2]
B1=ROOT/'data/reference/step3b1/SC0002_STEP3B1_Top20_Control_Candidates.csv'
D=ROOT/'data/reference/step3b2'
IMG=D/'review_contact_sheets'
META=D/'SC0002_STEP3B2_Top20_Review_Image_Metadata.csv'
META_ALL=D/'SC0002_STEP3B2_Review_Image_Metadata.csv'
INDEX=D/'SC0002_STEP3B2_Review_Contact_Sheet_Index.csv'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def png_size(p):
    b=p.read_bytes()[:24]
    if len(b)<24 or b[:8]!=b'\x89PNG\r\n\x1a\n': raise AssertionError(f'{p.name}: invalid PNG')
    return struct.unpack('>II',b[16:24])

def main():
    top=read(B1); meta=read(META); meta_all=read(META_ALL); idx=read(INDEX)
    if len(top)!=20: raise AssertionError('Top20 row count')
    if len(meta)!=140: raise AssertionError(f'Top20 metadata rows {len(meta)} != 140')
    if len(meta_all)!=147: raise AssertionError(f'all-site metadata rows {len(meta_all)} != 147')
    if len(idx)!=20: raise AssertionError(f'index rows {len(idx)} != 20')
    top_ids=[r['candidate_id'] for r in top]
    if set(r['site_id'] for r in meta)!=set(top_ids): raise AssertionError('metadata site set != Top20')
    for cid in top_ids:
        ys=sorted(int(float(r['year'])) for r in meta if r['site_id']==cid)
        if ys != list(range(2020,2027)): raise AssertionError(f'{cid}: years {ys}')
    pngs=sorted(p for p in IMG.glob('*_review_contact_sheet.png'))
    if len(pngs)!=20: raise AssertionError(f'contact sheet count {len(pngs)} != 20')
    expected_files=[]
    for r in top:
        rank=int(float(r['rank'])); cid=r['candidate_id']; expected_files.append(f'{rank:02d}_{cid}_review_contact_sheet.png')
    if [p.name for p in pngs] != sorted(expected_files): raise AssertionError('contact-sheet filenames do not match Top20')
    for p in pngs:
        if png_size(p)!=(1340,770): raise AssertionError(f'{p.name}: unexpected PNG size {png_size(p)}')
    if [r['candidate_id'] for r in idx] != top_ids: raise AssertionError('review index order != Top20')
    if [r['contact_sheet_file'] for r in idx] != expected_files: raise AssertionError('review index filenames mismatch')
    counts=[int(float(r['source_scene_count'])) for r in meta]
    if min(counts)<130 or max(counts)>174: raise AssertionError(f'unexpected scene-count range {min(counts)}-{max(counts)}')
    print(f'PASS — Step 3B.2 review archive contains 20 Top20 RGB contact sheets (1340×770), 140 control-year metadata rows, and a matching audit index; scene-count range {min(counts)}–{max(counts)}.')

if __name__=='__main__': main()
