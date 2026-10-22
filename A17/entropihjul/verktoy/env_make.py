import numpy as np, json, sys

EH, EW = 256, 512
el = 90 - (np.arange(EH) + 0.5) * 180.0 / EH
az = (np.arange(EW) + 0.5) * 360.0 / EW
EL, AZ = np.meshgrid(el, az, indexing='ij')
DIR = np.stack([np.cos(np.radians(EL)) * np.cos(np.radians(AZ)), np.cos(np.radians(EL)) * np.sin(np.radians(AZ)), np.sin(np.radians(EL))], -1)


def lobe(az0, el0, width, sharp=2.0):
    c = np.array([np.cos(np.radians(el0)) * np.cos(np.radians(az0)), np.cos(np.radians(el0)) * np.sin(np.radians(az0)), np.sin(np.radians(el0))])
    ang = np.degrees(np.arccos(np.clip(DIR @ c, -1, 1)))
    return 1.0 / (1.0 + np.exp((ang - width) / sharp))


def band(el0, el1, soft=3.0):
    return 1.0 / (1.0 + np.exp((el0 - EL) / soft)) / (1.0 + np.exp((EL - el1) / soft))


def basis():
    B = {}
    B['sky'] = band(5, 91, 4)
    B['zen'] = lobe(0, 90, 35, 6)
    for k, a in enumerate(range(0, 360, 45)):
        B[f'up{a}'] = lobe(a, 30, 28, 6) * band(0, 91, 2)
        B[f'lo{a}'] = lobe(a, -25, 30, 6) * band(-91, 2, 2)
    B['hor'] = band(-6, 6, 2)
    B['gnd'] = band(-91, -40, 6)
    return B


def make(weights):
    B = basis()
    E = np.zeros((EH, EW))
    for k, w in weights.items():
        E += w * B[k]
    return np.repeat(E[..., None], 3, 2).astype(np.float32)


if __name__ == '__main__':
    w = json.loads(open(sys.argv[2]).read()) if sys.argv[2].endswith('.json') else json.loads(sys.argv[2])
    np.save(sys.argv[1], make(w))
