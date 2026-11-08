"""Crop the checked-in ImageGen atlas into the four requested 16x16 materials.

Only needed when replacing the source artwork; normal builds use the committed PNGs.
Requires Pillow. Nearest-neighbor resampling preserves the pixel-art character.
"""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]/'assets-source'

def main():
    with Image.open(ROOT/'repair-materials.png') as source:
        image=source.convert('RGB')
    w,h=image.size
    boxes={'steel':(0,0,w//2,h//2),'casing':(w//2,0,w,h//2),
           'vent':(0,h//2,w//2,h),'circuit':(w//2,h//2,w,h)}
    output=ROOT/'textures/block'
    output.mkdir(parents=True,exist_ok=True)
    for name,box in boxes.items():
        image.crop(box).resize((16,16),Image.Resampling.NEAREST).save(output/(name+'.png'),optimize=True)

if __name__=='__main__':
    main()
