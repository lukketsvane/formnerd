#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A5 - pakkesøk for handhaldt kamera (ESP32-CAM + ESP32-CAM-MB + 1S LiPo + TP4056 USB-C + Pololu U1V11F5).

Koordinatar (alle mål i mm):
  x = djupn, +x = framover (linsa peikar mot +x)
  y = opp
  z = breidd, +z = til høgre sett bakfrå (fotografen sitt høgre), dvs. z = x × y
Indre hola: x i [0, X] (x = 0 er innsida av bakveggen/lokket, x = X er innsida av frontveggen),
            y i [0, Y], z i [0, Z].

Metode (brute force over orienteringar og plasseringar):
  1. For kvar arkitektur (kva vegg cella ligg mot) og kvar orientering av stabelen og cella
     blir hola auka i steg på 0,5 mm frå ei nedre grense, sortert etter ytre volum.
  2. Store delar (stabel, celle, skum, skiljeplate, leidningssone) blir prøvde i alle hjørne-
     og kantankre.
  3. Småkomponentar blir plasserte med «extreme point»-kandidatar (alle kombinasjonar av
     vegg- og nabokantar per akse) i alle tillatne orienteringar, med djupn-først-søk og
     tilbakesporing (dei K beste kandidatane per komponent).
  4. Kvar løysing må passere: ingen overlapp, minsteklaringar, port-/brytar-/knappekrav,
     og leidningsruting: kvart leidningspar må få ein 3 mm (26 AWG) eller 2 mm (30 AWG)
     kanal gjennom ledig rom (Manhattan-ruting, med eller utan mellompunkt).
  5. Første løysing i volumrekkjefølgje = minste volum for denne heuristikken.

Utdata: layout_<n>.glb (eitt mesh per komponent, namngjeve), layout_<n>.png, pakking.json.
Skriv berre under katalogen der skriptet ligg.
"""
import sys, os, json, math, itertools, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, '.pylib'))  # matplotlib (sist i stien, så system-numpy vinn)

import numpy as np
import trimesh

EPS = 1e-6
ST = 0.5  # stegstorleik i hol-søket (mm)

# ---------------------------------------------------------------------------
# 1. KJELDEFESTE MÅL
# ---------------------------------------------------------------------------
KJ = {
    'DM': '/home/user/formnerd/A2/print/delmaal.json',
    'PAR': '/home/user/formnerd/A2/print/parametrar.json',
    'AT': 'https://datasheet.lcsc.com/datasheet/pdf/a6b8e236d770ab01c85fedd0de00a6bb.pdf?productCode=C277946',
    'IAR': 'https://iarduino.ru/lib/78eba891fa500cedb3b7a5641d82ce74.pdf',
    'EEMB_PCM': 'https://store.comet.bg/download-file.php?id=19944',
    'EEMB': 'https://store.comet.bg/download-file.php?id=9211',
    'AZ': 'https://www.az-delivery.de/en/products/tp4056-with-protection-type-c',
    'TT': 'https://www.tinytronics.nl/en/power/bms-and-chargers/li-ion-and-li-po/with-protection-circuit/tp4056-usb-c-li-ion-charger-1a-with-li-ion-protection-circuit',
    'ROBU': 'https://probots.co.in/tp4056-1a-li-ion-lithium-battery-charging-module-with-current-protection-type-c.html',
    'GCT': 'https://gct.co/files/drawings/usb4105.pdf',
    'USBC': 'https://www.usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf',
    'MICROB': 'https://git.nefarius.at/nefarius/USB-Bluetooth-Specs/media/branch/master/usb_20_0702115/Micro-USB_final/Micro-USB_1_01.pdf',
    'POL': 'https://www.pololu.com/product/2562',
    'VIMEX': 'http://vimex.com/switches/techdocs/SS12D00-tech.pdf',
    'SS12_LCSC': 'https://atta.szlcsc.com/upload/public/pdf/source/20240529/1037A069FE9BBCECE56007AB916D4384.pdf',
    'OMRON': 'https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3f.pdf',
    'PANA': 'https://sy-dep-epc-lpc.web.cern.ch/components/datasheets/epc-lpc%20(converters)/FR-A-Electrolytic-Capacitor-(PANASONIC).pdf',
    'VISHAY': 'https://www.vishay.com/docs/88525/1n5817.pdf',
    'ADA26': 'https://www.adafruit.com/product/1877',
    'ADA30': 'https://www.adafruit.com/product/2051',
    'JST_DK': 'https://www.digikey.com/en/products/detail/jst-sales-america-inc/B2B-PH-K-S-LF-SN/926611',
    'JST_FE': 'https://www.futureelectronics.com/p/interconnect--connectors-pcb--header-plug-board-mount/b2b-ph-k-s-lf-sn-jst-6306179',
    'JST_RS': 'https://uk.rs-online.com/web/p/wire-housings-plugs/8201466',
    'ACF': 'https://www.albanycountyfasteners.com/media/64/3d/5a/1764619189/heat-set-insert-specs.pdf',
    'SONY': 'https://helpguide.sony.net/ilc/2020/v1/en/contents/TP1000156794.html',
    'RICOH': 'https://theta-archive.ricoh360.com/topics.theta360.com/en/faq/c_02_x/2206/',
    'BAMBU': 'https://www.additive-x.com/shop/mpattachments/file/viewonline/id/494/product_id/2236',
    'OE': 'https://www.open-electronics.org/a-i-thinker-esp32-cam-affrodable-esp32-camera-development-board-by-seeed-studio/',
}

M = {
    # ESP32-CAM + MB (gjenbrukt frå delmaal.json / parametrar.json)
    'stabel_L': 40.5,      # CAM 40,5 ±0,2 nominelt, målt 40,1–40,35; MB 39–40 [DM]
    'stabel_W': 27.3,      # 27,0 ±0,2 nominelt, målt 27,2–27,25 [DM]
    'kropp_til_mb': 17.5,  # 22 (linsetopp->MB-underside, maks av 18–22) - 4,5 (kamerakropp-topp over CAM-PCB, anslått) [DM][PAR]
    'linse_over_kropp': 4.5,  # linsetopp 9,0 (6,6–9,0) over PCB minus 4,5 [DM][PAR]
    'linse_d': 7.92,       # 7,1–7,92 [DM]
    'linse_L': 9.5,        # frå SD-enden, 8,0–10,6, typisk 9,5 [DM]
    'linse_W': 13.65,      # sentrert, 13,5–14,25 frå 5V-kanten [DM]
    'loddesone': 3.0,      # 1–2 mm loddespissar [DM] + A2 loddeklaring 2,5 [PAR] -> 3,0 = leidningskanal-regelen
    'frigang_front': 0.5,  # A2 frigang 0,5 [PAR] (kamerakropp-toppen er anslått)
    'sd_W0': 5.4, 'sd_W1': 21.7, 'sd_h': 2.3,   # SD-sokkel på tvers og høgd [DM]
    'pad_L': 8.39, 'pad_W': 2.07,  # midt mellom pad 1–4 (4,58–12,20 frå SD-enden), 2,07 frå langkant [DM]
    'antenne_L': 6.218,    # ANT-sone i antenneenden [DM]
    'blits_L': 30.1, 'blits_W': 24.75,  # 29,4–30,8 frå SD-enden, 24,5–25 frå 5V-kanten [DM]
    'mbusb_over_mb': 3.1,  # A2 [PAR] (Printables: 1,3–3,8 over MB-undersida [DM])
    'microb_kappe': (10.6, 8.5),  # maks [DM/MICROB]
    # Celle EEMB LP603448-PCM-LD
    'celle_L': 50.0, 'celle_W': 34.5, 'celle_T': 6.3,  # maks [EEMB_PCM]
    'svell': 1.10,          # +10 % tjukn (krav)
    'skum': 0.5,            # skumpute (krav)
    'leidningssone': 3.0,   # leidningar ut av kortsida + bøyeradius (3 mm-regelen)
    'skiljeplate': 1.0,     # eige val: heil PLA-plate mellom MB-loddespissar og posen
    # TP4056 USB-C-modul
    'tp_L': 29.0, 'tp_W': 17.3, 'tp_H': 4.3,  # AZ-Delivery 29 x 17,3 x 4,3 (spenn 25–29 x 17–19 x 4,0–4,3)
    'tp_wire': 3.0,         # puter B+/B-/OUT+/OUT- i enden motsett USB-C [ROBU] + 3 mm leidningssone
    'usbc_kappe': (12.35, 6.5),  # maks kappe [USBC via DM]
    'usbc_skal': (8.25, 2.40),   # pluggskal [USBC via DM]
    'usbc_rec_h': 3.31, 'usbc_rec_w': 8.94,  # GCT USB4105 (referanse) [GCT]
    'usbc_kappe_avstand_min': 1.85,  # GCT parringsvising: kappa står >= 1,85 frå kontaktfronten [GCT]
    # Pololu U1V11F5
    'bo_L': 15.2, 'bo_W': 11.4, 'bo_H': 2.5,  # [POL]; pinnar langs 11,4-kanten
    'bo_wire': 3.0, 'bo_wire_h': 1.5,         # leidningssone + leidningstjukn 26 AWG (1,4–1,5) [ADA26]
    # SS-12D00G3
    'sw_L': 8.8, 'sw_W': 3.9,   # 8,5 x 3,5 (Vimex) / 8,8 x 3,9 (LCSC) -> maks
    'sw_kropp_h': 3.5, 'sw_topp_til_pinne': 7.2, 'sw_spak': 3.0, 'sw_spak_b': 1.5, 'sw_vandring': 2.0,
    'sw_wire': 2.0, 'sw_pinne_klipt': 2.0,  # eige val: pinnane klipte til 2,0 mm under kroppen før lodding (30 AWG)
    # Utløysar
    'b3f_s': 6.0, 'b3f_h1000': 4.3, 'b3f_h1020': 5.0, 'b3f_stempel': 3.5, 'b3f_bein': 3.4,
    'b12_s': 12.0, 'b12_h': 7.3, 'b12_hette': (13.0, 8.0),
    'hette_flens': 11.0, 'hette_flens_t': 0.8,  # eige val: printa utløysarhette med flens inne
    # Kondensator EEU-FR1A471 (10 V)
    'c_d': 8.5, 'c_l': 13.0, 'c_bein': 2.0,     # Ø8,0±0,5 x 11,5±1,5 [PANA] + bøyde bein
    # 1N5817
    'd_d': 2.7, 'd_l': 5.2, 'd_bein': 2.0, 'krymp': 0.25,  # [VISHAY]
    # JST-PH-overgang (B2B-PH-K-S + PHR-2)
    'jst_w': 6.0, 'jst_t': 4.5, 'jst_mated': 8.0, 'jst_post': 3.4, 'jst_bend': 3.0,  # [JST_DK][JST_FE][JST_RS]
    # Stativinnsats 1/4"-20
    'stativ_hol': 8.2, 'stativ_od': 9.53, 'stativ_lengd': 9.5, 'stativ_boss': 13.5,  # [ACF]
    # Skal
    'vegg': 2.0, 'vegg_flat': 1.6, 'klaring': 0.3,
    'pla_rho': 1.24,  # g/cm3 [BAMBU]
    # Masse
    'm_cam': 10.0, 'm_mb': (6.0, 10.0), 'm_celle': (17.0, 21.0), 'm_boost': 0.7, 'm_b3f': 0.25, 'm_b12': 0.85,
}

C = M['klaring']
T_CELL = round(M['celle_T'] * M['svell'], 3)  # 6.93
BATT_T = M['skum'] + T_CELL                   # 7.43
SEP_T = M['skiljeplate']
STACK_D = M['kropp_til_mb']                   # 17.5
LODD = M['loddesone']
FRONT = M['frigang_front']

# ---------------------------------------------------------------------------
# 2. BOKSHJELP
# ---------------------------------------------------------------------------

def B(lo, hi):
    return np.array([lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]], dtype=float)


def size(b):
    return b[3:] - b[:3]


def overlap_any(cands, P, G):
    """cands (n,6), P (m,6), G (m,) gap. Returns (n,) bool: conflicts with any."""
    if len(P) == 0:
        return np.zeros(len(cands), bool)
    a = cands[:, None, :]
    b = P[None, :, :]
    g = G[None, :, None]
    ov = np.all((a[..., :3] < b[..., 3:] + g - 1e-4) & (b[..., :3] < a[..., 3:] + g - 1e-4), axis=-1)
    return ov.any(axis=1)


def boxes_overlap(a, b, gap=0.0):
    return bool(np.all((a[:3] < b[3:] + gap - 1e-4) & (b[:3] < a[3:] + gap - 1e-4)))


def box_gap(a, b):
    """Minste avstand mellom to boksar (0 ved overlapp)."""
    d = np.maximum(0, np.maximum(a[:3] - b[3:], b[:3] - a[3:]))
    return float(np.linalg.norm(d))


AX = {'x': 0, 'y': 1, 'z': 2}
AXN = 'xyz'

# ---------------------------------------------------------------------------
# 3. SMÅKOMPONENTAR (lokale mål; akse 0 er «funksjonsaksen»)
#    port: retning på flata som skal ut til veggen (-1 = lokal min-flate på akse 0)
# ---------------------------------------------------------------------------

def small_specs(variant):
    S = {}
    S['tp4056'] = dict(dims=(M['tp_L'] + M['tp_wire'], M['tp_W'], M['tp_H']), port=True,
                       tekst='TP4056 USB-C-ladar (29 x 17,3 x 4,3 + 3 mm leidningssone ved B+/B-/OUT-putene)')
    S['boost'] = dict(dims=(M['bo_L'] + M['bo_wire'], M['bo_W'], M['bo_H'] + M['bo_wire_h']), port=False,
                      tekst='Pololu U1V11F5 (11,4 x 15,2 x 2,5 + 3 mm leidningssone ved pinnane + 1,5 leidningstjukn)')
    if variant.get('brytar_klipt'):
        S['brytar'] = dict(dims=(M['sw_kropp_h'] + M['sw_pinne_klipt'] + 1.0, M['sw_L'], M['sw_W']), port=True,
                           tekst='SS-12D00G3 med pinnane klipte til 2,0 mm (kropp 3,5 + 2,0 + 1,0 leidning = 6,5), spaken gjennom veggen')
    else:
        S['brytar'] = dict(dims=(M['sw_topp_til_pinne'] + M['sw_wire'], M['sw_L'], M['sw_W']), port=True,
                           tekst='SS-12D00G3 skyvebrytar (8,8 x 3,9; 7,2 topp->pinnespiss + 2 mm leidning), spaken gjennom veggen')
    if variant.get('knapp', 'b3f') == 'b12':
        h = M['b12_h'] + 1.0 + 0.0
        S['utloysar'] = dict(dims=(h, 13.0, 13.0), port=True,
                             tekst='12x12x7,3 taktil (B3F-4050-klassen) + bøyde bein 1,0; Ø13-hetta går gjennom toppveggen')
    else:
        h = M['b3f_h1000'] + 1.0 + M['hette_flens_t']
        S['utloysar'] = dict(dims=(h, M['hette_flens'], M['hette_flens']), port=True,
                             tekst='6x6x4,3 taktil (B3F-1000) + bøyde bein 1,0 + printa hette med Ø11 x 0,8 flens inne')
    S['kondensator'] = dict(dims=(M['c_l'] + M['c_bein'], M['c_d'], M['c_d']), port=False,
                            tekst='470 µF/10 V EEU-FR1A471 (Ø8,5 x 13,0 maks) + 2 mm bøyde bein')
    dl = M['d_l'] + 2 * M['d_bein']
    S['diode'] = dict(dims=(dl, M['d_d'] + 2 * M['krymp'], M['d_d'] + 2 * M['krymp']), port=False,
                      tekst='1N5817 (Ø2,7 x 5,2) i krympestrømpe, bøyde bein')
    if variant.get('jst'):
        S['jst'] = dict(dims=(M['jst_mated'] + M['jst_post'] + 1.0 + M['jst_bend'], M['jst_w'], M['jst_t']), port=False,
                        tekst='JST-PH-overgang: B2B-PH-K-S med leidningar lodda på stiftene + PHR-2 frå cella (8,0 parra høgd + 3,4 stift + 1,0 lodd + 3,0 bøy)')
    if variant.get('stativ'):
        S['stativ'] = dict(dims=(M['stativ_lengd'] - M['vegg'] + 1.0, M['stativ_boss'], M['stativ_boss']), port=True,
                           tekst='1/4"-20 innsmeltingsmutter (hol 8,2, OD 9,53, lengd 9,5) i boss Ø13,5; munnen i botnflata')
    return S


ORDER = ['tp4056', 'utloysar', 'brytar', 'stativ', 'kondensator', 'boost', 'jst', 'diode']

# ---------------------------------------------------------------------------
# 4. STORE DELAR
# ---------------------------------------------------------------------------

def stack_local_to_global(st, l, w):
    """st: dict(La, sL, Wa, sW, p (y,z-min-hjørne som array len 3)). Returnerer (y,z)-koordinat i global array."""
    g = np.zeros(3)
    La, Wa = st['La'], st['Wa']
    g[La] = st['lo'][La] + (l if st['sL'] > 0 else M['stabel_L'] - l)
    g[Wa] = st['lo'][Wa] + (w if st['sW'] > 0 else M['stabel_W'] - w)
    return g


def battery_group(arch, cav, cell_o, anchor):
    """Lagar skum, celle, leidningssone og skiljeplate.
    arch: 'x-' | 'y-' | 'z-' | 'z+' (veggen cella ligg mot = lokket)
    cell_o: (La, sign_lead) La = global akse for cellelengda; sign_lead = -1 leidningar ved min-enden
    anchor: dict akse->min-koordinat for celle+leidningssone-gruppa i planet
    """
    X = cav
    ta = {'x-': 0, 'y-': 1, 'z-': 2, 'z+': 2}[arch]
    tsign = -1 if arch.endswith('-') else +1
    La, sl = cell_o
    inplane = [a for a in range(3) if a != ta]
    Wa = [a for a in inplane if a != La][0]
    grp_len = M['celle_L'] + M['leidningssone']
    parts = {}
    # langs tjukna
    if tsign < 0:
        f0, f1 = 0.0, M['skum']
        c0, c1 = f1, f1 + T_CELL
        s0, s1 = c1, c1 + SEP_T
    else:
        f1, f0 = cav[ta], cav[ta] - M['skum']
        c1, c0 = f0, f0 - T_CELL
        s1, s0 = c0, c0 - SEP_T
    lo = np.zeros(3); hi = np.zeros(3)
    p = anchor[La]
    if sl < 0:
        lz = (p, p + M['leidningssone']); ce = (p + M['leidningssone'], p + grp_len)
    else:
        ce = (p, p + M['celle_L']); lz = (p + M['celle_L'], p + grp_len)
    w0 = anchor[Wa]; w1 = w0 + M['celle_W']

    def mk(t0, t1, l0, l1, ww0, ww1):
        lo = np.zeros(3); hi = np.zeros(3)
        lo[ta], hi[ta] = t0, t1
        lo[La], hi[La] = l0, l1
        lo[Wa], hi[Wa] = ww0, ww1
        return B(lo, hi)
    parts['celle'] = mk(c0, c1, ce[0], ce[1], w0, w1)
    parts['skum'] = mk(f0, f1, ce[0], ce[1], w0, w1)
    parts['leidningssone'] = mk(min(f0, c0), max(f1, c1), lz[0], lz[1], w0, w1)
    # skiljeplata dekkjer cella + 0,3 rundt (ikkje leidningssona: der går leidningane fram)
    sl0 = max(0.0, ce[0] - C); sl1 = min(cav[La], ce[1] + C)
    if sl < 0:
        sl0 = ce[0]
    else:
        sl1 = ce[1]
    sw0 = max(0.0, w0 - C); sw1 = min(cav[Wa], w1 + C)
    parts['skiljeplate'] = mk(s0, s1, sl0, sl1, sw0, sw1)
    meta = dict(ta=ta, tsign=tsign, La=La, Wa=Wa, sl=sl, lead_end=(lz[0] if sl < 0 else lz[1]))
    return parts, meta


def stack_parts(cav, st):
    X = cav[0]
    lo = st['lo'].copy()
    L, W = M['stabel_L'], M['stabel_W']
    body_lo = lo.copy(); body_hi = lo.copy()
    body_lo[0] = X - FRONT - STACK_D; body_hi[0] = X - FRONT
    body_hi[st['La']] = lo[st['La']] + L
    body_hi[st['Wa']] = lo[st['Wa']] + W
    body = B(body_lo, body_hi)
    lod = body.copy(); lod[0] = X - FRONT - STACK_D - LODD; lod[3] = X - FRONT - STACK_D
    parts = {'stabel': body, 'loddesone': lod}
    # SD-kanal frå SD-enden til veggen (framste 2,6 mm av stabelsona: CAM-PCB-front .. +2,6)
    La, Wa = st['La'], st['Wa']
    sd = np.zeros(6)
    pcb_front = X - FRONT - M['linse_over_kropp'] * 0 - 4.5  # CAM-PCB-fronten: kamerakroppen er 4,5 høg
    sd[0] = pcb_front; sd[3] = pcb_front + M['sd_h'] + C
    a = stack_local_to_global(st, 0.0, M['sd_W0'] - C)
    b = stack_local_to_global(st, 0.0, M['sd_W1'] + C)
    sd[Wa] = min(a[Wa], b[Wa]); sd[Wa + 3] = max(a[Wa], b[Wa])
    sdend = stack_local_to_global(st, 0.0, 0.0)[La]
    if st['sL'] > 0:  # SD-enden på min-sida
        sd[La] = 0.0; sd[La + 3] = sdend
    else:
        sd[La] = sdend; sd[La + 3] = cav[La]
    if sd[La + 3] - sd[La] > 1e-6:
        parts['sd_kanal'] = sd
    return parts


# ---------------------------------------------------------------------------
# 5. KLARINGSREGLAR
# ---------------------------------------------------------------------------
ZONES = {'loddesone', 'leidningssone', 'sd_kanal'}
ZERO_PAIRS = {frozenset(p) for p in [('stabel', 'loddesone'), ('loddesone', 'skiljeplate'), ('skiljeplate', 'celle'),
                                       ('celle', 'skum'), ('celle', 'leidningssone'), ('skum', 'leidningssone'),
                                       ('skiljeplate', 'leidningssone'), ('stabel', 'sd_kanal'), ('skiljeplate', 'skum')]}


def pair_gap(a, b):
    if a == 'kanal' or b == 'kanal':
        return 0.0
    if a in ZONES or b in ZONES:
        return 0.0
    if frozenset((a, b)) in ZERO_PAIRS:
        return 0.0
    if 'skiljeplate' in (a, b):
        return 0.0  # plata er ein del av innmatsramma; komponentar kan liggje an mot ho
    return C


def wall_ok(name, b, cav, lid_axis, lid_sign):
    lo = np.full(3, C); hi = cav - C
    if name in ZONES or name == 'skiljeplate':
        lo = np.zeros(3); hi = cav.copy()
    if name == 'stabel':
        hi = hi.copy(); hi[0] = cav[0] - FRONT
    if name in ('skum', 'celle', 'leidningssone'):
        lo = lo.copy(); hi = hi.copy()
        if lid_sign < 0:
            lo[lid_axis] = 0.0
        else:
            hi[lid_axis] = cav[lid_axis]
    if name in ('leidningssone',):
        lo = np.zeros(3); hi = cav.copy()
    return bool(np.all(b[:3] >= lo - 1e-6) and np.all(b[3:] <= hi + 1e-6))


# ---------------------------------------------------------------------------
# 6. ORIENTERINGAR FOR SMÅDELAR
# ---------------------------------------------------------------------------
PERMS = list(itertools.permutations(range(3)))


def orientations(dims):
    out = []
    for p in PERMS:
        sz = np.zeros(3)
        for i in range(3):
            sz[p[i]] = dims[i]
        for s0 in (+1, -1):
            out.append((p, s0, sz))
    return out


def port_dir(p, s0):
    """Global retning (akse, forteikn) for lokal min-flate på akse 0."""
    return p[0], -s0


# ---------------------------------------------------------------------------
# 7. LEIDNINGSRUTING
# ---------------------------------------------------------------------------

def seg_box(a, b, w):
    lo = np.minimum(a, b) - w / 2
    hi = np.maximum(a, b) + w / 2
    return B(lo, hi)


def path_boxes(pts, w):
    return [seg_box(pts[i], pts[i + 1], w) for i in range(len(pts) - 1) if np.linalg.norm(pts[i + 1] - pts[i]) > 1e-9]


def manhattan(p, q, order):
    pts = [p.copy()]
    cur = p.copy()
    for ax in order:
        nxt = cur.copy(); nxt[ax] = q[ax]
        pts.append(nxt); cur = nxt
    return pts


def route(p, q, w, obstacles, cav, waypoints):
    """Finn ein Manhattan-kanal frå p til q. obstacles: liste av boksar."""
    O = np.array(obstacles) if obstacles else np.zeros((0, 6))

    def free(boxes):
        for bx in boxes:
            # innanfor hola (kanalen kan liggje an mot veggen)
            if np.any(bx[:3] < -1e-6) or np.any(bx[3:] > cav + 1e-6):
                # klem kanalen inn mot veggen: leidningar kan liggje inntil veggen
                bx = bx.copy(); bx[:3] = np.maximum(bx[:3], 0); bx[3:] = np.minimum(bx[3:], cav)
            if len(O) and np.any(np.all((bx[None, :3] < O[:, 3:] - 1e-3) & (O[:, :3] < bx[None, 3:] - 1e-3), axis=1)):
                return False
        return True

    for order in PERMS:
        pts = manhattan(p, q, order)
        bxs = path_boxes(pts, w)
        if free(bxs):
            return pts
    for wp in waypoints:
        for o1 in PERMS:
            pts1 = manhattan(p, wp, o1)
            if not free(path_boxes(pts1, w)):
                continue
            for o2 in PERMS:
                pts2 = manhattan(wp, q, o2)
                if free(path_boxes(pts2, w)):
                    return pts1 + pts2[1:]
    return None



WIRE_END = {'tp4056': M['tp_wire'], 'boost': M['bo_wire'], 'brytar': M['sw_wire'], 'utloysar': 1.0,
            'kondensator': M['c_bein']}


def body_and_zones(name, b, ori):
    """Del ein smådel i kropp (hinder for leidningar) og leidningssoner (fritt for leidningar)."""
    p, s0 = ori
    a = p[0]
    if name == 'diode':
        return None, [b]  # dioden sit i leidningsbunten
    if name == 'stativ':
        return b, []
    if name == 'jst':
        z1 = b.copy(); z2 = b.copy(); body = b.copy()
        e_top = M['jst_bend']; e_bot = M['jst_post'] + 1.0
        if s0 > 0:
            z1[a] = b[a + 3] - e_top; z2[a + 3] = b[a] + e_bot
            body[a] = b[a] + e_bot; body[a + 3] = b[a + 3] - e_top
        else:
            z1[a + 3] = b[a] + e_top; z2[a] = b[a + 3] - e_bot
            body[a] = b[a] + e_top; body[a + 3] = b[a + 3] - e_bot
        return body, [z1, z2]
    e = WIRE_END[name]
    z = b.copy(); body = b.copy()
    if s0 > 0:
        z[a] = b[a + 3] - e; body[a + 3] = b[a + 3] - e
    else:
        z[a + 3] = b[a] + e; body[a] = b[a] + e
    return body, [z]

# Maks leidningslengd per nett (eige val, frå «korte, tjukke leidningar» [MG] og «så kort som mogleg» for C1):
MAXLEN = {'kondensator->MB5V': 25.0, 'diode->MB5V': 40.0, 'boost->diode': 40.0, 'tp4056->boost': 80.0,
          'celle->tp4056': 95.0, 'celle->jst': 95.0, 'jst->tp4056': 80.0, 'brytar->boost(SHDN)': 90.0,
          'utloysar->MB(IO13)': 90.0}


def path_len(pts):
    return float(sum(np.linalg.norm(np.array(pts[i + 1]) - np.array(pts[i])) for i in range(len(pts) - 1)))


GRID_H = 1.0


def grid_route(p, q, w, bodies, unblock, cav, h=GRID_H):
    """BFS på eit 1 mm-rutenett. Kanalen sin senterline må halde w/2 frå hinder (obst_dil);
    obst_nodil (eigarane av endepunkta) blir berre sperra i sjølve kroppen. Returnerer punktliste eller None."""
    n = np.maximum(1, np.ceil(cav / h - 1e-9).astype(int))
    cs = [(np.arange(n[k]) + 0.5) * h for k in range(3)]
    blocked = np.zeros(tuple(n), bool)
    m = w / 2.0

    def mark(b, mm):
        sl = []
        for k in range(3):
            i0 = np.searchsorted(cs[k], b[k] - mm + 1e-6, side='left')
            i1 = np.searchsorted(cs[k], b[k + 3] + mm - 1e-6, side='right')
            if i1 <= i0:
                return
            sl.append(slice(i0, i1))
        blocked[tuple(sl)] = True
    # 1) alle kroppar med w/2 rundt
    for b in bodies:
        mark(b, m)
    # 2) bunten må liggje inne i hola: senterlinja minst w/2 (-0,25 toleranse) frå veggane
    for k in range(3):
        bad = (cs[k] < m - 0.25) | (cs[k] > cav[k] - m + 0.25)
        idx = [slice(None)] * 3; idx[k] = bad
        blocked[tuple(idx)] = True
    # 3) opne leidningssoner (loddesone, leidningssone, endepunkta sine utgangar)
    for b in unblock:
        sl = []
        ok = True
        for k in range(3):
            i0 = np.searchsorted(cs[k], b[k] - 1e-6, side='left')
            i1 = np.searchsorted(cs[k], b[k + 3] + 1e-6, side='right')
            if i1 <= i0:
                ok = False; break
            sl.append(slice(i0, i1))
        if ok:
            blocked[tuple(sl)] = False
    # 4) kroppane sjølve er alltid sperra
    for b in bodies:
        mark(b, 0.0)
    pi = tuple(np.clip((p / h).astype(int), 0, n - 1))
    qi = tuple(np.clip((q / h).astype(int), 0, n - 1))
    if blocked[pi] or blocked[qi]:
        # endepunktet kan liggje på kanten av eit hinder: opna sjølve voxelen
        blocked[pi] = False; blocked[qi] = False
    free = ~blocked
    dist = np.full(tuple(n), -1, dtype=np.int32)
    dist[pi] = 0
    front = np.zeros(tuple(n), bool); front[pi] = True
    d = 0
    while True:
        if dist[qi] >= 0:
            break
        nf = np.zeros_like(front)
        nf[1:, :, :] |= front[:-1, :, :]; nf[:-1, :, :] |= front[1:, :, :]
        nf[:, 1:, :] |= front[:, :-1, :]; nf[:, :-1, :] |= front[:, 1:, :]
        nf[:, :, 1:] |= front[:, :, :-1]; nf[:, :, :-1] |= front[:, :, 1:]
        nf &= free & (dist < 0)
        if not nf.any():
            return None
        d += 1
        dist[nf] = d
        front = nf
    # tilbakespor frå q, føretrekk same retning
    path = [qi]
    cur = qi; last = None
    dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    while dist[cur] > 0:
        order = ([last] if last else []) + [dd for dd in dirs if dd != last]
        for dd in order:
            nb = (cur[0] + dd[0], cur[1] + dd[1], cur[2] + dd[2])
            if all(0 <= nb[k] < n[k] for k in range(3)) and dist[nb] == dist[cur] - 1:
                cur = nb; last = dd; path.append(nb)
                break
    path = path[::-1]
    pts = [np.array([(i + 0.5) * h for i in v]) for v in path]
    pts[0] = p.copy(); pts[-1] = q.copy()
    # fjern kolineære punkt
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a = pts[i] - out[-1]; b = pts[i + 1] - pts[i]
        if np.linalg.norm(np.cross(a, b)) > 1e-9:
            out.append(pts[i])
    out.append(pts[-1])
    # gjer alle segment akseparallelle (endepunkta kan vere off-grid): flytt éin akse om gongen
    fixed = [out[0]]
    for pt in out[1:]:
        cur = fixed[-1].copy()
        for ax in np.argsort(-np.abs(pt - cur)):
            if abs(pt[ax] - cur[ax]) > 1e-9:
                cur = cur.copy(); cur[ax] = pt[ax]
                fixed.append(cur)
    # fjern dublettar
    ded = [fixed[0]]
    for pt in fixed[1:]:
        if np.linalg.norm(pt - ded[-1]) > 1e-9:
            ded.append(pt)
    fixed = ded
    return fixed


# ---------------------------------------------------------------------------
# 8. SØK
# ---------------------------------------------------------------------------
class Searcher:
    def __init__(self, spec):
        self.spec = spec
        self.S = small_specs(spec)
        self.names = [n for n in ORDER if n in self.S]
        self.nodes = 0

    # ---------- store delar ----------
    def big_configs(self, cav):
        sp = self.spec
        arch = sp['arch']
        ta = {'x-': 0, 'y-': 1, 'z-': 2, 'z+': 2}[arch]
        tsign = -1 if arch.endswith('-') else +1
        out = []
        inplane = [a for a in range(3) if a != ta]
        for La in inplane:
            if sp.get('cell_La') is not None and La != sp['cell_La']:
                continue
            Wa = [a for a in inplane if a != La][0]
            for sl in (-1, +1):
                gl = M['celle_L'] + M['leidningssone']
                if gl > cav[La] - 1e-6 or M['celle_W'] + 2 * C > cav[Wa] + 1e-6:
                    continue
                # ankre langs La: leidningssona kan gå heilt til veggen (gap 0), cella 0,3 frå veggen
                candL = set()
                if sl < 0:
                    candL |= {0.0, cav[La] - C - gl}
                else:
                    candL |= {C, cav[La] - gl}
                candW = {C, cav[Wa] - C - M['celle_W']}
                for pl in candL:
                    for pw in candW:
                        if pl < -1e-6 or pw < C - 1e-6:
                            continue
                        anc = np.zeros(3); anc[La] = pl; anc[Wa] = pw
                        parts, meta = battery_group(arch, cav, (La, sl), anc)
                        if not all(wall_ok(n, b, cav, ta, tsign) for n, b in parts.items()):
                            continue
                        out.append((parts, meta))
        return out

    def stack_configs(self, cav, bparts):
        sp = self.spec
        res = []
        for La in (1, 2):
            if sp.get('stack_La') is not None and La != sp['stack_La']:
                continue
            Wa = 3 - La
            for sL in (+1, -1):
                if sp.get('stack_sL') is not None and sL != sp['stack_sL']:
                    continue
                for sW in (+1, -1):
                    # ankre: USB-enden (lokal L = 40,5) skal stå 0,3 frå ein vegg
                    usb_at_max = (sL > 0)
                    lo = np.zeros(3)
                    candL = [cav[La] - C - M['stabel_L']] if usb_at_max else [C]
                    candW = set([C, cav[Wa] - C - M['stabel_W']])
                    # i tillegg: kant mot skiljeplata/cella for golv/sidearkitektur
                    for b in bparts.values():
                        candW |= {b[Wa + 3] + C, b[Wa] - C - M['stabel_W']}
                    for pl in candL:
                        for pw in candW:
                            if pw < C - 1e-6 or pw + M['stabel_W'] > cav[Wa] - C + 1e-6:
                                continue
                            lo = np.zeros(3); lo[La] = pl; lo[Wa] = pw
                            st = dict(La=La, Wa=Wa, sL=sL, sW=sW, lo=lo)
                            parts = stack_parts(cav, st)
                            if parts['loddesone'][0] < -1e-6:
                                continue
                            ok = all(wall_ok(n, b, cav, 0, -1) or n in ZONES for n, b in parts.items())
                            if not ok:
                                continue
                            bad = False
                            for n1, b1 in parts.items():
                                for n2, b2 in bparts.items():
                                    if boxes_overlap(b1, b2, pair_gap(n1, n2)):
                                        bad = True; break
                                if bad:
                                    break
                            if bad:
                                continue
                            if not self.check_stack_constraints(cav, st, parts, bparts):
                                continue
                            res.append((st, parts))
        return res

    def check_stack_constraints(self, cav, st, sparts, bparts):
        sp = self.spec
        lens = stack_local_to_global(st, M['linse_L'], M['linse_W'])
        if sp.get('lens_z_max_frac') is not None and lens[2] > sp['lens_z_max_frac'] * cav[2] + 1e-6:
            return False
        if sp.get('no_cell_behind_antenna'):
            a0 = stack_local_to_global(st, M['stabel_L'] - M['antenne_L'], 0)
            a1 = stack_local_to_global(st, M['stabel_L'], M['stabel_W'])
            ant = np.zeros(6)
            ant[:3] = np.minimum(a0, a1); ant[3:] = np.maximum(a0, a1)
            ant[0] = 0; ant[3] = cav[0]
            if boxes_overlap(ant, bparts['celle'], 0.0):
                return False
        if sp.get('usb_end_axis_sign') is not None:
            ax, sg = sp['usb_end_axis_sign']
            usb = stack_local_to_global(st, M['stabel_L'], 0)
            if st['La'] != ax:
                return False
            at_max = abs(usb[ax] - (cav[ax] - C)) < 1e-6
            if (sg > 0) != at_max:
                return False
        return True

    # ---------- småkomponentar ----------
    def candidates(self, name, cav, placed, ctx):
        sp = self.spec
        dims = self.S[name]['dims']
        P = np.array([b for _, b in placed])
        G_names = [n for n, _ in placed]
        res = []
        lid_axis, lid_sign = ctx['lid']
        for (p, s0, sz) in orientations(dims):
            # portkrav
            pax, psg = port_dir(p, s0)
            fixed = {}
            if self.S[name]['port']:
                allowed = sp['ports'].get(name)
                if allowed is not None and (pax, psg) not in allowed:
                    continue
                fixed[pax] = C if psg < 0 else cav[pax] - C - sz[pax]
            else:
                if s0 < 0:  # forteiknet på akse 0 betyr berre noko for portdelar og leidningsende
                    pass
            axes_c = []
            for k in range(3):
                if k in fixed:
                    axes_c.append(np.array([fixed[k]]))
                    continue
                cs = {C, cav[k] - C - sz[k]}
                for (n, b) in placed:
                    if n == 'kanal':
                        continue
                    g = pair_gap(name, n)
                    cs.add(b[k + 3] + g)
                    cs.add(b[k] - g - sz[k])
                cs = np.array(sorted(cs))
                cs = cs[(cs >= C - 1e-6) & (cs + sz[k] <= cav[k] - C + 1e-6)]
                axes_c.append(cs)
            if any(len(a) == 0 for a in axes_c):
                continue
            g0, g1, g2 = np.meshgrid(*axes_c, indexing='ij')
            lo = np.stack([g0.ravel(), g1.ravel(), g2.ravel()], axis=1)
            cand = np.concatenate([lo, lo + sz[None, :]], axis=1)
            G = np.array([pair_gap(name, n) for n in G_names]) if len(G_names) else np.zeros(0)
            bad = overlap_any(cand, P, G)
            cand = cand[~bad]
            if len(cand) == 0:
                continue
            # spesialkrav
            cand = self.filter_special(name, cand, cav, ctx, (p, s0, sz))
            for c in cand:
                res.append((c, (p, s0)))
        return res

    def filter_special(self, name, cand, cav, ctx, ori):
        sp = self.spec
        p, s0, sz = ori
        if name == 'utloysar' and sp.get('shutter_z_min_frac') is not None:
            cz = (cand[:, 2] + cand[:, 5]) / 2
            cand = cand[cz >= sp['shutter_z_min_frac'] * cav[2]]
        if name == 'kondensator':
            pad = ctx['pad']
            d = np.linalg.norm(np.maximum(0, np.maximum(cand[:, :3] - pad, pad - cand[:, 3:])), axis=1)
            cand = cand[d <= sp.get('cap_max_dist', 12.0)]
            # beina (leidningsenden) skal peike mot padane, ikkje bort frå dei
            if len(cand):
                ax = p[0]
                wire_hi = (s0 > 0)
                endc = cand[:, ax + 3] if wire_hi else cand[:, ax]
                farc = cand[:, ax] if wire_hi else cand[:, ax + 3]
                cand = cand[np.abs(endc - pad[ax]) <= np.abs(farc - pad[ax]) + 1e-6]
        if name == 'stativ' and sp.get('stativ_z_band') is not None:
            cz = (cand[:, 2] + cand[:, 5]) / 2
            lo, hi = sp['stativ_z_band']
            cand = cand[(cz >= lo * cav[2]) & (cz <= hi * cav[2])]
        if name == 'boost' and sp.get('boost_not_on_cell'):
            cb = ctx['celle']
            d = np.array([box_gap(c, cb) for c in cand]) if len(cand) else np.zeros(0)
            cand = cand[d >= 1.0 - 1e-6] if len(cand) else cand
        return cand

    def score_all(self, name, cand, cav, placed, ctx):
        """Vektorisert: kontakt (flater mot vegg/nabo) og avstand til målpunkt."""
        contact = np.zeros(len(cand))
        for k in range(3):
            contact += (np.abs(cand[:, k] - C) < 1e-6)
            contact += (np.abs(cand[:, k + 3] - (cav[k] - C)) < 1e-6)
        for n, b in placed:
            if n == 'kanal':
                continue
            g = pair_gap(name, n)
            for k in range(3):
                o = [j for j in range(3) if j != k]
                ov = np.ones(len(cand), bool)
                for j in o:
                    ov &= (cand[:, j] < b[j + 3]) & (b[j] < cand[:, j + 3])
                touch = (np.abs(cand[:, k] - (b[k + 3] + g)) < 1e-6) | (np.abs(b[k] - (cand[:, k + 3] + g)) < 1e-6)
                contact += (ov & touch)
        centre = (cand[:, :3] + cand[:, 3:]) / 2
        tgt = ctx['targets'].get(name)
        dist = np.linalg.norm(centre - tgt, axis=1) if tgt is not None else np.zeros(len(cand))
        return -contact * self.spec.get('kontakt_vekt', 1000.0) + dist

    def terminal(self, name, b, ori, which='wire'):
        body, zones = body_and_zones(name, b, ori)
        if name == 'jst':
            zt = zones[0] if which == 'wire' else zones[1]
            return (zt[:3] + zt[3:]) / 2
        z = zones[0]
        return (z[:3] + z[3:]) / 2

    def net_defs(self):
        nets = []
        if 'jst' in self.S:
            nets += [('celle->jst', ('LEAD', None), ('jst', 'wire'), 3.0),
                     ('jst->tp4056', ('jst', 'port'), ('tp4056', 'wire'), 3.0)]
        else:
            nets += [('celle->tp4056', ('LEAD', None), ('tp4056', 'wire'), 3.0)]
        nets += [('tp4056->boost', ('tp4056', 'wire'), ('boost', 'wire'), 3.0),
                 ('boost->diode', ('boost', 'wire'), ('diode', 'wire'), 3.0),
                 ('diode->MB5V', ('diode', 'wire'), ('PAD', None), 3.0),
                 ('kondensator->MB5V', ('kondensator', 'wire'), ('PAD', None), 3.0),
                 ('brytar->boost(SHDN)', ('brytar', 'wire'), ('boost', 'wire'), 2.0),
                 ('utloysar->MB(IO13)', ('utloysar', 'wire'), ('PAD', None), 2.0)]
        return nets

    def term_point(self, ep, boxes, sol, ctx):
        n, which = ep
        if n == 'LEAD':
            return ctx['lead']
        if n == 'PAD':
            return ctx['pad']
        return self.terminal(n, boxes[n], sol[n], which)

    def route_net(self, net, cav, placed, ctx, sol):
        nm, a, b, w = net
        boxes = {n: bx for n, bx in placed if n != 'kanal'}
        p = self.term_point(a, boxes, sol, ctx).copy()
        q = self.term_point(b, boxes, sol, ctx).copy()
        owners = {a[0], b[0]}
        bodies, unblock = [], []
        for n, bx in placed:
            if n == 'kanal':
                continue
            if n in ('loddesone', 'leidningssone'):
                unblock.append(bx)
                continue
            if n in sol:
                body, zones = body_and_zones(n, bx, sol[n])
                if body is not None:
                    bodies.append(body)
                if n in owners:
                    pp, s0 = sol[n]
                    ax = pp[0]
                    for z in zones:
                        e = z.copy()
                        if n == 'diode':
                            e[ax] -= w / 2; e[ax + 3] += w / 2
                        else:
                            # utgangen peikar bort frå kroppen
                            if body is not None and z[ax] >= body[ax + 3] - 1e-6:
                                e[ax + 3] += w / 2
                            else:
                                e[ax] -= w / 2
                        unblock.append(e)
                elif n == 'diode':
                    bodies.append(bx)
            else:
                bodies.append(bx)  # store delar og sd_kanal
        return grid_route(p, q, w, bodies, unblock, cav)

    def dfs(self, i, cav, placed, ctx, sol, routes):
        self.nodes += 1
        if self.nodes > self.node_limit:
            return None
        if i == len(self.names):
            return (list(placed), dict(sol), dict(routes))
        name = self.names[i]
        cands = self.candidates(name, cav, placed, ctx)
        if not cands:
            return None
        arr = np.array([c for c, _ in cands])
        sc = self.score_all(name, arr, cav, placed, ctx)
        idx = np.argsort(sc, kind='stable')
        seen = []
        K = self.spec.get('K', 3)
        placed_names = set(n for n, _ in placed) | {'LEAD', 'PAD'}
        for ii in idx:
            c, ori = cands[ii]
            if any(np.allclose(c, s_) for s_ in seen):
                continue
            seen.append(c)
            if len(seen) > K:
                break
            placed.append((name, c)); sol[name] = ori
            # rut alle nett som no er komplette og involverer denne delen
            added = 0; new_routes = []
            ok = True
            pn = placed_names | {name}
            for net in self.net_defs():
                nm, a, b, w = net
                if nm in routes:
                    continue
                if a[0] in pn and b[0] in pn and name in (a[0], b[0]):
                    r = self.route_net(net, cav, placed, ctx, sol)
                    if r is not None and path_len(r) > MAXLEN.get(nm, 90.0):
                        r = None
                    if r is None:
                        ok = False
                        break
                    routes[nm] = dict(punkt=[list(map(float, x)) for x in r], breidd=w, lengd_mm=round(path_len(r), 1),
                                      maks_mm=MAXLEN.get(nm, 90.0))
                    new_routes.append(nm)
                    for bx in path_boxes(r, w):
                        bx = bx.copy(); bx[:3] = np.maximum(bx[:3], 0); bx[3:] = np.minimum(bx[3:], cav)
                        placed.append(('kanal', bx)); added += 1
            if ok:
                res = self.dfs(i + 1, cav, placed, ctx, sol, routes)
                if res is not None:
                    return res
            for _ in range(added):
                placed.pop()
            for nm in new_routes:
                routes.pop(nm, None)
            placed.pop(); sol.pop(name, None)
        return None

    # ---------- hovudløkke ----------
    def search(self, time_limit=600, node_limit=4000):
        sp = self.spec
        t0 = time.time()
        Xlo, Ylo, Zlo = sp['lo']
        rng = sp.get('range', (10, 14, 14))
        Xs = np.arange(Xlo, Xlo + rng[0] + 1e-6, ST)
        Ys = np.arange(Ylo, Ylo + rng[1] + 1e-6, ST)
        Zs = np.arange(Zlo, Zlo + rng[2] + 1e-6, ST)
        lid_ax = {'x-': 0, 'y-': 1, 'z-': 2, 'z+': 2}[sp['arch']]
        walls = np.array([M['vegg']] * 6)
        cavs = []
        for X in Xs:
            for Y in Ys:
                for Z in Zs:
                    out = self.outer_dims(np.array([X, Y, Z]))
                    cavs.append((out[0] * out[1] * out[2], X, Y, Z))
        cavs.sort()
        tried = 0
        for vol, X, Y, Z in cavs:
            if time.time() - t0 > time_limit:
                break
            cav = np.array([X, Y, Z])
            tried += 1
            if tried % 10 == 0:
                print(f"  ... {tried} hol, no {X:.1f} x {Y:.1f} x {Z:.1f}, {time.time() - t0:.0f} s", flush=True)
            for bparts, bmeta in self.big_configs(cav):
                for st, sparts in self.stack_configs(cav, bparts):
                    placed = list(bparts.items()) + list(sparts.items())
                    pad = stack_local_to_global(st, M['pad_L'], M['pad_W'])
                    pad[0] = (sparts['loddesone'][0] + sparts['loddesone'][3]) / 2
                    lead = (bparts['leidningssone'][:3] + bparts['leidningssone'][3:]) / 2
                    ctx = dict(lid=(bmeta['ta'], bmeta['tsign']), pad=pad, lead=lead, celle=bparts['celle'],
                               targets={'kondensator': pad, 'diode': pad, 'jst': lead})
                    # boost nær TP4056/pad: målet blir sett etter at TP4056 er plassert (forenkla: pad)
                    ctx['targets']['boost'] = pad
                    for tn, frac in sp.get('mal', {}).items():
                        ctx['targets'][tn] = cav * np.array(frac)
                    # rask førehandssjekk: kvar smådel må ha minst éin kandidat aleine
                    if any(len(self.candidates(n, cav, placed, ctx)) == 0 for n in self.names):
                        continue
                    self.nodes = 0
                    self.node_limit = node_limit
                    r = self.dfs(0, cav, placed, ctx, {}, {})
                    if r is not None:
                        placed_all, sol, routes = r
                        placed_all = [(n, b) for n, b in placed_all if n != 'kanal']
                        return dict(cav=cav, placed=placed_all, sol=sol, routes=routes, st=st, bmeta=bmeta,
                                    ctx=ctx, tried=tried, sekund=round(time.time() - t0, 1))
        return None

    def outer_dims(self, cav):
        sp = self.spec
        out = cav.copy().astype(float)
        lid = sp['arch']
        for k in range(3):
            lo_w = M['vegg']; hi_w = M['vegg']
            if lid == 'x-' and k == 0: lo_w = M['vegg_flat']
            if lid == 'y-' and k == 1: lo_w = M['vegg_flat']
            if lid == 'z-' and k == 2: lo_w = M['vegg_flat']
            if lid == 'z+' and k == 2: hi_w = M['vegg_flat']
            out[k] += lo_w + hi_w
        return out

    def wall_t(self):
        sp = self.spec
        lo = np.array([M['vegg']] * 3); hi = np.array([M['vegg']] * 3)
        lid = sp['arch']
        if lid == 'x-': lo[0] = M['vegg_flat']
        if lid == 'y-': lo[1] = M['vegg_flat']
        if lid == 'z-': lo[2] = M['vegg_flat']
        if lid == 'z+': hi[2] = M['vegg_flat']
        return lo, hi


# ---------------------------------------------------------------------------
# 9. KONTROLL AV FERDIG LØYSING (uavhengig av søket)
# ---------------------------------------------------------------------------

def verify(sol, spec):
    cav = sol['cav']
    placed = sol['placed']
    issues = []
    min_gap = {}
    for i in range(len(placed)):
        n1, b1 = placed[i]
        for j in range(i + 1, len(placed)):
            n2, b2 = placed[j]
            g = pair_gap(n1, n2)
            if boxes_overlap(b1, b2, g):
                issues.append(f'{n1} og {n2} bryt klaringa {g} mm')
            if n1 not in ZONES and n2 not in ZONES and g > 0:
                d = box_gap(b1, b2)
                min_gap[f'{n1}|{n2}'] = round(d, 3)
    # trimesh-kontroll: volum av snitt mellom alle par (skal vere 0 for ekte delar)
    tm_overlap = []
    real = [(n, b) for n, b in placed if n not in ZONES]
    for i in range(len(real)):
        for j in range(i + 1, len(real)):
            a = real[i][1]; b = real[j][1]
            lo = np.maximum(a[:3], b[:3]); hi = np.minimum(a[3:], b[3:])
            if np.all(hi - lo > 1e-4):
                ma = trimesh.creation.box(bounds=[a[:3], a[3:]])
                mb = trimesh.creation.box(bounds=[b[:3], b[3:]])
                try:
                    v = ma.intersection(mb).volume
                except Exception:
                    v = float(np.prod(hi - lo))
                if v > 1e-3 and frozenset((real[i][0], real[j][0])) not in ZERO_PAIRS:
                    tm_overlap.append((real[i][0], real[j][0], round(v, 3)))
    inside = all(np.all(b[:3] >= -1e-6) and np.all(b[3:] <= cav + 1e-6) for _, b in placed)
    small_gaps = {k: v for k, v in min_gap.items() if v < 1.0}
    return dict(problem=issues, trimesh_overlapp=tm_overlap, alt_innanfor_hola=bool(inside),
                minste_klaringar_under_1mm=dict(sorted(small_gaps.items(), key=lambda kv: kv[1])),
                minste_klaring_mm=(min(min_gap.values()) if min_gap else None))


# ---------------------------------------------------------------------------
# 10. LAYOUTAR
# ---------------------------------------------------------------------------
XLO = M['skum'] + T_CELL + SEP_T + LODD + STACK_D + FRONT  # 29.43
NOT_FRONT_NOT_BACK = [(1, -1), (1, +1), (2, -1), (2, +1)]

LAYOUTS = [
    dict(id=1, namn='L1 Minimum (sandwich, brute force)', arch='x-', lo=(XLO, 35.1, 53.3), range=(8, 10, 10),
         stack_La=None, cell_La=None, jst=False, knapp='b3f',
         ports={'tp4056': NOT_FRONT_NOT_BACK, 'brytar': NOT_FRONT_NOT_BACK, 'utloysar': [(1, +1)]},
         skildring='Minste ytre volum funne. Cella flatt bak MB, alt anna i dei to ledige stripene rundt stabelen. '
                   'Celleleidningane blir korta og lodda direkte på B+/B- (ingen JST).'),
    dict(id=2, namn='L2 Grep (sandwich, ergonomisk, JST)', arch='x-', lo=(XLO, 35.1, 53.3), range=(8, 10, 12),
         stack_La=2, stack_sL=+1, cell_La=2, jst=True, knapp='b3f', lens_z_max_frac=0.5, shutter_z_min_frac=0.6,
         K=3, nodes=1500, time=1700, brytar_klipt=True, kontakt_vekt=8.0, mal={'utloysar': (1.0, 1.0, 0.8)},
         ports={'tp4056': [(2, -1), (1, -1)], 'brytar': [(1, +1)], 'utloysar': [(1, +1)]},
         skildring='Liggjande format, linsa til venstre for midten (sett bakfrå), utløysar oppe til høgre, '
                   'straumbrytar oppe, USB-C på venstre side, programmerings-USB på høgre side. JST-plugg for cella.'),
    dict(id=3, namn='L3 Balanse/antenne/stativ (sandwich, JST, 1/4"-20)', arch='x-', lo=(XLO, 35.1, 53.3),
         range=(8, 12, 14), stack_La=2, stack_sL=+1, cell_La=2, jst=True, stativ=True, knapp='b3f',
         lens_z_max_frac=0.5, shutter_z_min_frac=0.6, no_cell_behind_antenna=True, K=3, nodes=1500, time=1700, brytar_klipt=True,
         mal={'utloysar': (1.0, 1.0, 0.8), 'brytar': (1.0, 1.0, 0.1), 'stativ': (0.5, 0.0, 0.5)},
         ports={'tp4056': [(2, -1), (1, -1)], 'brytar': [(1, +1)], 'utloysar': [(1, +1)], 'stativ': [(1, -1)]},
         skildring='Som L2, men cella står ikkje bak PCB-antenna (6,2 mm-sona), og det er plass til ein 1/4"-20-innsmeltingsmutter i botnen.'),
    dict(id=4, namn='L4 Botnluke (cella i golvet, djupt grep)', arch='y-', lo=(35.1, 36.0, 53.3),
         range=(12, 10, 12), stack_La=2, stack_sL=+1, cell_La=2, jst=True, knapp='b12', lens_z_max_frac=0.5,
         shutter_z_min_frac=0.6,
         ports={'tp4056': [(2, -1), (0, -1)], 'brytar': [(1, +1)], 'utloysar': [(1, +1)]},
         skildring='Cella ligg i golvet bak ei botnluke (som eit vanleg kamera). Djupare kropp gir betre grep og større utløysar (12x12).'),
    dict(id=5, namn='L5 Portrett (sandwich, ståande)', arch='x-', lo=(XLO, 53.3, 35.1), range=(8, 10, 10),
         stack_La=1, cell_La=1, jst=True, knapp='b3f',
         ports={'tp4056': [(1, -1), (2, -1), (2, +1)], 'brytar': [(2, +1), (2, -1), (1, +1)], 'utloysar': [(1, +1)]},
         skildring='Same volumklasse som L1, men ståande (smal og høg), med USB-C i botnen og utløysar på toppen.'),
]

COLORS = {
    'stabel': (40, 110, 200, 255), 'loddesone': (120, 170, 230, 90), 'celle': (210, 160, 40, 255),
    'skum': (250, 240, 200, 255), 'skiljeplate': (150, 150, 150, 160), 'leidningssone': (250, 120, 120, 90),
    'sd_kanal': (90, 220, 120, 90), 'tp4056': (30, 140, 60, 255), 'boost': (120, 60, 160, 255),
    'brytar': (30, 30, 30, 255), 'utloysar': (220, 50, 50, 255), 'kondensator': (20, 20, 120, 255),
    'diode': (60, 60, 60, 255), 'jst': (240, 240, 240, 255), 'stativ': (180, 180, 190, 255),
    'linse': (10, 10, 10, 255), 'skal': (230, 230, 225, 60), 'kanal': (255, 140, 0, 140),
    'opning': (255, 0, 200, 200),
}


# ---------------------------------------------------------------------------
# 11. ETTERARBEID: overflate, portar, masse, tyngdepunkt, eksport
# ---------------------------------------------------------------------------

def face_name(ax, sg):
    return {(0, 1): 'framside', (0, -1): 'bakside', (1, 1): 'topp', (1, -1): 'botn', (2, 1): 'høgre side', (2, -1): 'venstre side'}[(ax, sg)]


def build_features(res, spec, srch):
    """Overflatedetaljar med posisjon i YTRE koordinatar (origo i utvendig bak-botn-venstre hjørne,
    x fram, y opp, z til høgre sett bakfrå). Alle detaljar er funksjonelle (port, kontroll, lys, luft, grep, skøyt, feste)."""
    cav = res['cav']; st = res['st']
    wlo, whi = srch.wall_t()
    out = cav + wlo + whi
    boxes = dict(res['placed'])
    sol = res['sol']
    F = []
    X, Y, Z = cav

    def O(p):
        return [round(float(v), 1) for v in (np.array(p, dtype=float) + wlo)]

    def add(namn, flate, senter, mål, funksjon, **kw):
        d = dict(namn=namn, flate=flate, senter_mm=O(senter), mål_mm=mål, funksjon=funksjon)
        d.update(kw)
        F.append(d)

    La, Wa = st['La'], st['Wa']
    sgnL = 1 if st['sL'] > 0 else -1
    # --- FRAMSIDE -------------------------------------------------------
    lens = stack_local_to_global(st, M['linse_L'], M['linse_W']); lens[0] = X + whi[0]
    add('Objektivring og linsehol', 'framside', lens,
        'Hol Ø11,0 gjennom frontveggen (linseløp Ø7,1–7,92, linsa er handmontert ±1,5). Ring Ø16,0 ytre, står 3,0 fram frå frontflata. '
        'Innvendig 35°-kon frå linsetopp-planet ut til Ø12,4 i ringflata. Valfri 0,4 mm fas på ringkanten.',
        'Linsetoppen står 4,0 framom innsida av frontveggen (9,0 over CAM-PCB, design-maks). Ringa vernar linsa og gjer at heile kroppen kan vere 3 mm tynnare enn med flat front.',
        kjelde='delmaal.json (linse 6,6–9,0 over PCB, Ø7,1–7,92, 8,0–10,6 frå SD-enden), A2 parametrar.json (hol 11, 35° halvvinkel)')
    bl = stack_local_to_global(st, M['blits_L'], M['blits_W']); bl[0] = X + whi[0]
    add('Blitsvindauge', 'framside', bl, '5,4 x 5,2 opning, eller 0,6 mm restvegg i natur/kvit PLA som diffusor',
        'Kvit blits-LED (GPIO4) sit 29,4–30,8 frå SD-enden og 24,5–25 frå 5V-kanten. Kan sløyfast om blitsen ikkje skal brukast.',
        kjelde='delmaal.json; Printables 650751 (blitshol 5,4 x 5,2)')
    gz0 = max(lens[2] + 8.0 + 3.0, Z - 18.0)
    gy0, gy1 = 2.0, Y - 2.0
    if gz0 - 3.0 <= bl[2] <= Z + 1.0:  # hald blitsvindauget fritt
        if bl[1] > Y / 2:
            gy1 = bl[1] - 2.6 - 2.0
        else:
            gy0 = bl[1] + 2.6 + 2.0
    add('Grepsone framme til høgre', 'framside', [X + whi[0], (gy0 + gy1) / 2, (gz0 + Z) / 2],
        f'Felt {Z - gz0:.1f} B x {gy1 - gy0:.1f} H (z {gz0 + wlo[2]:.1f}–{Z + wlo[2]:.1f}, y {gy0 + wlo[1]:.1f}–{gy1 + wlo[1]:.1f}; blitsvindauget halde fritt): vertikale riller 0,6 djupe, deling 1,6, eller 0,3 mm tekstur. '
        'Valfri fingerrygg: +3,0 mm fram over dei same {:.0f} mm (berre skal, hol innvendig).'.format(Z - gz0),
        'Langfinger og ringfinger ligg her; held fingrane minst 8 mm frå objektivringen (linsa sit på venstre halvdel sett bakfrå).')
    # --- TOPP -----------------------------------------------------------
    ub = boxes['utloysar']; c = (ub[:3] + ub[3:]) / 2; c[1] = Y + whi[1]
    if spec.get('knapp', 'b3f') == 'b3f':
        add('Utløysar', 'topp', c,
            'Hol Ø8,4 for printa hette Ø8,0 med flens Ø11 x 0,8 inne; hetta står 0,8 over toppflata. Krage Ø12 x 0,6 rundt. 6x6 B3F-1000 under (vandring 0,25 +0,2/−0,1, stempel Ø3,5).',
            'GPIO13 mot GND, aktiv låg. Kragen gjer knappen lett å finne med peikefingeren utan å sjå.', kjelde='Omron B3F-datablad')
    else:
        add('Utløysar', 'topp', c, 'Hol Ø13,6 for Ø13 x 8-hette på 12x12x7,3-brytar (vandring 0,3). Krage Ø17 x 0,8.',
            'GPIO13 mot GND, aktiv låg.', kjelde='Omron B3F-datablad; forhandlartal for hetta')
    bb = boxes['brytar']; p, s0 = sol['brytar']; pax, psg = port_dir(p, s0)
    c = (bb[:3] + bb[3:]) / 2; c[pax] = (cav[pax] + whi[pax]) if psg > 0 else -wlo[pax]
    add('Straumbrytar AV/PÅ (SS-12D00G3 på SHDN)', face_name(pax, psg), c,
        'Spor 4,1 x 2,1 (spak 1,5 + vandring 2,0 + 2 x 0,3), langs den lange aksen til brytaren. Forsenking 12 x 7 x 0,8 rundt sporet, så spaken (3,0 over kroppen) står om lag 0,7 over hovudflata. Gravert «0 | I» 0,4 djupt.',
        'Lukka brytar = AV (SHDN mot GND). Forsenkinga hindrar utilsikta påslag i lomma.', kjelde='Vimex SS-12D00 / LCSC-datablad')
    # --- PORTAR ---------------------------------------------------------
    tb = boxes['tp4056']; p, s0 = sol['tp4056']; pax, psg = port_dir(p, s0)
    hax = p[2]
    c = (tb[:3] + tb[3:]) / 2; c[pax] = (cav[pax] + whi[pax]) if psg > 0 else -wlo[pax]
    c[hax] = tb[hax + 3] - M['usbc_rec_h'] / 2
    add('Ladeport USB-C (TP4056)', face_name(pax, psg), c,
        'Gjennomgang 9,2 x 3,4 obround (pluggskal 8,25 x 2,40 + toleranse). Veggen lokalt 1,5 mm (lomme 13 x 7,5 x 0,5 frå innsida), så kontaktfront -> ytterflate = 0,3 + 1,5 = 1,8 mm <= 1,85. Gravert «5V»/lyn 0,4 djupt.',
        'Kappa (maks 12,35 x 6,5) skal liggje an mot ytterflata. Ein ribbe bak modulen tek innstikkskrafta (5–20 N). Mål overhenget til kontakten på modulen: det er ikkje oppgitt nokon stad.',
        kjelde='GCT USB4105-teikning (1,85 min, 3,31 høg); USB Type-C R2.0 (kappe 12,35 x 6,5, skal 8,25 x 2,40)')
    if hax == 1 and tb[4] >= Y - 4.0:
        led = (tb[:3] + tb[3:]) / 2; led[1] = Y + whi[1]
        led[pax] = (tb[pax] + 7.0) if psg < 0 else (tb[pax + 3] - 7.0)
        lflate = 'topp'
        lmål = (f'2 x lysleiar Ø2,0 x {Y - tb[4] + 0.5 + M["vegg"]:.1f} (klar PLA/PMMA-stav) gjennom toppveggen, 3,0 c/c, om lag 7 mm inn frå USB-C-enden; '
                'eller eitt felt 3 x 8 med 0,5 mm restvegg i natur-PLA. Flytt etter målt LED-posisjon.')
    else:
        off_ax = [k for k in range(3) if k not in (pax, hax)][0]
        led = c.copy(); led[off_ax] = c[off_ax] + (6.5 if (tb[off_ax] + tb[off_ax + 3]) / 2 >= c[off_ax] else -6.5)
        lflate = face_name(pax, psg)
        lmål = '2 x lysleiar Ø2,0 eller éi spalte 1,0 x 5,0 med 0,5 mm restvegg i natur-PLA, ved sida av USB-C-opninga. Flytt etter målt LED-posisjon.'
    add('Ladelys (raud = ladar, grøn = ferdig)', lflate, led, lmål,
        'LED-ane sit på komponentsida av TP4056-modulen; ingen forhandlar oppgir posisjonen. Lyset må sjåast medan kabelen står i.',
        kjelde='TP4056-datablad (CHRG/STDBY); Tinytronics/AZ-Delivery (modul)')
    usb = stack_local_to_global(st, M['stabel_L'], M['stabel_W'] / 2)
    usb[0] = boxes['loddesone'][3] + M['mbusb_over_mb']
    usb[La] = (cav[La] + whi[La]) if sgnL > 0 else -wlo[La]
    add('Programmeringsport (micro-USB på MB)', face_name(La, sgnL), usb,
        'Opning 11,6 x 9,5 (kappe maks 10,6 x 8,5 + 0,5 rundt), kappa kan gå inn i veggen. Senter 3,1 over MB-undersida (Printables: kontakten sit 1,3–3,8 over; mål kortet). Printa propp eller TPU-lokk 11,4 x 9,3 med hengsel. Gravert «PROG».',
        'Berre for programmering, med brytaren AV (éi 5 V-kjelde om gongen). Antenneenden av CAM ligg mot same vegg: ikkje metall her.',
        kjelde='delmaal.json (micro-B kappe maks 10,6 x 8,5, typisk 10 x 6, plugg >= 5,4); A2 parametrar.json')
    sd = stack_local_to_global(st, 0.0, (M['sd_W0'] + M['sd_W1']) / 2)
    sd[0] = X - FRONT - 4.5 + 1.15
    sd[La] = -wlo[La] if sgnL > 0 else (cav[La] + whi[La])
    add('microSD-spor', face_name(La, -sgnL), sd,
        'Spalte 11,8 x 2,1 (kort 11 x 15 x 1,0) med 0,5 mm fas og fingerhakk Ø10 x 1,0 djup ved sida. Gravert SD-symbol.',
        'Kortet går inn langs kortaksen frå SD-enden; sokkelen er flukt med kortkanten (0,0 overheng). Kanalen innanfor (2,6 x 16,9) er halden fri i pakkinga.',
        kjelde='delmaal.json (SD-sokkel 0–15,6 frå SD-enden, 5,4–21,7 på tvers, 1,8–2,3 høg)')
    # RST-pinhol: med USB-enden mot ein og komponentsida opp (+x) sit RST til høgre
    f = -sgnL * np.eye(3)[La]; u = np.eye(3)[0]; r = np.cross(f, u)
    rsgn = int(np.sign(r[Wa]))
    edge_at_wall = (boxes['stabel'][Wa + 3] >= cav[Wa] - C - 1e-6) if rsgn > 0 else (boxes['stabel'][Wa] <= C + 1e-6)
    rst = stack_local_to_global(st, M['stabel_L'] - 8.05, 0)
    rst[0] = boxes['loddesone'][3] + 1.6 + 1.0
    rst[Wa] = (cav[Wa] + whi[Wa]) if rsgn > 0 else -wlo[Wa]
    if edge_at_wall:
        add('RST-pinhol (valfritt)', face_name(Wa, rsgn), rst,
            'Ø1,5 hol, 7,5–8,6 frå USB-enden; senterhøgd anslått 2,6 over MB-undersida (MB-PCB-tjukn ikkje funnen): mål før boring.',
            'Sideaktivert RST på MB. RST på MB resettar ikkje alltid CAM-en (Tinytronics), så dette er berre eit hjelpemiddel.',
            kjelde='delmaal.json (knappar 7,5–8,6 frå USB-kanten, RST til høgre med USB mot deg)')
    # --- LUFT -----------------------------------------------------------
    bo = boxes['boost']; cb = (bo[:3] + bo[3:]) / 2
    cands = []
    for k in range(3):
        for sgn in (-1, 1):
            if k == 0 and sgn < 0 and spec['arch'] == 'x-':
                continue
            if k == 1 and sgn < 0 and spec['arch'] == 'y-':
                continue
            d = (bo[k]) if sgn < 0 else (cav[k] - bo[k + 3])
            cands.append((d, k, sgn))
    d, k, sgn = min(cands)
    v = cb.copy(); v[k] = -wlo[k] if sgn < 0 else cav[k] + whi[k]
    add('Luftespalter ved boosten', face_name(k, sgn), v,
        f'4 spalter 1,2 x 8,0, deling 2,4 (bru 1,2 = 3 liner); avstand boost->vegg {d:.1f} mm',
        'Tap i U1V11F5: P_ut·(1/η−1) ≈ 0,06–0,41 W. Spaltene ligg ved spolen og vekk frå cella.', kjelde='Pololu U1V11F5 (η 70–90 %)')
    sb = boxes['stabel']
    esp_lo = stack_local_to_global(st, M['stabel_L'] - 25.5, 0); esp_hi = stack_local_to_global(st, M['stabel_L'] - 11.0, M['stabel_W'])
    e0 = min(esp_lo[La], esp_hi[La]); e1 = max(esp_lo[La], esp_hi[La])
    # botn-/sidevegg langs stabelens W-kant som står mot ein vegg
    wsgn = -1 if sb[Wa] <= C + 1e-6 else (1 if sb[Wa + 3] >= cav[Wa] - C - 1e-6 else -1)
    v = np.zeros(3); v[0] = X - 8.0; v[La] = (e0 + e1) / 2; v[Wa] = -wlo[Wa] if wsgn < 0 else cav[Wa] + whi[Wa]
    add('Luftinntak under ESP32-S-skjoldet', face_name(Wa, wsgn), v,
        f'6 spalter 1,2 x 6,0 (langs x), deling 2,4, over {e1 - e0:.1f} mm av antennehalvdelen (11–25,5 mm frå USB-enden, så RST-holet står fritt; x ca. {X - 11 + wlo[0]:.0f}–{X - 5 + wlo[0]:.0f})',
        'ESP32-S-skjoldet ligg 0–25,5 frå antenneenden, mellom CAM og MB. Kald luft inn her, varm ut ved programmeringsporten (skorsteinsverknad).',
        kjelde='delmaal.json (skjold 18 x 25,5 x 3,0); arXiv 2505.24081 (65–74 °C internt)')
    v2 = usb.copy(); v2[0] = X - 7.0 + wlo[0] - wlo[0]
    v2 = stack_local_to_global(st, M['stabel_L'], M['stabel_W'] / 2); v2[0] = X - 7.0
    v2[La] = (cav[La] + whi[La]) if sgnL > 0 else -wlo[La]
    add('Luftutløp ved programmeringsporten', face_name(La, sgnL), v2,
        '2 x 3 spalter 1,2 x 6,0 framom porten (x ca. X−9 til X−5), over og under senterlinja',
        'Utløp for varm luft frå ESP32-S og AMS1117 (≈ 0,25–0,31 W i regulatoren ved 180 mA).', kjelde='integrasjonsnotat (effektbudsjett)')
    # --- BAK / LOKK -----------------------------------------------------
    if spec['arch'] == 'x-':
        ce = boxes['celle']
        add('Baklokk som skyvelokk (batteriluke)', 'bakside', [-wlo[0], Y / 2, Z / 2],
            f'Flatt panel {Z:.1f} x {Y:.1f} x 1,6 som går i spor 0,8 x 1,0 i topp- og botnveggen, skyvast ut mot venstre; venstre vegg stoppar 1,6 mm før bakkanten. Hakelås: knast r 1,0 / 0,5 ut (A2-verdi) i høgre ende.',
            'Lokket held cella med skumputa (0,5) og innmatsramma. Ingen skruer eller bossar inne, så heile bakflata er cellelomme.', kjelde='A2 parametrar.json (knast_r 1,0, knast_ut 0,5)')
        add('Trykkavlastning i lokket', 'bakside', [-wlo[0], ce[4] - 6.0, (ce[2] + ce[5]) / 2],
            '3 spalter 0,8 x 12 (eller eit felt 15 x 10 med 0,6 mm restvegg) nær overkanten av cellelomma',
            'Lufteveg slik at gass frå ei skadd celle kan sleppe ut utan at boksen blir sett under trykk. PLA mjuknar ved 54–60 °C, så huset er ikkje brannvern.',
            kjelde='kraftnotat (EEMB/Ormix: stopp bruk ved svelling; Bambu PLA HDT 54/57 °C)')
        add('Tommelkvile', 'bakside', [-wlo[0], Y * 0.62, Z - 10.0],
            'Opphøgd pute 14 x 18 x 1,0 med 3 tverriller, eller 0,3 mm tekstur', 'Mothald for tommelen når utløysaren blir trykt.')
        add('Fingergrep for lokket', 'bakside', [-wlo[0], Y / 2, 3.0], '3 riller 0,6 x 10 ved venstre kant', 'Skyv lokket ut med tommelen.')
        add('Skøyt (delelinje)', 'rundt baksida', [0.0, Y / 2, Z / 2],
            f'Rundt heile bakkanten, {wlo[0]:.1f} mm frå bakflata; 0,3 mm skuggefuge (fas 0,3 x 45°)',
            'Einaste synlege delelinja: frontskalet (5 sider i eitt) + baklokk. Gjer det lett å lese kroppen som éin blokk.')
    else:
        add('Botnluke som skyvelokk (batteri)', 'botn', [X / 2, -wlo[1], Z / 2],
            f'Flatt panel {Z:.1f} x {X:.1f} x 1,6 i spor 0,8 x 1,0 i fram- og bakveggen, skyvast ut mot venstre; hakelås knast r 1,0 / 0,5',
            'Cella fyller heile golvet (34,5 av 35,1 mm djupn), så det er ikkje plass til skruebossar (M2 krev boss Ø5,0). Lokket ber cella via skumputa.',
            kjelde='Albany County Fasteners (M2: boss >= 5,0); A2 parametrar.json (knast)')
        add('Skøyt (delelinje)', 'rundt botnen', [X / 2, 0.0, Z / 2], '1,6 mm over botnflata, 0,3 mm skuggefuge',
            'Einaste synlege delelinja: hovudskal (5 sider) + botnluke.')
        add('Trykkavlastning i botnluka', 'botn', [X * 0.7, -wlo[1], Z * 0.3], '3 spalter 0,8 x 12 eller felt 15 x 10 med 0,6 mm restvegg',
            'Lufteveg for gass frå ei skadd celle; PLA er ikkje brannvern.', kjelde='kraftnotat')
    # innmatsramme
    add('Klips for innmatsramma (inne)', 'innside topp/botn', [boxes['skiljeplate'][3], Y / 2, Z / 2],
        '4 knastar r 1,0 / 0,5 ut på innsida av topp- og botnveggen ved z = 25 % og 75 %, rett framom skiljeplata',
        'Held stabelen mot frontskuldrene (4 hjørneribber 2 x 2 frå frontveggen til CAM-PCB, utanfor stiftane).', kjelde='A2 parametrar.json')
    # stropp
    occ = [b for n, b in res['placed'] if n not in ZONES and n not in ('skiljeplate',)]
    best = None
    for zc in (Z - 3.5, 3.5):
        for yc in (Y - 3.5, 3.5):
            for xc in (X - 3.5, X - 10.0):
                box = B([xc - 2.5, yc - 2.5, zc - 2.5], [xc + 2.5, yc + 2.5, zc + 2.5])
                if not any(boxes_overlap(box, b, 0.0) for b in occ):
                    best = (xc, yc, zc); break
            if best: break
        if best: break
    if best:
        add('Stroppfeste (kanal gjennom hjørnet)', 'hjørne ' + ('høgre' if best[2] > Z / 2 else 'venstre') + (' oppe' if best[1] > Y / 2 else ' nede'), best,
            'Bøygd kanal Ø2,2 gjennom ein massiv hjørneblokk 5 x 5 x 5 (inn på sida, ut på toppen/botnen)',
            'Handleddsstropp. Plassert i eit hjørne der pakkinga har ledig rom (sjekka mot alle komponentar).')
    else:
        add('Stroppfeste (utvendig øyre)', 'høgre side', [X / 2, Y - 4, Z + whi[2]], 'Øyre 6 x 4 x 2,5 med Ø2,2 hol', 'Inga ledig hjørnekube inne, difor utvendig.')
    # stativ
    if 'stativ' in boxes:
        sb2 = boxes['stativ']; c = (sb2[:3] + sb2[3:]) / 2; c[1] = -wlo[1]
        add('Stativgjenge 1/4"-20', 'botn', c, 'Innsmeltingsmutter: hol 8,2, OD 9,53, lengd 9,5–12,7, boss >= Ø13,5. Munnen 0,3 under botnflata.',
            'Sony tilrår stativskruer under 5,5 mm; kameragjenger er 6–6,7 djupe.', kjelde='Albany County Fasteners; Sony helpguide; Ricoh THETA X')
    else:
        add('Stativ (tilval som påklipst fot)', 'botn', [X / 2, -wlo[1], Z / 2],
            'Eigen fotplate 10,5 tjukk med 1/4"-20-innsmeltingsmutter (hol 8,2, OD 9,53, lengd 9,5, boss Ø13,5), klikkar i 2 spor 1,0 x 1,0 i botnen',
            'Det er ikkje plass til mutteren inne utan å gjere kroppen større (sjå L3). Fotplata gjer kroppen 10,5 mm høgare berre når ho er på.',
            kjelde='Albany County Fasteners; Sony helpguide')
    # graveringar
    add('Graveringar', 'alle', [X / 2, Y / 2, Z / 2], '0,4 mm djupe, linjebreidd >= 0,5 (2 liner): «0 | I», «5V», «PROG», SD-symbol, pil for lokket',
        'Funksjonell merking av kvar port og kontroll.')
    return F


def assembly_text(res, spec):
    boxes = dict(res['placed']); sol = res['sol']
    jst = 'jst' in boxes
    fl = {n: face_name(*port_dir(*sol[n])) for n in ('tp4056', 'brytar', 'utloysar') if n in sol}
    st = res['st']
    usbf = face_name(st['La'], 1 if st['sL'] > 0 else -1)
    sdf = face_name(st['La'], -1 if st['sL'] > 0 else 1)
    steg = []
    steg.append('Førebu (utanfor huset): lodd 26 AWG frå MB-undersida (pad 1 = 5V, pad 2 = GND i 5V-rekkja) via 1N5817 (ring mot MB) til boost VOUT/GND, '
                'og C1 470 µF rett på 5V/GND-padane. Lodd 30 AWG til IO13 (pad 4). Boost VIN/GND til TP4056 OUT+/OUT−, SHDN + GND til brytaren. '
                + ('Lodd B2B-PH-K-S-stiftene til TP4056 B+/B− med 26 AWG og krympestrømpe.' if jst else 'Kort celleleidningane til lengda i kanalen og lodd dei på B+/B− (raud på B+). Mål polariteten først.'))
    if spec['arch'] == 'x-':
        steg.append('Frontskalet (fem sider i eitt, ope bak) ligg med fronten ned på bordet.')
        steg.append(f'Utløysarhetta inn frå innsida ({fl.get("utloysar")}), så 6x6-knappen i lomma under. Brytaren i lomma si med spaken gjennom sporet ({fl.get("brytar")}).')
        steg.append(f'TP4056 inn i lomma med USB-C mot porten ({fl.get("tp4056")}); ribba bak modulen tek innstikkskrafta.')
        steg.append(f'CAM+MB-stabelen blir skyvd inn bakfrå: linsa i objektivringen, USB-enden mot programmeringsporten ({usbf}), SD-enden mot SD-sporet ({sdf}).')
        steg.append('Boost, C1, diode' + (' og JST-overgangen' if jst else '') + ' i lommene, leidningane i kanalane (loddesona bak MB er hovudkanalen).')
        steg.append('Innmatsramma med skiljeplata (1,0 mm, heil, utan skruespissar) klikkar inn og pressar MB mot hjørnehyllene.')
        steg.append(('Plugg cella i JST-en, ' if jst else 'Legg ') + 'cella flatt på plata med PCM-enden mot leidningssona (3 mm), skumputa (0,5) oppå.')
        steg.append('Skyv baklokket inn i spora frå venstre til det klikkar. Opning: skyv lokket ut, ta ut cella' + (' og dra JST-pluggen' if jst else '') + ', så ramma.')
    else:
        steg.append('Hovudskalet (fem sider, ope nede) ligg med toppen ned. Utløysar og brytar i lommene under toppveggen.')
        steg.append('TP4056, boost, C1, diode og JST i lommene bak stabelen. Stabelen inn nedanfrå, linsa i ringen.')
        steg.append('Skiljeplata/innmatsramma klikkar inn under stabelen. Plugg cella, legg ho på plata, skumputa under.')
        steg.append('Skyv botnluka (1,6 mm) inn i spora frå venstre til hakelåsen klikkar.')
    return ' '.join(f'{i + 1}) {t}' for i, t in enumerate(steg))


def family_bounds():
    """Analytisk nedre grense for kvar arkitekturfamilie (berre stabel + celle-gruppe, utan smådelar)."""
    L, W = M['stabel_L'] + 2 * C, M['stabel_W'] + 2 * C
    gl = C + M['celle_L'] + M['leidningssone']; gw = M['celle_W'] + 2 * C
    batt = M['skum'] + T_CELL + SEP_T
    sx = LODD + STACK_D + FRONT
    fam = []
    # sandwich (celle bak)
    for nm, inner in [('x- sandwich, liggjande', (batt + sx, gw, gl)), ('x- sandwich, ståande', (batt + sx, gl, gw)),
                      ('y- golv (celle under stabelen)', (max(gw, sx + C), batt + W - C, max(gl, L))),
                      ('z- side (celle ved sida, ståande)', (max(gw, sx + C), max(gl, L), batt + W - C))]:
        lo = np.array([M['vegg_flat'] if nm.startswith('x-') else M['vegg'], M['vegg_flat'] if nm.startswith('y-') else M['vegg'], M['vegg_flat'] if nm.startswith('z-') else M['vegg']])
        o = np.array(inner) + lo + M['vegg']
        fam.append(dict(familie=nm, indre_mm=[round(v, 2) for v in inner], ytre_mm=[round(float(v), 2) for v in o], ytre_cm3=round(float(np.prod(o)) / 1000, 1)))
    return fam


def load_result(spec, path):
    """Les ei tidlegare søkeløysing frå pakking_<n>.json (for ny eksport utan nytt søk)."""
    d = json.load(open(path))
    L = [l for l in d['layoutar'] if l['id'] == spec['id']][0]
    cav = np.array([L['indre_mm']['X_djupn'], L['indre_mm']['Y_hogd'], L['indre_mm']['Z_breidd']])
    placed = []; sol = {}
    for c in L['komponentar']:
        placed.append((c['namn'], np.array(c['min_indre'] + c['max_indre'], dtype=float)))
        if c['orientering']:
            sol[c['namn']] = (tuple(c['orientering']['perm']), c['orientering']['s0'])
    sk = L['søk']
    La = AX[sk['stabel']['L_akse']]
    sb = dict(placed)['stabel']
    lo = np.zeros(3); lo[1] = sb[1]; lo[2] = sb[2]
    st = dict(La=La, Wa=3 - La, sL=sk['stabel']['sL'], sW=sk['stabel']['sW'], lo=lo)
    ta = {'x-': 0, 'y-': 1, 'z-': 2, 'z+': 2}[spec['arch']]
    bmeta = dict(ta=ta, tsign=-1, La=AX[sk['celle']['L_akse']], sl=sk['celle']['leidningsende'])
    return dict(cav=cav, placed=placed, sol=sol, routes=L['kanalar'], st=st, bmeta=bmeta, tried=sk['hol_prøvde'], sekund=sk['sekund'])


def mass_and_com(res, spec, srch):
    cav = res['cav']
    wlo, whi = srch.wall_t()
    out = cav + wlo + whi
    v_out = float(np.prod(out)); v_in = float(np.prod(cav))
    v_shell = v_out - v_in
    boxes = dict(res['placed'])
    sep = boxes['skiljeplate']; v_sep = float(np.prod(size(sep)))
    v_ring = math.pi / 4 * (16 ** 2 - 11 ** 2) * 3.0
    v_pla = (v_shell + v_sep + v_ring) / 1000.0
    m_pla = v_pla * M['pla_rho']
    parts_mass = []
    sb = boxes['stabel']
    cam = sb.copy(); cam[3] = sb[3]; cam[0] = sb[3] - 6.0
    mb = sb.copy(); mb[3] = sb[0] + 10.0
    parts_mass.append(('ESP32-CAM', 10.0, 10.0, cam))
    parts_mass.append(('ESP32-CAM-MB', 6.0, 10.0, mb))
    parts_mass.append(('LiPo LP603448', 17.0, 21.0, boxes['celle']))
    parts_mass.append(('U1V11F5', 0.7, 0.7, boxes['boost']))
    parts_mass.append(('utløysar', M['m_b3f'] if spec.get('knapp', 'b3f') == 'b3f' else M['m_b12'],
                       M['m_b3f'] if spec.get('knapp', 'b3f') == 'b3f' else M['m_b12'], boxes['utloysar']))
    lo = sum(p[1] for p in parts_mass) + m_pla
    hi = sum(p[2] for p in parts_mass) + m_pla
    # tyngdepunkt (middelmasse), skalet som jamn masse i boksskalet
    num = np.zeros(3); den = 0.0
    for n, a, b, bx in parts_mass:
        m = (a + b) / 2
        num += m * (bx[:3] + bx[3:]) / 2; den += m
    shell_c = cav / 2 + (whi - wlo) / 2  # skalet sitt senter i indre koordinatar (tilnærma)
    num += m_pla * shell_c; den += m_pla
    com = num / den
    centre = cav / 2
    return dict(pla_cm3=round(v_pla, 2), pla_g=round(m_pla, 1), kjende_komponentar_g=[round(sum(p[1] for p in parts_mass), 1), round(sum(p[2] for p in parts_mass), 1)],
                totalt_g=[round(lo, 1), round(hi, 1)],
                ikkje_med='TP4056-modul, SS-12D00, EEU-FR1A471, 1N5817, leidningar, skumpute, JST og stativmutter: vekt ikkje funnen i kjeldene',
                tyngdepunkt_indre_mm=[round(float(v), 1) for v in com],
                tyngdepunkt_avvik_frå_senter_mm=[round(float(v), 1) for v in (com - centre)])


def export(res, spec, srch, idx):
    cav = res['cav']
    wlo, whi = srch.wall_t()
    sc = trimesh.Scene()
    for n, b in res['placed']:
        m = trimesh.creation.box(bounds=[b[:3] + wlo, b[3:] + wlo])
        m.visual.face_colors = COLORS.get(n, (200, 200, 200, 255))
        sc.add_geometry(m, node_name=n, geom_name=n)
    # linse
    st = res['st']
    lens = stack_local_to_global(st, M['linse_L'], M['linse_W'])
    x0 = cav[0] - FRONT
    cyl = trimesh.creation.cylinder(radius=M['linse_d'] / 2, height=M['linse_over_kropp'],
                                    transform=trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    cyl.apply_translation([x0 + M['linse_over_kropp'] / 2 + wlo[0], lens[1] + wlo[1], lens[2] + wlo[2]])
    cyl.visual.face_colors = COLORS['linse']
    sc.add_geometry(cyl, node_name='linse', geom_name='linse')
    # skal (hol boks)
    outer = trimesh.creation.box(bounds=[np.zeros(3), cav + wlo + whi])
    inner = trimesh.creation.box(bounds=[wlo, cav + wlo])
    try:
        shell = outer.difference(inner)
    except Exception:
        shell = outer
    ring = trimesh.creation.annulus(r_min=5.5, r_max=8.0, height=3.0,
                                    transform=trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    ring.apply_translation([cav[0] + wlo[0] + whi[0] + 1.5, lens[1] + wlo[1], lens[2] + wlo[2]])
    try:
        shell = trimesh.util.concatenate([shell, ring])
    except Exception:
        pass
    shell.visual.face_colors = COLORS['skal']
    sc.add_geometry(shell, node_name='skal', geom_name='skal')
    # kanalar
    for nm, r in res['routes'].items():
        pts = [np.array(p) for p in r['punkt']]
        for i, bx in enumerate(path_boxes(pts, r['breidd'])):
            m = trimesh.creation.box(bounds=[bx[:3] + wlo, bx[3:] + wlo])
            m.visual.face_colors = COLORS['kanal']
            sc.add_geometry(m, node_name=f'kanal_{nm}_{i}', geom_name=f'kanal_{nm}_{i}')
    path = os.path.join(HERE, f'layout_{idx}.glb')
    sc.export(path)
    return path


def render_png(res, spec, srch, idx, title):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception:
        return None
    cav = res['cav']
    wlo, whi = srch.wall_t()
    out = cav + wlo + whi
    st = res['st']
    lens = stack_local_to_global(st, M['linse_L'], M['linse_W'])
    fig = plt.figure(figsize=(15, 6.5), dpi=110)
    views = [('Frå høgre side og framme (høgre = sett bakfrå), heile innmaten', 22, 35, set()),
             ('Bakfrå, cellegruppa skjult (stripene rundt stabelen)', 28, -125, {'celle', 'skum', 'skiljeplate', 'leidningssone'})]
    for vi, (vt, el, az, hide) in enumerate(views):
        axp = fig.add_subplot(1, 2, vi + 1, projection='3d')

        def draw(b, col, alpha, lw=0.3):
            x0, y0, z0, x1, y1, z1 = b
            P = lambda x, y, z: (z, x, y)
            V = [P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)]
            faces = [[V[0], V[1], V[2], V[3]], [V[4], V[5], V[6], V[7]], [V[0], V[1], V[5], V[4]],
                     [V[2], V[3], V[7], V[6]], [V[1], V[2], V[6], V[5]], [V[0], V[3], V[7], V[4]]]
            axp.add_collection3d(Poly3DCollection(faces, facecolors=col, alpha=alpha, edgecolors='k', linewidths=lw))
        for n, b in res['placed']:
            if n in hide:
                continue
            c = np.array(COLORS.get(n, (200, 200, 200, 255))[:3]) / 255
            a = 0.18 if (n in ZONES or n == 'skiljeplate') else 0.9
            draw(b + np.concatenate([wlo, wlo]), c, a)
        draw(np.concatenate([np.zeros(3), out]), (0.85, 0.85, 0.85), 0.04, 0.7)
        for nm, r in res['routes'].items():
            pts = np.array(r['punkt']) + wlo
            axp.plot(pts[:, 2], pts[:, 0], pts[:, 1], color='orange', lw=1.4)
        # linse + objektivring
        th = np.linspace(0, 2 * np.pi, 40)
        for rr, xx, col in ((M['linse_d'] / 2, out[0] + 2.0, 'k'), (8.0, out[0] + 3.0, 'dimgray'), (8.0, out[0], 'dimgray')):
            axp.plot(lens[2] + wlo[2] + rr * np.cos(th), np.full_like(th, xx), lens[1] + wlo[1] + rr * np.sin(th), color=col, lw=1.2)
        axp.set_box_aspect((out[2], out[0] + 4, out[1]))
        axp.set_xlim(0, out[2]); axp.set_ylim(0, out[0] + 4); axp.set_zlim(0, out[1])
        axp.set_xlabel('z breidd (mm)'); axp.set_ylabel('x djupn (fram ->)'); axp.set_zlabel('y opp')
        axp.view_init(elev=el, azim=az)
        axp.set_title(vt, fontsize=9)
    handles = []
    names = dict(res['placed'])
    for n in ['stabel', 'celle', 'tp4056', 'boost', 'brytar', 'utloysar', 'kondensator', 'diode', 'jst', 'stativ', 'skiljeplate', 'loddesone', 'leidningssone', 'sd_kanal']:
        if n in names:
            handles.append(mpatches.Patch(color=np.array(COLORS[n][:3]) / 255, label=n))
    handles.append(mpatches.Patch(color='orange', label='leidningskanal'))
    fig.legend(handles=handles, loc='center left', fontsize=8)
    fig.suptitle(f'{title}:  ytre {out[2]:.1f} B x {out[1]:.1f} H x {out[0]:.1f} D mm (+3,0 objektivring), {np.prod(out) / 1000:.1f} cm3', fontsize=11)
    path = os.path.join(HERE, f'layout_{idx}.png')
    fig.savefig(path, bbox_inches='tight')
    plt.close(fig)
    return path


def ports_summary(res, spec):
    sol = res['sol']; st = res['st']
    out = {}
    for n in ('tp4056', 'brytar', 'utloysar', 'stativ'):
        if n in sol:
            p, s0 = sol[n]
            out[n] = face_name(*port_dir(p, s0))
    out['mb_microusb'] = face_name(st['La'], 1 if st['sL'] > 0 else -1)
    out['microsd'] = face_name(st['La'], -1 if st['sL'] > 0 else 1)
    out['linse'] = 'framside'
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    from_json = '--frå-json' in sys.argv
    only = [int(a) for a in args] if args else None
    results = []
    for spec in LAYOUTS:
        if only and spec['id'] not in only:
            continue
        srch = Searcher(spec)
        t0 = time.time()
        if from_json:
            src = os.path.join(HERE, f'pakking_{spec["id"]}.json')
            if not os.path.exists(src):
                src = os.path.join(HERE, 'pakking.json')
            res = load_result(spec, src)
        else:
            res = srch.search(time_limit=spec.get('time', 900), node_limit=spec.get('nodes', 3000))
        if res is None:
            print(f"[{spec['id']}] inga løysing funnen ({time.time() - t0:.0f} s)")
            results.append(dict(id=spec['id'], namn=spec['namn'], løysing=None))
            continue
        cav = res['cav']
        wlo, whi = srch.wall_t()
        outer = cav + wlo + whi
        ver = verify(res, spec)
        mc = mass_and_com(res, spec, srch)
        glb = export(res, spec, srch, spec['id'])
        png = render_png(res, spec, srch, spec['id'], spec['namn'])
        ring_extra = 3.0
        comp = []
        for n, b in res['placed']:
            comp.append(dict(namn=n, min_indre=[round(float(v), 2) for v in b[:3]], max_indre=[round(float(v), 2) for v in b[3:]],
                             min_ytre=[round(float(v), 2) for v in (b[:3] + wlo)], max_ytre=[round(float(v), 2) for v in (b[3:] + wlo)],
                             mål=[round(float(v), 2) for v in size(b)],
                             orientering=(None if n not in res['sol'] else dict(perm=list(res['sol'][n][0]), s0=res['sol'][n][1],
                                                                                portretning=face_name(*port_dir(*res['sol'][n]))))))
        r = dict(id=spec['id'], namn=spec['namn'], skildring=spec['skildring'], arkitektur=spec['arch'],
                 indre_mm=dict(X_djupn=round(float(cav[0]), 2), Y_hogd=round(float(cav[1]), 2), Z_breidd=round(float(cav[2]), 2)),
                 ytre_mm=dict(djupn=round(float(outer[0]), 2), hogd=round(float(outer[1]), 2), breidd=round(float(outer[2]), 2),
                              djupn_med_objektivring=round(float(outer[0] + ring_extra), 2)),
                 veggar_mm=dict(lo=[float(v) for v in wlo], hi=[float(v) for v in whi]),
                 volum_cm3=dict(indre=round(float(np.prod(cav)) / 1000, 2), ytre_kropp=round(float(np.prod(outer)) / 1000, 2),
                                ytre_med_ring=round(float(np.prod(outer)) / 1000 + math.pi / 4 * 16 ** 2 * 3.0 / 1000, 2)),
                 masse=mc, portar=ports_summary(res, spec), komponentar=comp, kanalar=res['routes'], kontroll=ver,
                 søk=dict(hol_prøvde=res['tried'], sekund=res['sekund'], stabel=dict(L_akse=AXN[res['st']['La']], sL=res['st']['sL'], sW=res['st']['sW']),
                          celle=dict(L_akse=AXN[res['bmeta']['La']], leidningsende=res['bmeta']['sl'])),
                 montering=assembly_text(res, spec), filer=dict(glb=glb, png=png))
        r['overflate'] = build_features(res, spec, srch)
        results.append(r)
        print(f"[{spec['id']}] {spec['namn']}: ytre {outer[2]:.1f} B x {outer[1]:.1f} H x {outer[0]:.1f} D = {np.prod(outer) / 1000:.1f} cm3 "
              f"(indre {np.prod(cav) / 1000:.1f}); {res['tried']} hol prøvde, {res['sekund']} s; kontroll: {len(ver['problem'])} problem, "
              f"{len(ver['trimesh_overlapp'])} overlapp; min klaring {ver['minste_klaring_mm']}")
    data = dict(
        tittel='A5 pakking: brute-force-søk over orienteringar og plasseringar',
        koordinatar='x = djupn (+x fram, linsa), y = opp, z = breidd (+z = høgre sett bakfrå). Indre: origo i innvendig bak-botn-venstre hjørne. Ytre: origo i utvendig bak-botn-venstre hjørne.',
        reglar=dict(klaring_kort=C, svell_tjukn='+10 %', skumpute=M['skum'], vegg=M['vegg'], vegg_flatt_panel=M['vegg_flat'],
                    leidningskanal='3,0 mm (26 AWG-par) og 2,0 mm (30 AWG-par) berre der leidningane faktisk går',
                    frigang_front=FRONT, loddesone_under_MB=LODD, skiljeplate=SEP_T),
        familiar_nedre_grense=family_bounds(), mål=M, kjelder=KJ, layoutar=results)
    outname = 'pakking.json' if (not only or len(only) == len(LAYOUTS)) else f'pakking_{"_".join(map(str, only))}.json'
    with open(os.path.join(HERE, outname), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))


if __name__ == '__main__':
    main()
