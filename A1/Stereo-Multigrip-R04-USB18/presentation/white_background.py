import sys
from PIL import Image
for path in sys.argv[1:]:
 foreground=Image.open(path).convert('RGBA')
 background=Image.new('RGBA',foreground.size,(255,255,255,255))
 Image.alpha_composite(background,foreground).convert('RGB').save(path)
 print(path)
