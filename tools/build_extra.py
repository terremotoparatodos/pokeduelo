"""Genera la cadena EXTRA del juego: altura|peso|mega|regional|método|mejor stat|fase|2º color|método+ por especie (#1-#1025).
Ejecutar desde la carpeta que contiene cache/ después de fetch_pokeapi.py."""
import json, re, sys
sys.argv = ['x']
exec(open('tools/evo_method.py', encoding='utf-8').read().split('if __name__')[0])
sys.path.insert(0, 'tools')
from sprite_colors import COLORS, second_color

METHODS = ['NINGUNO', 'NIVEL', 'PIEDRA', 'INTERCAMBIO', 'AMISTAD', 'OBJETO', 'MOVIMIENTO', 'ESPECIAL']
REGIONS = ['alola', 'galar', 'hisui', 'paldea']
STATS = ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']
# Megaevolución: 1 = la especie tiene mega; 2 = no tiene, pero sí alguna evolución posterior de su línea.
own_mega = {i for i in range(1, 1026) if any('-mega' in v['pokemon']['name']
            for v in json.load(open(f'cache/pokemon-species_{i}.json', encoding='utf-8'))['varieties'])}
descendants = {}
phase = {}  # 0 = ÚNICA (la cadena tiene una sola especie); si no, profundidad en la cadena
for f in glob.glob('cache/evolution-chain_*.json'):
    def collect(n):
        i = int(n['species']['url'].rstrip('/').split('/')[-1])
        below = set()
        for x in n['evolves_to']: below |= {int(x['species']['url'].rstrip('/').split('/')[-1])} | collect(x)
        descendants[i] = below
        return below
    chain = json.load(open(f, encoding='utf-8'))['chain']
    collect(chain)
    def depth(n, level, total):
        phase[int(n['species']['url'].rstrip('/').split('/')[-1])] = 0 if total == 1 else level
        for x in n['evolves_to']: depth(x, level + 1, total)
    def count(n): return 1 + sum(count(x) for x in n['evolves_to'])
    depth(chain, 1, count(chain))
# PokeAPI une a Phione y Manaphy en una cadena, pero ninguno evoluciona del otro.
phase[489] = phase[490] = 0

rows = []
for i in range(1, 1026):
    s = json.load(open(f'cache/pokemon-species_{i}.json', encoding='utf-8'))
    p = json.load(open(f'cache/pokemon_{i}.json', encoding='utf-8'))
    names = [v['pokemon']['name'] for v in s['varieties']]
    mega = 1 if i in own_mega else 2 if descendants.get(i, set()) & own_mega else 0
    reg = 0
    for n in names:
        m = re.search(r'-(alola|galar|hisui|paldea)', n)
        if m and 'cap' not in n and 'totem' not in n: reg |= 1 << REGIONS.index(m.group(1))
    method = result[i][0]
    assert method in METHODS, (i, method)
    extra_method = 1 if has_extra_condition(method, result[i][1], i) else 0
    # Mejor stat: bits en el orden de STATS; con 3 o más empatadas queda 0 (NO TIENE).
    base = {x['stat']['name']: x['base_stat'] for x in p['stats']}
    top = [k for k in STATS if base[k] == max(base.values())]
    best = sum(1 << STATS.index(k) for k in top) if len(top) <= 2 else 0
    # 2º color experimental (desde el sprite): 0 = ninguno; si no, índice del color + 1.
    c2 = second_color(f'sprites/{i}.png', s['color']['name'])[0]
    color2 = COLORS.index(c2) + 1 if c2 else 0
    rows.append(f"{p['height']}|{p['weight']}|{mega}|{reg}|{METHODS.index(method)}|{best}|{phase[i]}|{color2}|{extra_method}")
open('extra.txt', 'w').write(';'.join(rows))
print(len(rows), 'filas;', sum(r.split('|')[2] == '1' for r in rows), 'con mega;', sum(r.split('|')[2] == '2' for r in rows), 'con mega en su evolución;',
      sum(r.split('|')[3] != '0' for r in rows), 'con forma regional')
