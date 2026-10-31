#!/usr/bin/env python3
"""
Genealogy Data Builder & Tree Merger
Builds:
1. Árbol Reyes - Moreira (Isolated)
2. Árbol González - Guijarro (Isolated)
3. Árbol Familiar Unificado (Unified Master Tree)
Outputs both JSON files and a zero-dependency JS bundle for web and GitHub Pages.
"""

import os
import json
import re
import shutil
from collections import Counter

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(WORKSPACE_ROOT, 'docs')
DATA_DIR = os.path.join(DOCS_DIR, 'data')
PICS_SRC_DIR = os.path.join(WORKSPACE_ROOT, 'PICs', 'AGUADO')
PICS_DEST_DIR = os.path.join(DOCS_DIR, 'pics', 'aguado')

PHOTO_MAPPINGS = {
    'I3': ['pics/aguado/Carmelo_REYES_A.jpg', 'pics/aguado/Carmelo_REYES_B.jpg'],
    'I20': ['pics/aguado/Luis_REYES.jpg'],
    'I19': [
        'pics/aguado/Encarna_AGUADO_A.jpg',
        'pics/aguado/Encarna_AGUADO_B.jpg',
        'pics/aguado/Encarna_AGUADO_Virginia_AGUADO.jpg',
        'pics/aguado/Francisco_AGUADO_y_Encarnacion_AGUADO.jpg'
    ],
    'I42': [
        'pics/aguado/Francisco_AGUADO_A.jpg',
        'pics/aguado/Francisco_AGUADO_B.jpg',
        'pics/aguado/Francisco_AGUADO_C.jpg',
        'pics/aguado/Francisco_AGUADO_Maria_HIDALGO.jpg',
        'pics/aguado/Francisco_AGUADO_y_Encarnacion_AGUADO.jpg',
        'pics/aguado/Francisco_AGUADO_y_mas.jpg'
    ],
    'I43': [
        'pics/aguado/Maria_HIDALGO.jpg',
        'pics/aguado/Francisco_AGUADO_Maria_HIDALGO.jpg'
    ],
    'I53': [
        'pics/aguado/Carmen_VACCHIANO_María_José_VACCHIANO_A.jpg',
        'pics/aguado/Carmen_VACCHIANO_María_José_VACCHIANO_B.jpg'
    ],
    'I54': [
        'pics/aguado/Carmen_VACCHIANO_María_José_VACCHIANO_A.jpg',
        'pics/aguado/Carmen_VACCHIANO_María_José_VACCHIANO_B.jpg'
    ]
}

def merge_gedcom_trees(base_path, merge_path, output_path):
    with open(base_path, 'r', encoding='utf-8', errors='ignore') as f:
        base_lines = f.readlines()
    with open(merge_path, 'r', encoding='utf-8', errors='ignore') as f:
        merge_lines = f.readlines()

    # Bridge mapping
    indi_map = {
        'I1': 'I213',  # Estilita
        'I2': 'I34',   # Juan José
        'I4': 'I212',  # Emiliana
        'I8': 'I214',  # Aurora
    }
    fam_map = {
        'F2': 'F68'    # Juan José & Emiliana family
    }

    max_i = 500
    max_f = 200
    for l in base_lines:
        m_i = re.match(r'^0 @I(\d+)@ INDI', l)
        if m_i: max_i = max(max_i, int(m_i.group(1)))
        m_f = re.match(r'^0 @F(\d+)@ FAM', l)
        if m_f: max_f = max(max_f, int(m_f.group(1)))

    merge_records = []
    curr = []
    for l in merge_lines:
        if l.startswith('0 '):
            if curr: merge_records.append(curr)
            curr = [l]
        else:
            if curr: curr.append(l)
    if curr: merge_records.append(curr)

    counter_i = max_i + 1
    counter_f = max_f + 1

    for rec in merge_records:
        h = rec[0].strip()
        m_i = re.match(r'^0 @(I\d+)@ INDI', h)
        if m_i:
            oid = m_i.group(1)
            if oid not in indi_map:
                indi_map[oid] = f'I{counter_i}'
                counter_i += 1
        m_f = re.match(r'^0 @(F\d+)@ FAM', h)
        if m_f:
            ofid = m_f.group(1)
            if ofid not in fam_map:
                fam_map[ofid] = f'F{counter_f}'
                counter_f += 1

    out_lines = []
    for l in base_lines:
        if l.strip() == '0 TRLR':
            continue
        out_lines.append(l)

    # Attach Emiliana's parents family to I212
    emiliana_famc = None
    for rec in merge_records:
        if rec[0].startswith('0 @I4@ INDI'):
            for rl in rec:
                m_famc = re.match(r'^1 FAMC @(F\d+)@', rl.strip())
                if m_famc:
                    emiliana_famc = fam_map.get(m_famc.group(1))

    new_out_lines = []
    for l in out_lines:
        new_out_lines.append(l)
        if l.strip() == '0 @I212@ INDI' and emiliana_famc:
            new_out_lines.append(f'1 FAMC @{emiliana_famc}@\n')
    out_lines = new_out_lines

    for rec in merge_records:
        h = rec[0].strip()
        m_i = re.match(r'^0 @(I\d+)@ INDI', h)
        m_f = re.match(r'^0 @(F\d+)@ FAM', h)

        if m_i:
            oid = m_i.group(1)
            if oid in ['I1', 'I2', 'I4', 'I8']:
                continue
            new_id = indi_map[oid]
            new_rec = [f'0 @{new_id}@ INDI\n']
            for line in rec[1:]:
                l_str = line
                for orig_i, mapped_i in indi_map.items():
                    l_str = re.sub(rf'@{orig_i}@', f'@{mapped_i}@', l_str)
                for orig_f, mapped_f in fam_map.items():
                    l_str = re.sub(rf'@{orig_f}@', f'@{mapped_f}@', l_str)
                new_rec.append(l_str)
            out_lines.extend(new_rec)

        elif m_f:
            ofid = m_f.group(1)
            if ofid == 'F2':
                continue
            new_id = fam_map[ofid]
            new_rec = [f'0 @{new_id}@ FAM\n']
            for line in rec[1:]:
                l_str = line
                for orig_i, mapped_i in indi_map.items():
                    l_str = re.sub(rf'@{orig_i}@', f'@{mapped_i}@', l_str)
                for orig_f, mapped_f in fam_map.items():
                    l_str = re.sub(rf'@{orig_f}@', f'@{mapped_f}@', l_str)
                new_rec.append(l_str)
            out_lines.extend(new_rec)

    out_lines.append('0 TRLR\n')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)

    print(f"Created unified master tree: {output_path}")

def parse_gedcom(filepath, tree_id, tree_title, subtitle, default_root_id=None):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    indis = {}
    fams = {}
    current = None
    ctype = None

    for line in lines:
        line = line.rstrip('\r\n')
        if not line:
            continue
        parts = line.strip().split(' ', 2)
        level = parts[0]

        if level == '0':
            if len(parts) >= 3 and parts[2] == 'INDI':
                ctype = 'INDI'
                cid = parts[1].strip('@')
                current = {
                    'id': cid,
                    'name': '',
                    'givenName': '',
                    'surname': '',
                    'sex': 'U',
                    'birth': {},
                    'death': {},
                    'baptism': {},
                    'burial': {},
                    'occupation': '',
                    'notes': [],
                    'fams': [],
                    'famc': None,
                    'photos': []
                }
                indis[cid] = current
            elif len(parts) >= 3 and parts[2] == 'FAM':
                ctype = 'FAM'
                cid = parts[1].strip('@')
                current = {
                    'id': cid,
                    'husb': None,
                    'wife': None,
                    'children': [],
                    'marriage': {}
                }
                fams[cid] = current
            else:
                ctype = None
                current = None
        elif current:
            tag = parts[1] if len(parts) > 1 else ''
            val = parts[2] if len(parts) > 2 else ''

            if ctype == 'INDI':
                if tag == 'NAME':
                    current['name'] = val.replace('/', '').strip()
                elif tag == 'GIVN':
                    current['givenName'] = val.strip()
                elif tag == 'SURN':
                    current['surname'] = val.strip()
                elif tag == 'SEX':
                    current['sex'] = val.strip().upper()
                elif tag == 'OCCU':
                    current['occupation'] = val.strip()
                elif tag == 'NOTE':
                    current['notes'].append(val.strip())
                elif tag == 'FAMS':
                    current['fams'].append(val.strip('@'))
                elif tag == 'FAMC':
                    current['famc'] = val.strip('@')
                elif level == '1':
                    if tag in ['BIRT', 'DEAT', 'CHR', 'BAPM', 'BURI']:
                        current['_last_event'] = tag
                    else:
                        current['_last_event'] = None
                elif level == '2' and current.get('_last_event'):
                    evt = current['_last_event']
                    target_dict = None
                    if evt == 'BIRT': target_dict = current['birth']
                    elif evt == 'DEAT': target_dict = current['death']
                    elif evt in ['CHR', 'BAPM']: target_dict = current['baptism']
                    elif evt == 'BURI': target_dict = current['burial']

                    if target_dict is not None:
                        if tag == 'DATE':
                            target_dict['date'] = val.strip()
                        elif tag == 'PLAC':
                            target_dict['place'] = val.strip()

            elif ctype == 'FAM':
                if tag == 'HUSB':
                    current['husb'] = val.strip('@')
                elif tag == 'WIFE':
                    current['wife'] = val.strip('@')
                elif tag == 'CHIL':
                    current['children'].append(val.strip('@'))
                elif level == '1':
                    if tag == 'MARR':
                        current['_last_event'] = 'MARR'
                    else:
                        current['_last_event'] = None
                elif level == '2' and current.get('_last_event') == 'MARR':
                    if tag == 'DATE':
                        current['marriage']['date'] = val.strip()
                    elif tag == 'PLAC':
                        current['marriage']['place'] = val.strip()

    # Clean temporary keys
    for p in indis.values():
        p.pop('_last_event', None)
    for f in fams.values():
        f.pop('_last_event', None)

    # Attach photos
    if tree_id in ['reyes_moreira', 'master_unified']:
        for pid, pphotos in PHOTO_MAPPINGS.items():
            if pid in indis:
                indis[pid]['photos'] = pphotos

    # Link relationships
    for pid, person in indis.items():
        parents = []
        siblings = []
        if person['famc'] and person['famc'] in fams:
            fam = fams[person['famc']]
            if fam['husb']: parents.append(fam['husb'])
            if fam['wife']: parents.append(fam['wife'])
            for ch in fam['children']:
                if ch != pid and ch not in siblings:
                    siblings.append(ch)
        person['parents'] = parents
        person['siblings'] = siblings

        spouses = []
        children = []
        for f_id in person['fams']:
            if f_id in fams:
                fam = fams[f_id]
                sp_id = fam['wife'] if fam['husb'] == pid else (fam['husb'] if fam['wife'] == pid else None)
                if sp_id and sp_id not in [s['id'] for s in spouses]:
                    spouses.append({'id': sp_id, 'marriage': fam['marriage']})
                for ch in fam['children']:
                    if ch not in children:
                        children.append(ch)
        person['spouses'] = spouses
        person['children'] = children

    # Statistics
    years = []
    places = []
    surnames = []
    given_names = []
    month_counts = {m: 0 for m in range(1, 13)}
    lifespans_m = []
    lifespans_f = []
    birth_centuries = []

    MONTH_MAP = {
        'jan': 1, 'ene': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'abr': 4,
        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'ago': 8, 'sep': 9,
        'set': 9, 'oct': 10, 'nov': 11, 'dec': 12, 'dic': 12
    }

    for p in indis.values():
        if p.get('surname'):
            surnames.append(p['surname'])

        gn = p.get('givenName', '')
        if not gn and p.get('name'):
            gn = p['name'].split()[0]
        if gn:
            first_w = gn.replace(',', '').split()[0].capitalize()
            if len(first_w) > 1 and first_w not in ['?', 'Desconocido']:
                given_names.append(first_w)

        bdate = p.get('birth', {}).get('date', '')
        ddate = p.get('death', {}).get('date', '')

        if bdate:
            m = re.search(r'\b([a-zA-ZáéíóúÁÉÍÓÚ]{3,})\b', bdate)
            if m:
                m_key = m.group(1).lower()[:3]
                if m_key in MONTH_MAP:
                    month_counts[MONTH_MAP[m_key]] += 1

            y_m = re.search(r'\b(1[4-9]\d\d|20\d\d)\b', bdate)
            if y_m:
                by = int(y_m.group(1))
                cent = (by // 100) + 1
                cent_roman = {16: 'XVI', 17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX', 21: 'XXI'}.get(cent, str(cent))
                birth_centuries.append(f'Siglo {cent_roman}')

        if bdate and ddate:
            yb_m = re.search(r'\b(1[4-9]\d\d|20\d\d)\b', bdate)
            yd_m = re.search(r'\b(1[4-9]\d\d|20\d\d)\b', ddate)
            if yb_m and yd_m:
                yb = int(yb_m.group(1))
                yd = int(yd_m.group(1))
                age = yd - yb
                if 0 <= age <= 115:
                    entry = {'age': age, 'name': p['name'], 'birth': yb, 'death': yd}
                    if p.get('sex') == 'M':
                        lifespans_m.append(entry)
                    elif p.get('sex') == 'F':
                        lifespans_f.append(entry)

        for ev in [p.get('birth', {}), p.get('death', {})]:
            d = ev.get('date', '')
            ym = re.findall(r'\b(1[4-9]\d\d|20\d\d)\b', d)
            if ym:
                years.extend([int(y) for y in ym])
            plc = ev.get('place', '')
            if plc:
                places.append(plc)

    min_year = min(years) if years else None
    max_year = max(years) if years else None
    top_surnames = Counter(surnames).most_common(8)
    top_given_names = Counter(given_names).most_common(8)
    top_places = Counter(places).most_common(8)
    birth_cent_counts = Counter(birth_centuries).most_common()

    def get_life_summary(arr):
        if not arr: return {'count': 0, 'avg': 0, 'maxAge': 0, 'maxPerson': ''}
        avg_age = round(sum(x['age'] for x in arr) / len(arr), 1)
        max_item = max(arr, key=lambda x: x['age'])
        return {
            'count': len(arr),
            'avg': avg_age,
            'maxAge': max_item['age'],
            'maxPerson': f"{max_item['name']} ({max_item['age']} años, {max_item['birth']}–{max_item['death']})"
        }

    lifespan_summary = {
        'men': get_life_summary(lifespans_m),
        'women': get_life_summary(lifespans_f),
        'overall': get_life_summary(lifespans_m + lifespans_f)
    }

    if not default_root_id or default_root_id not in indis:
        default_root_id = 'I1' if 'I1' in indis else next(iter(indis.keys()))

    return {
        'id': tree_id,
        'title': tree_title,
        'subtitle': subtitle,
        'rootId': default_root_id,
        'individualsCount': len(indis),
        'familiesCount': len(fams),
        'stats': {
            'minYear': min_year,
            'maxYear': max_year,
            'topSurnames': top_surnames,
            'topGivenNames': top_given_names,
            'topPlaces': top_places,
            'birthMonths': [{'month': m, 'count': month_counts[m]} for m in range(1, 13)],
            'birthCenturies': birth_cent_counts,
            'lifespan': lifespan_summary
        },
        'individuals': indis,
        'families': fams
    }

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PICS_DEST_DIR, exist_ok=True)

    # 1. GitHub Pages .nojekyll
    nojekyll_path = os.path.join(DOCS_DIR, '.nojekyll')
    with open(nojekyll_path, 'w') as f:
        f.write('')

    # 2. Copy photos
    if os.path.exists(PICS_SRC_DIR):
        for img in os.listdir(PICS_SRC_DIR):
            if img.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                src_path = os.path.join(PICS_SRC_DIR, img)
                dest_path = os.path.join(PICS_DEST_DIR, img)
                shutil.copy2(src_path, dest_path)
        print(f"Copied photos to {PICS_DEST_DIR}")

    # 3. Create Unified GEDCOM
    tree1_path = os.path.join(WORKSPACE_ROOT, 'REYES_MOREIRA_Genealogy.ged')
    tree2_path = os.path.join(WORKSPACE_ROOT, 'GONZALEZ_GUIJARRO_Genealogy.ged')
    tree3_path = os.path.join(WORKSPACE_ROOT, 'MASTER_UNIFIED_Genealogy.ged')
    merge_gedcom_trees(tree1_path, tree2_path, tree3_path)

    # 4. Parse all three trees
    t1 = parse_gedcom(
        tree1_path,
        'reyes_moreira',
        'Árbol Reyes - Moreira',
        'Tronco Principal · Madrid, Galicia, Asturias y Ribera del Duero',
        'I1'
    )

    t2 = parse_gedcom(
        tree2_path,
        'gonzalez_guijarro',
        'Árbol González - Guijarro',
        'Rama Estilita · Covarrubias, Moradillo, Fuentecén y Ribera del Arlanza',
        'I1'
    )

    t3 = parse_gedcom(
        tree3_path,
        'master_unified',
        'Árbol Unificado Familiar',
        'Fusión Completa · Reyes Moreira + González Guijarro (Siglos XVII – XXI)',
        'I1'
    )

    # 5. Save JSONs
    with open(os.path.join(DATA_DIR, 'reyes_moreira.json'), 'w', encoding='utf-8') as f:
        json.dump(t1, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DATA_DIR, 'gonzalez_guijarro.json'), 'w', encoding='utf-8') as f:
        json.dump(t2, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DATA_DIR, 'master_unified.json'), 'w', encoding='utf-8') as f:
        json.dump(t3, f, ensure_ascii=False, indent=2)

    # 6. Save JS bundle
    bundle_content = (
        f"window.TREES_DATA = {{\n"
        f"  'reyes_moreira': {json.dumps(t1, ensure_ascii=False)},\n"
        f"  'gonzalez_guijarro': {json.dumps(t2, ensure_ascii=False)},\n"
        f"  'master_unified': {json.dumps(t3, ensure_ascii=False)}\n"
        f"}};\n"
    )
    with open(os.path.join(DATA_DIR, 'trees_bundle.js'), 'w', encoding='utf-8') as f:
        f.write(bundle_content)

    print("All 3 trees processed and saved successfully in docs/data/!")

if __name__ == '__main__':
    main()
