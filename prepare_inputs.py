#!/usr/bin/env python3
"""Validate a group MBM bundle; export subject-ordered inputs for official MBM.

NOT a replacement for Cao 2024 toolbox. Requires already-aligned 32k fsLR
anatomical maps and SAME-template eigenmodes/mass/mask/mesh.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

HEMIS = ('lh', 'rh')
VERTICES = 32492  # fsLR 32k vertices per hemisphere
FIELDS = ('subject_id','group','age','sex','lh_map','rh_map')

def text_mask_length(path):
    vals = path.read_text(encoding='utf-8').split()
    if len(vals) != VERTICES or any(v not in ('0','1','0.0','1.0') for v in vals):
        raise ValueError(f'{path} must contain exactly {VERTICES} binary mask values')
    if sum(float(v) for v in vals) < 20000:
        raise ValueError(f'{path}: unusually small cortex mask')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default='config.json')
    args = p.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding='utf-8'))
    root = Path(cfg['group_bundle']).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f'group_bundle not found: {root}')
    cases = str(cfg['case_label']).strip()
    controls = str(cfg['control_label']).strip()
    if not cases or not controls or cases == controls:
        raise ValueError('Distinct case_label and control_label required')
    n_modes = int(cfg.get('num_modes',150))
    n_perm = int(cfg.get('n_permutations',5000))
    if not 2 <= n_modes <= 150:
        raise ValueError('For the official 150-mode fsLR reference, num_modes must be in 2..150')
    if n_perm < 100:
        raise ValueError('Set at least 100 permutations (5000 recommended for final work)')

    path = root / 'subjects.csv'
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or any(x not in reader.fieldnames for x in FIELDS):
            raise ValueError(f'{path}: required columns are {FIELDS}')
        rows = [r for r in reader if r['group'] in (cases, controls)]
    if not rows:
        raise ValueError('No rows after case/control selection')

    seen = set(); counts = {cases:0,controls:0}; matrix = []
    lists = {'lh':[],'rh':[]}; included=[]
    for r in rows:
        sid = r['subject_id'].strip()
        if not sid or sid in seen:
            raise ValueError(f'Duplicate/blank subject ID: {sid!r}')
        seen.add(sid)
        grp = r['group'].strip()
        counts[grp] += 1
        age = float(r['age'])
        if not 18 <= age <= 120:
            raise ValueError(f'{sid} age out of expected range')
        sex = r['sex'].strip().lower()
        if sex in ('m','male','1'): sex_code=1
        elif sex in ('f','female','2','0'): sex_code=0
        else: raise ValueError(f'{sid} sex must be M/F or 1/2')
        matrix.append([1 if grp==cases else 2, age, sex_code])
        included.append([sid, grp, age, sex_code])
        for h in HEMIS:
            target = (root / r[f'{h}_map']).resolve()
            if not target.is_file():
                raise FileNotFoundError(f'{sid}: missing {h} map: {target}')
            if not target.is_relative_to(root):
                raise ValueError(f'{sid}: map path escapes group bundle: {target}')
            if target.suffix.lower() != '.gii':
                raise ValueError(f'{sid}: expected metric GIFTI .gii for {h}')
            lists[h].append(str(target))
    if min(counts.values()) < 3:
        raise ValueError(f'Need at least 3 subjects in each group: {counts}')

    for h in HEMIS:
        for fn in (f'{h}.mask.txt', f'{h}.eig.txt', f'{h}.mass.mat', f'{h}.surf.vtk'):
            template = root / 'template' / fn
            if not template.is_file():
                raise FileNotFoundError(f'Missing SAME-TEMPLATE resource: {template}')
        text_mask_length(root / 'template' / f'{h}.mask.txt')

    out = Path('prepared')
    out.mkdir(exist_ok=True)
    for h in HEMIS:
        (out / f'{h}_input_maps.txt').write_text('\n'.join(lists[h])+'\n',encoding='utf-8')
    with (out/'design_ANCOVA.txt').open('w',encoding='utf-8') as f:
        for g,age,sex in matrix: f.write(f'{g}\t{age:.8f}\t{sex}\n')
    with (out/'included_subjects.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['subject_id','group','age','sex_code']);writer.writerows(included)

    report = {
        'status':'PREFLIGHT_ONLY_NOT_MBM_RESULTS',
        'case_label':cases, 'control_label':controls,
        'counts':counts,'n_total':len(rows),
        'template':'fsLR 32k midthickness, both hemispheres',
        'num_modes':n_modes, 'n_permutations':n_perm,
        'warning':'GIFTI vertex space and eigenmode/mass alignment require independent inspection; same length is not sufficient.',
        'original_toolbox':'https://github.com/NSBLab/MBM',
    }
    (out/'preflight_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('MBM preflight failed:', e, file=sys.stderr)
        raise
