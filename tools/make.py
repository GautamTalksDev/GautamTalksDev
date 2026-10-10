"""Builds every image in ../assets. Run locally:

    PROFILE_FONTS=<folder with the OFL font files> python tools/make.py [hero] [boards] [cards] [extras] [live]

Fonts (all SIL OFL): Inter, Geist, Geist Mono, Instrument Serif, Fraunces, Nunito, Manrope, B612 Mono.
Text becomes paths, so no SVG needs a font at view time. Only the DODGE row is rebuilt in CI
(tools/live.py), from tools/glyphs.json.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write

what = sys.argv[1:] or ['hero', 'boards', 'cards', 'extras', 'live']
sizes = {}
if 'hero' in what:
    import hero
    for th in ('dark', 'light'):
        sizes[f'hero-{th}.svg'] = write(f'hero-{th}.svg', hero.hero(th))
        sizes[f'hero-{th}-n.svg'] = write(f'hero-{th}-n.svg', hero.hero(th, narrow=True))
if 'boards' in what:
    import boards
    for name, svg in boards.build_all():
        sizes[name] = write(name, svg)
if 'cards' in what:
    import cards
    for name, svg in cards.build_all():
        sizes[name] = write(name, svg)
if 'extras' in what:
    import extras
    for name, svg in extras.build_all():
        sizes[name] = write(name, svg)
if 'live' in what:
    import live, glyphs as G
    for name, svg in live.build_all(live.facts(live.load(os.environ.get('DODGE_JSON')))):
        sizes[name] = write(name, svg)
    G.save_cache(keys_full_ascii=live.FONTS_FULL)
    print('glyph cache written')
for k, v in sizes.items():
    print(f'{k:34s} {v/1024:7.1f} KB')
