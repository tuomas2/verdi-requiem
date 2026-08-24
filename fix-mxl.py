#!/usr/bin/env python3
"""Paikkaa Audiveriksen MusicXML-viennistä puuttuvat tahdit.

MuseScore kaatuu tuonnissa, jos jollakin osastolla on eri määrä tahteja kuin
muilla. Tämä lisää puuttuvien tahtien paikalle kokotahdin tauon.

Käyttö: python3 fix-mxl.py sisään.mxl ulos.mxl
"""
import copy, os, sys, zipfile
import xml.etree.ElementTree as ET


def inner_xml_name(z):
    for n in z.namelist():
        if not n.startswith('META-INF') and n.lower().endswith('.xml'):
            return n
    raise SystemExit('MusicXML-tiedostoa ei löytynyt paketista')


def measure_divisions(part):
    for m in part.findall('measure'):
        d = m.find('attributes/divisions')
        if d is not None and d.text:
            return int(d.text)
    return 4


def fix(root):
    parts = root.findall('part')
    if not parts:
        return 0
    order = [m.get('number') for m in parts[0].findall('measure')]
    added = 0
    for part in parts[1:]:
        have = {m.get('number'): m for m in part.findall('measure')}
        div = measure_divisions(part)
        for pos, num in enumerate(order):
            if num in have:
                continue
            m = ET.Element('measure', {'number': num})
            note = ET.SubElement(m, 'note')
            ET.SubElement(note, 'rest').set('measure', 'yes')
            ET.SubElement(note, 'duration').text = str(div * 4)
            ET.SubElement(note, 'voice').text = '1'
            part.insert(pos, m)
            added += 1
            print(f'  osasto {part.get("id")}: lisätty tahti {num}')
    return added


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(src) as z:
        name = inner_xml_name(z)
        tree = ET.ElementTree(ET.fromstring(z.read(name)))
    root = tree.getroot()
    counts = {p.get('id'): len(p.findall('measure')) for p in root.findall('part')}
    print(f'{os.path.basename(src)}: {len(counts)} osastoa, '
          f'tahtimäärät {sorted(set(counts.values()))}')
    added = fix(root)
    print(f'lisätty {added} tahtia')
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('META-INF/container.xml',
                   '<?xml version="1.0" encoding="UTF-8"?>\n<container><rootfiles>'
                   '<rootfile full-path="score.xml" '
                   'media-type="application/vnd.recordare.musicxml+xml"/>'
                   '</rootfiles></container>\n')
        z.writestr('score.xml', ET.tostring(root, encoding='UTF-8', xml_declaration=True))
    print(f'kirjoitettu {dst}')


if __name__ == '__main__':
    main()
