"""Descarga (con caché) species, pokemon y cadenas evolutivas de PokeAPI para #1-#1025."""
import json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

CACHE = sys.argv[1] if len(sys.argv) > 1 else 'cache'
os.makedirs(CACHE, exist_ok=True)

def get(url):
    key = url.rstrip('/').replace('https://pokeapi.co/api/v2/', '').replace('/', '_')
    path = os.path.join(CACHE, key + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f: return json.load(f)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'pokeduelo-data/1.0'})
            data = json.load(urllib.request.urlopen(req, timeout=30))
            break
        except Exception as e:
            if attempt == 3: raise
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f)
    return data

ids = range(1, 1026)
with ThreadPoolExecutor(16) as ex:
    species = list(ex.map(lambda i: get(f'https://pokeapi.co/api/v2/pokemon-species/{i}/'), ids))
    list(ex.map(lambda i: get(f'https://pokeapi.co/api/v2/pokemon/{i}/'), ids))
    chains = sorted({s['evolution_chain']['url'] for s in species})
    list(ex.map(get, chains))
# Sprites que usa el juego, para el 2º color experimental (tools/sprite_colors.py).
os.makedirs('sprites', exist_ok=True)
def sprite(i):
    path = f'sprites/{i}.png'
    if not os.path.exists(path):
        urllib.request.urlretrieve(f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{i}.png', path)
with ThreadPoolExecutor(16) as ex: list(ex.map(sprite, ids))
print('ok', len(species), 'species,', len(chains), 'chains')
