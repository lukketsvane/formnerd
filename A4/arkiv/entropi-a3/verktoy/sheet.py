import sys
from PIL import Image
prefix, out = sys.argv[1], sys.argv[2]
names = ['skra-framme', 'grepside', 'bak', 'linse', 'skra-bak', 'topp']
ims = [Image.open(f'{prefix}-{n}.png').convert('RGB').resize((600, 600)) for n in names]
sheet = Image.new('RGB', (1800, 1200), 'white')
for i, im in enumerate(ims):
    sheet.paste(im, ((i % 3) * 600, (i // 3) * 600))
sheet.save(out)
