"""Segundo color (experimental): se calcula desde el sprite oficial que usa el juego
(PokeAPI/sprites, sprites/pokemon/{id}.png). No es un dato oficial de los juegos.

Regla fija, reproducible:
1. Se ignoran los píxeles transparentes, los del borde (el contorno del dibujo) y los negros
   que no forman una zona maciza (líneas internas y sombras finas).
2. Cada píxel se clasifica en uno de los 10 colores oficiales de la Pokédex por su tono,
   saturación y brillo (HSV).
3. El segundo color es el más frecuente que NO sea el color oficial de la especie,
   siempre que ocupe al menos MIN_SHARE del cuerpo. Si no llega, queda NINGUNO."""
import colorsys, json
from PIL import Image

COLORS = ['black', 'blue', 'brown', 'gray', 'green', 'pink', 'purple', 'red', 'white', 'yellow']
MIN_SHARE = 0.12

def classify(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if v < 0.25 or (v < 0.4 and s < 0.5): return 'black'
    if s < 0.15: return 'white' if v > 0.8 else 'gray'
    if s < 0.35 and v > 0.75 and 15 <= h < 70: return 'white'     # crema / beige claro
    if 12 <= h < 38:                                                 # naranjas y marrones
        return 'red' if s >= 0.6 and v >= 0.7 else 'brown'
    if h < 12 or h >= 330: return 'pink' if s < 0.6 and v > 0.7 else 'red'
    if h < 70: return 'yellow' if v > 0.55 else 'brown'
    if h < 185: return 'green'
    if h < 245: return 'blue'
    if h < 290: return 'purple'
    return 'pink'

def shares(path):
    im = Image.open(path).convert('RGBA')
    w, hgt = im.size; px = im.load()
    cls = {}
    for y in range(hgt):
        for x in range(w):
            if px[x, y][3] >= 128: cls[x, y] = classify(*px[x, y][:3])
    near = ((1, 0), (-1, 0), (0, 1), (0, -1))
    counts = dict.fromkeys(COLORS, 0); total = 0
    for (x, y), c in cls.items():
        if any((x + dx, y + dy) not in cls for dx, dy in near): continue     # contorno exterior
        # Negro sólo cuenta en zonas macizas: descarta líneas internas del dibujo y sombras finas.
        if c == 'black' and any(cls[x + dx, y + dy] != 'black' for dx, dy in near): continue
        counts[c] += 1; total += 1
    return {k: n / total for k, n in counts.items()} if total else {}

def second_color(path, official):
    sh = shares(path)
    rest = sorted(((v, k) for k, v in sh.items() if k != official), reverse=True)
    return (rest[0][1] if rest and rest[0][0] >= MIN_SHARE else None), sh

if __name__ == '__main__':
    out = {}
    for i in range(1, 1026):
        official = json.load(open(f'cache/pokemon-species_{i}.json'))['color']['name']
        out[i] = second_color(f'sprites/{i}.png', official)
    json.dump({i: [c, sh] for i, (c, sh) in out.items()}, open('second_color.json', 'w'))
