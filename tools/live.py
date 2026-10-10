"""Redraws the DODGE row of the projects board from DODGE's public daily data.

Runs anywhere with Python 3 and no packages: text comes from tools/glyphs.json, data from
https://raw.githubusercontent.com/GautamTalksDev/dodge/data/latest.json (DODGE's own output).
Usage: python tools/live.py [path-to-latest.json]
"""
import json, os, re, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write, GREEN
import boards

SRC = 'https://raw.githubusercontent.com/GautamTalksDev/dodge/data/latest.json'
FONTS_FULL = ('inter500', 'inter600', 'gmono500')   # everything the row draws; cached for CI
MONTHS = 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()


def load(path=None):
    if path:
        return json.load(open(path, encoding='utf-8'))
    req = urllib.request.Request(SRC, headers={'User-Agent': 'GautamTalksDev-profile-card'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def facts(d):
    tot = d['totals']
    day = str(d.get('day') or d['generated_at'][:10])
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        raise SystemExit(f'unexpected date format in DODGE data: {day!r}')
    closest = min((float(c['miss_km']) for c in d.get('closest', [])), default=None)
    u5, u1 = int(tot['under_5km']), int(tot['under_1km'])
    if not (0 <= u1 <= u5 < 10_000_000):
        raise SystemExit(f'implausible DODGE totals: {u5} {u1}')
    return {'u5': u5, 'u1': u1, 'closest_m': None if closest is None else round(closest * 1000),
            'day': day, 'hours': int(d['stats'].get('hours', 24))}


def dodge_row(F):
    y, m, dd = F['day'].split('-')
    mon = MONTHS[int(m) - 1]
    nice = f'{int(dd)} {mon.title()}'
    meta = f'RUN {dd} {mon} · {F["u1"]:,} UNDER 1 KM'
    if F['closest_m'] is not None:
        meta += f' · CLOSEST {F["closest_m"]} M'
    return dict(since='06 OCT', name='DODGE', status='LIVE', color=GREEN,
                what=f'Who makes Starlink dodge: {F["u5"]:,} passes under 5 km, {nice}.',
                what_n=f'Who makes Starlink dodge. {F["u5"]:,} passes under 5 km.',
                meta_n=meta,
                title=(f'DODGE, who makes Starlink dodge: {F["u5"]:,} predicted passes within 5 km of a Starlink satellite in the '
                       f'{F["hours"]} hours screened by the {nice} run, {F["u1"]:,} within 1 km. Screening grade, not collision '
                       'probability. Status: live.'))


def build_all(F):
    R = dodge_row(F)
    out = []
    for th in ('dark', 'light'):
        for n in (False, True):
            sfx = f'-{th}' + ('-n' if n else '')
            svg = boards.row(R, th, n, seed=200)
            out.append((f'row-dodge{sfx}.svg', svg))
    return out


if __name__ == '__main__':
    F = facts(load(sys.argv[1] if len(sys.argv) > 1 else None))
    for name, svg in build_all(F):
        print(name, write(name, svg))
    print(F)
