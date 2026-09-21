"""Clasifica el método por el que se obtiene cada especie (forma por defecto),
usando el dato del juego más reciente que PokeAPI tenga para esa evolución."""
import json, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
VG = json.load(open('cache/vg_order.json'))
STONES = {'fire-stone','water-stone','thunder-stone','leaf-stone','moon-stone','sun-stone',
          'shiny-stone','dusk-stone','dawn-stone','ice-stone'}

det = {}
for f in glob.glob('cache/evolution-chain_*.json'):
    c = json.load(open(f, encoding='utf-8'))
    def walk(n):
        det[int(n['species']['url'].rstrip('/').split('/')[-1])] = n['evolution_details']
        for x in n['evolves_to']: walk(x)
    walk(c['chain'])

def name(v): return v.get('name', v) if isinstance(v, dict) else v

def is_default_form(d):
    req, out = name(d.get('required_pokemon_form')), name(d.get('evolved_pokemon_form'))
    regional = ('-alola', '-galar', '-hisui', '-paldea')
    return not (req and any(r in req for r in regional)) and not (out and any(r in out for r in regional))

def classify(d):
    t = d['trigger']['name']
    if t == 'trade': return 'INTERCAMBIO'
    if t == 'use-item':
        return 'PIEDRA' if name(d['item']) in STONES else 'OBJETO'
    if t in ('use-move', 'agile-style-move', 'strong-style-move'): return 'MOVIMIENTO'
    if t in ('level-up', 'in-battle-level-up'):
        if d.get('min_happiness') or d.get('min_affection'): return 'AMISTAD'
        if d.get('known_move') or d.get('known_move_type'): return 'MOVIMIENTO'
        if d.get('held_item'): return 'OBJETO'
        if d.get('min_level'): return 'NIVEL'
        if d.get('location'): return 'LUGAR'
    return 'ESPECIAL'

def summary(d):
    keys = [k for k, v in d.items() if v not in (None, False, '', []) and k not in ('trigger', 'is_default')]
    return d['trigger']['name'] + ' ' + ' '.join(f'{k}={name(d[k])}' for k in keys)

# Correcciones manuales: el dato "más reciente" de PokeAPI es el último método
# introducido, no el vigente en los últimos juegos.
OVERRIDES = {
    350: 'INTERCAMBIO',  # Milotic: en EV/Z-A es intercambio con Escama Bella (belleza sólo Gen 3/4/ROZA/DBPR)
}

result = {}
for i in range(1, 1026):
    s = json.load(open(f'cache/pokemon-species_{i}.json', encoding='utf-8'))
    if not s['evolves_from_species']:
        result[i] = ('NINGUNO', [], []); continue
    ds = [d for d in det.get(i, []) if is_default_form(d)] or det.get(i, [])
    top = max(VG.get(name(d.get('version_group')), 0) for d in ds)
    latest = [d for d in ds if VG.get(name(d.get('version_group')), 0) == top]
    classes = sorted({classify(d) for d in latest})
    result[i] = (OVERRIDES.get(i) or (classes[0] if len(classes) == 1 else '?'.join(classes)), latest, ds)

if __name__ == '__main__':
    for i, (c, latest, ds) in result.items():
        allc = sorted({classify(d) for d in ds})
        if c == 'NINGUNO': continue
        if '?' in c or len(allc) > 1 or c in ('ESPECIAL', 'LUGAR'):
            s = json.load(open(f'cache/pokemon-species_{i}.json', encoding='utf-8'))['name']
            print(f'{i} {s}: {c}   <- latest: ' + ' || '.join(summary(d) for d in latest) + f'   [historial: {",".join(allc)}]')
    json.dump({i: r[0] for i, r in result.items()}, open('evo_method.json', 'w'))
