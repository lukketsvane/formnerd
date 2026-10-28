import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'cad/assembly-manifest.json').read_text())
items = {p['id']: p for p in manifest['parts'] + manifest['hardware']}


def scene(ids, direction=(-1, 2, 1), shifts=None):
    shifts = shifts or {}
    return {'objects': [{'id': i, 'path': items[i]['stl'], 'color': items[i]['color'], 'translation': shifts.get(i, [0, 0, 0])} for i in ids], 'camera': {'direction': list(direction)}, 'margin': 0.12}


def needed(pid, name, quantity):
    return {'scene': scene([pid], (-1, 2, 1)), 'label': name, 'quantity': quantity}


names = {'P01': 'Frontskal', 'P02': 'Bakskal', 'P03': 'Kameraberar', 'P04': 'Venstre linsekrage', 'P05': 'Høgre linsekrage', 'P06': 'Utløysarknapp', 'P08': 'Venstre haldelist', 'P09': 'Høgre haldelist', 'P10': 'Passningsprøve'}
all_ids = [p for p in items if p.startswith('P') and p != 'P10']
base = ['P01', 'P04', 'P05', 'P06']
assembled = all_ids + [p for p in items if not p.startswith('P')]
pages = [
    {'type': 'cover', 'title': 'STEREO R01', 'scene': scene(assembled, (-1, -2, 1)), 'subtitle': 'Montering av mekanisk prototype', 'note': 'Bygd frå vald skisse og Tripo-master. Digitalt mekanisk byggjesett. Mål mot elektronikken, fysisk passform og kamerafunksjon må framleis prøvast.'},
    {'type': 'inventory', 'title': 'Delar · 1', 'items': [{'id': i, 'name': names[i], 'quantity': 1, 'scene': scene([i])} for i in ['P01', 'P02', 'P03', 'P04', 'P05', 'P06']], 'note': 'Linsekragane er mekaniske innfatningar, ikkje optikk. Skala og knappen har mesh-geometri; dei presise mekaniske delane har eigne STEP-filer.'},
    {'type': 'inventory', 'title': 'Delar · 2', 'items': [{'id': i, 'name': names[i], 'quantity': 1, 'scene': scene([i])} for i in ['P08', 'P09', 'P10']] + [
        {'id': 'A', 'name': 'M3 × 30', 'quantity': 4, 'scene': scene(['H01'])},
        {'id': 'B', 'name': 'M3 × 12', 'quantity': 2, 'scene': scene(['H05'])},
        {'id': 'C', 'name': 'M3 × 10', 'quantity': 4, 'scene': scene(['H07'])},
        {'id': 'D', 'name': 'M3-mutter', 'quantity': 10, 'scene': scene(['N01'])}], 'note': 'Kjøp skruar og mutrar; ikkje print maskinvara. Verktøy: passande sekskantnøkkel, skyvelære og avgradingsverktøy. P10 er prøve, ikkje produktdel.'},
    {'number': 1, 'title': 'Prøv passforma', 'scene': scene(['P10'], (-1, -2, 2)), 'labels': [{'id': 'P10', 'text': 'P10', 'position': [.82, .75]}], 'instructions': ['Print P10 først. Prøv ei linsekrage, M3-skrue, mutter og kortkant.', 'Avgrad forsiktig. Delane skal gli på plass utan stor kraft.'], 'check': 'Stopp dersom passninga er feil. Juster toleransar før resten av delane blir printa.'},
    {'number': 2, 'title': 'Set inn mutrane', 'needed': [needed('N01', 'M3', 6)], 'scene': scene(['P01'] + [f'N{i:02}' for i in range(1, 7)], shifts={f'N{i:02}': [0, 12, 0] for i in range(1, 7)}), 'labels': [{'id': 'P01', 'text': 'P01', 'position': [.1, .78]}], 'instructions': ['Plasser fire mutrar for bakskalet og to for kameraberaren i P01.', 'Kontroller at alle seks mutrane sit flatt i lommene før neste steg.'], 'check': 'Monteringsvegane og tilkomsten til mutrane er viste og kontrollerte digitalt. Prøv dei også fysisk.'},
    {'number': 3, 'title': 'Set inn kragane', 'scene': scene(['P01', 'P04', 'P05'], shifts={'P04': [0, 32, 0], 'P05': [0, 32, 0]}), 'labels': [{'id': 'P04', 'text': 'P04', 'position': [.22, .80]}, {'id': 'P05', 'text': 'P05', 'position': [.83, .75]}], 'arrows': [{'from': [-6, 11, 48], 'to': [-6, -11, 48]}, {'from': [48, 11, 48], 'to': [48, -11, 48]}], 'instructions': ['Før begge kragane frå innsida mot fronten.', 'Flensane skal liggje bak skuldrene i frontskalet.'], 'check': 'Kragane blir haldne på plass av kameraberaren i steg 5. Ingen liming i denne modellen.'},
    {'number': 4, 'title': 'Set inn knappen', 'scene': scene(base, shifts={'P06': [0, 0, -22]}), 'labels': [{'id': 'P06', 'text': 'P06', 'position': [.17, .37]}], 'arrows': [{'from': [-49.5, -13, 55], 'to': [-49.5, -13, 69]}], 'instructions': ['Før knappen opp i opninga frå innsida av P01.', 'Hald knappen på plass til bakskalet er montert.'], 'check': 'Knappen er ein mekanisk demonstrator. Fjør og elektrisk brytar er ikkje monterte.'},
    {'number': 5, 'title': 'Fest beraren', 'needed': [needed('H05', 'M3 × 12', 2)], 'scene': scene(base + ['P03', 'H05', 'H06'], shifts={'P03': [0, 24, 0], 'H05': [0, 38, 0], 'H06': [0, 38, 0]}), 'labels': [{'id': 'P03', 'text': 'P03', 'position': [.85, .76]}], 'arrows': [{'from': [21, 20, 40], 'to': [21, 2, 40]}], 'instructions': ['Før P03 fram mot frontskalet. Kragane blir fanga mellom delane.', 'Fest med to M3 × 12. Stram varsamt for hand.'], 'check': 'Ingen del skal bøyast for å få skruehola til å passe. Kontroller at kragane ikkje kan falle ut.'},
    {'number': 6, 'title': 'Prøv korta', 'needed': [needed('H07', 'M3 × 10', 4), needed('N07', 'M3', 4)], 'scene': scene(['P03', 'P08', 'P09', 'H07', 'H08', 'H09', 'H10'], shifts={'P08': [0, 17, 16], 'P09': [0, 17, 16], **{f'H{i:02}': [0, 26, 16] for i in range(7, 11)}}), 'labels': [{'id': 'P08', 'text': 'P08', 'position': [.15, .79]}, {'id': 'P09', 'text': 'P09', 'position': [.85, .76]}], 'instructions': ['Prøv dei faktiske korta utan straum. Kontroller komponentar og kablar.', 'Monter haldelistene berre når korta sit fritt og utan press på komponentane.'], 'check': 'Nominell kortflate: 27 × 40,5 mm. MB-kort, optisk senter, linsemodul og kabelruting er ikkje passformstadfesta.'},
    {'number': 7, 'title': 'Lukk huset', 'needed': [needed('H01', 'M3 × 30', 4)], 'scene': scene(assembled, shifts={'P02': [0, 46, 0], **{f'H{i:02}': [0, 60, 0] for i in range(1, 5)}}), 'labels': [{'id': 'P02', 'text': 'P02', 'position': [.82, .76]}], 'arrows': [{'from': [-10, 49, 42], 'to': [-10, 27, 42]}], 'instructions': ['Hald kablar utanfor skøyt og knappgaffel. Før bakskalet rett inn.', 'Fest med fire M3 × 30. Stram lett og kryssvis.'], 'check': 'Bakskalet fangar knappen. Kontroller fri knapperørsle og at skøytane sluttar jamt.'},
    {'title': 'Monteringsoversikt', 'scene': scene(all_ids, shifts={i: items[i]['exploded_translation'] for i in all_ids}), 'labels': [{'id': i, 'text': i, 'position': xy} for i, xy in [('P01', [.12, .35]), ('P02', [.88, .83]), ('P03', [.72, .33]), ('P04', [.16, .69]), ('P05', [.44, .82]), ('P06', [.12, .91])]], 'instructions': ['Ta vare på delnummera ved reparasjon eller vidare endring.'], 'check': 'Alle viste delar kjem frå same CAD-revisjon som printfilene. Eksploderte avstandar er berre for forklaring.'},
    {'title': 'Før bruk', 'scene': scene(assembled, (-1, -2, 1)), 'instructions': ['Dette er eit digitalt mekanisk prøvebygg, ikkje eit ferdig fungerande kamera.', 'Prøv passform, varme, optikk, utløysar og elektrisk system før bruk.'], 'check': 'USB-C er ei reservert opning. Lading, dataoverføring, stereosynkronisering og kravet om minst Ø30 mm faktisk optikk er framleis opne.'}
]
pages[7], pages[8] = pages[8], pages[7]
pages[7]['number'] = 5
pages[8]['number'] = 6
pages[7]['instructions'] = ['Prøv dei faktiske korta utan straum medan P03 ligg utanfor huset.', 'Set inn mutrane og fest haldelistene berre når kort og komponentar ligg fritt.']
pages[8]['instructions'] = ['Før den ferdig prøvde kassetten inn frå baksida. Hald kablane fri.', 'Fest med to M3 × 12. Stram varsamt for hand.']
pages[5]['check'] = 'Kragane blir haldne på plass av kameraberaren i steg 6. Ingen liming i denne modellen.'
pages[4]['scene'] = scene(['P01'] + [f'N{i:02}' for i in range(1, 7)], shifts={'N01': [0, 0, 12], 'N02': [0, 0, 12], 'N03': [0, 0, -12], 'N04': [0, 0, -12], 'N05': [12, 0, 0], 'N06': [12, 0, 0]})
pages[4]['instructions'] = ['Skyv fire mutrar inn i lommene ved skøyten frå innsida.', 'Skyv dei to berarmutrane inn frå sida. Alle skal liggje flatt.']
closure_label = re.search(r'M3\s*×\s*\d+', items['H01']['name']).group(0)
keeper_label = re.search(r'M3\s*×\s*\d+', items['H07']['name']).group(0)
def refresh(value):
    if isinstance(value, str):
        return value.replace('M3 × 30', closure_label).replace('M3 × 10', keeper_label)
    if isinstance(value, dict):
        return {k: refresh(v) for k, v in value.items()}
    if isinstance(value, list):
        return [refresh(v) for v in value]
    return value
pages = refresh(pages)
if keeper_label == re.search(r'M3\s*×\s*\d+', items['H05']['name']).group(0):
    pages[2]['items'] = [i for i in pages[2]['items'] if i['id'] != 'C']
    for i in pages[2]['items']:
        if i['id'] == 'B':
            i['quantity'] = 6
        if i['id'] == 'D':
            i['id'] = 'C'
pages[5]['labels'] = [{'id': 'P04', 'text': 'P04', 'offset': [35, 55]}, {'id': 'P05', 'text': 'P05', 'offset': [-30, 55]}]
sx, sy = manifest['datum'].get('shutter_axis_xy_mm', [-49.5, -6.6])
drop = float(manifest['datum'].get('shutter_entry_drop_mm', 2))
drop_text = f'{drop:g}'.replace('.', ',')
pages[6]['scene'] = scene(base, shifts={'P06': [0, 28, -drop]})
pages[6]['labels'] = [{'id': 'P06', 'text': 'P06', 'offset': [-45, 75]}]
pages[6]['arrows'] = [{'from': [sx, sy+23, 75], 'to': [sx, sy+5, 75]}]
pages[6]['instructions'] = [f'Før knappen inn frå baksida, {drop_text} mm under sluttposisjonen.', f'Lyft knappen {drop_text} mm opp i setet. Hald han støtta til bakskalet er på.']
pages[10]['scene'] = scene(all_ids, (1, 2, 1.1), {'P01': [0, -65, 0], 'P02': [-30, 185, 0], 'P03': [0, 55, 0], 'P04': [0, -10, 0], 'P05': [0, -10, 0], 'P06': [0, -65, 30], 'P08': [0, 95, 35], 'P09': [0, 95, 35]})
pages[10]['labels'] = [{'id': i, 'text': i, 'offset': xy} for i, xy in [('P01', [-38, -50]), ('P02', [45, 25]), ('P03', [0, -65]), ('P04', [0, 45]), ('P05', [-25, 35]), ('P06', [-15, 35]), ('P08', [10, 30]), ('P09', [25, 20])]]
pages[10]['labels'][0].update(anchor_fraction=[.04, .60], offset=[-28, -28])
pages[7]['labels'] = [{'id': 'P08', 'text': 'P08', 'offset': [40, 65]}, {'id': 'P09', 'text': 'P09', 'offset': [-30, 60]}]
cassette = ['P03', 'P08', 'P09'] + [f'{prefix}{i:02}' for prefix in ['H', 'N'] for i in range(7, 11)]
pages[8]['scene'] = scene(base + cassette + ['H05', 'H06'], shifts={**{i: [0, 24, 0] for i in cassette}, 'H05': [0, 38, 0], 'H06': [0, 38, 0]})
plan = {'title': 'FormNerd Stereo R01 · Monteringsrettleiing', 'revision': 'STEREO R01 · MEKANISK PROTOTYPE', 'filename': 'FormNerd-Stereo-R01-montering.pdf', 'pages': pages}
(ROOT / 'manual/plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2))
hero = scene(assembled, (-1, -2, 1))
hero.update(mode='product', size=[2200, 1800], supersample=1.5, margin=.10)
(ROOT / 'review/hero-scene.json').write_text(json.dumps(hero, indent=2))
print(len(pages))
