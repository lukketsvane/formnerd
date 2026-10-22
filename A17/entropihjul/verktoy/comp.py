import sys, numpy as np, cv2
from PIL import Image


def over_white(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    mx = 65535.0 if im.max() > 255 else 255.0
    rgb = im[:, :, 2::-1] / mx; a = im[:, :, 3:4] / mx
    out = rgb * a + (1 - a)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    img = over_white(src)
    Image.fromarray(img).save(dst)
    if len(sys.argv) > 4:
        ref = np.asarray(Image.open(sys.argv[3]).convert('RGB').resize((img.shape[1], img.shape[0])))
        Image.fromarray(np.hstack([ref, img])).save(sys.argv[4])
