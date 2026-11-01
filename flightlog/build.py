"""Flight Log: draws every image in ../assets and writes ../README.md from ../profile.toml and live data.

Local build (cuts glyphs from the font files):
    FLIGHTLOG_FONTS=<folder with archivo-var.woff2, plexmono-*.woff2> python flightlog/build.py
CI build (Python standard library only; glyph outlines come from flightlog/glyphs.json):
    python3 flightlog/build.py

Every image comes in a dark and a light version whose background is GitHub's own page colour, so on the
profile the edges disappear and the README reads as one designed page. If a viewer's GitHub theme and
system theme disagree, an image shows as a plain panel, never as unreadable text.

Live data, fetched in memory on every build:
  * GitHub contribution calendar (GraphQL; needs GITHUB_TOKEN or GH_TOKEN). CONTRIB_JSON=<file> overrides.
  * DODGE's public daily screen (latest.json from the dodge repo's data branch). DODGE_JSON=<file> overrides.
  * The main language of every hangar repository (GitHub REST).
If a source fails, the last good values in flightlog/live.json are used, so a build never breaks the page.
"""
import json, math, os, random, re, sys, tomllib, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets')
sys.path.insert(0, HERE)
import glyphs as G
import terrain as TR

DODGE_SRC = 'https://raw.githubusercontent.com/GautamTalksDev/dodge/data/latest.json'
LIVE = os.path.join(HERE, 'live.json')
W = 1200
THEMES = ('dark', 'light')
MONTHS = 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split()

# fixed colours (the same in both themes)
C = dict(flame='#FF5A1F', hot='#FFB36B', sky0='#03050A', sky1='#0A1222')
# theme colours: page is GitHub's own background, so frameless images melt into the profile
TH = {
    'dark': dict(page='#0D1117', ink='#F2F4F8', soft='#C9D0DD', dim='#8A94A8', faint='#4A5368', line='#FFFFFF', line_op=.11,
                 chip='#FFFFFF', chip_op=.05, chip_line=.15, cmd='#C9D0DD', stars=True, topo='#FFFFFF', topo_op=.07,
                 shadow='#000000', shadow_op=.6, accent=C['hot'], tipcore='#FFFFFF', glow_op=.09, planet0='#3A4E78',
                 planet1='#0E1830', rim='#9CC8FF', green='#4BE08B', amber='#FFC24B', grey='#9AA3B5', sky='#8AB4FF', red='#FF6B5E',
                 stamp_op=.92),
    'light': dict(page='#FFFFFF', ink='#14151A', soft='#3D434C', dim='#59636E', faint='#9AA1AB', line='#14151A', line_op=.12,
                  chip='#14151A', chip_op=.04, chip_line=.16, cmd='#2B3038', stars=False, topo='#9C7B55', topo_op=.2,
                  shadow='#5C4A2E', shadow_op=.16, accent='#D63600', tipcore='#FF5A1F', glow_op=.10, planet0='#6A7EA8',
                  planet1='#26324F', rim='#5E7FB8', green='#1A7F37', amber='#9A6700', grey='#6E7781', sky='#0969DA', red='#CF222E',
                  stamp_op=.88),
}
STATUS = {'live': ('LIVE', 'green'), 'beta': ('BETA', 'amber'), 'parked': ('PARKED', 'grey'), 'docked': ('DOCKED', 'sky')}
LANG = {'TypeScript': '#3178C6', 'JavaScript': '#F1E05A', 'Python': '#3572A5', 'Rust': '#DEA584', 'Go': '#00ADD8',
        'C++': '#F34B7D', 'C': '#555555', 'Java': '#B07219', 'Shell': '#89E051', 'HTML': '#E34C26', 'CSS': '#563D7C'}


def status(s, th):
    lab, key = STATUS[s]
    return lab, TH[th][key]


# =============================================================== data
def load_profile():
    with open(os.path.join(ROOT, 'profile.toml'), 'rb') as f:
        P = tomllib.load(f)
    validate_profile(P)
    return P


# ---------------------------------------------------------------- input validation (everything in profile.toml)
SAFE_URL = re.compile(r'https://[A-Za-z0-9.-]+(?::\d{2,5})?(?:/[A-Za-z0-9._~%!$&()*+,;=:@/?#-]*)?'
                      r'|mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.ASCII)
GH_REPO = re.compile(r'https://github\.com/([A-Za-z0-9-]{1,39})/([A-Za-z0-9._-]{1,100})/?', re.ASCII)
GH_HOSTS = {'github.com', 'www.github.com'}
BAD_GH_HOSTS = {'gist.github.com', 'raw.githubusercontent.com', 'gist.githubusercontent.com', 'objects.githubusercontent.com'}
CONTROL = re.compile(r'[\x00-\x1f\x7f]')
VISUALS = {'molecule', 'bitgrid', 'hexscan', 'crowd', 'plimsoll', 'orbit'}
PATCHES = {'seal', 'clock', 'flame', 'orbit', 'shield'}


def validate_profile(P):
    """Fail closed: a bad link or a stray control character stops the build before anything is drawn."""
    def text(v, where, limit=400):
        if not isinstance(v, str) or CONTROL.search(v) or len(v) > limit:
            raise SystemExit(f'profile.toml: {where} must be plain text under {limit} characters')

    def url(v, where):
        text(v, where, 300)
        if not SAFE_URL.fullmatch(v):
            raise SystemExit(f'profile.toml: {where} is not an https or mailto link: {v!r}')

    url(P['identity']['site'], 'identity.site')
    for k, v in P['identity'].items():
        text(v, f'identity.{k}')
    for sect in ('links', 'missions', 'orbit', 'expeditions', 'hangar'):
        for i, item in enumerate(P.get(sect, [])):
            for k, v in item.items():
                where = f'{sect}[{i}].{k}'
                if k == 'url':
                    url(v, where)
                elif k == 'links':
                    for j, l in enumerate(v):
                        url(l['url'], f'{where}[{j}].url')
                        text(l['label'], f'{where}[{j}].label', 40)
                elif k == 'published':
                    for j, s in enumerate(v):
                        text(s, f'{where}[{j}]', 40)
                elif isinstance(v, str):
                    text(v, where, 60 if k == 'name' else 400)
    for i, m in enumerate(P['missions']):
        if m['status'] not in STATUS or m['patch'] not in PATCHES or not re.fullmatch(r'#[0-9A-Fa-f]{6}', m['color']):
            raise SystemExit(f'profile.toml: missions[{i}] has an unknown status, patch or colour')
    for sect in ('missions', 'orbit', 'expeditions', 'hangar'):
        for i, item in enumerate(P[sect]):
            if not item.get('url'):
                raise SystemExit(f'profile.toml: {sect}[{i}] ({item.get("name")}) has no public url; private work never goes on this page')
    for i, o in enumerate(P['orbit']):
        if o['status'] not in STATUS:
            raise SystemExit(f'profile.toml: orbit[{i}].status must be one of {sorted(STATUS)}')
    for i, e in enumerate(P['expeditions']):
        if e['visual'] not in VISUALS:
            raise SystemExit(f'profile.toml: expeditions[{i}].visual must be one of {sorted(VISUALS)}')
    for u in all_urls(P):
        host = (urllib.parse.urlsplit(u).hostname or '').lower()
        if host in BAD_GH_HOSTS:
            raise SystemExit(f'profile.toml: links to {host} are not allowed: {u}')
        if host in GH_HOSTS and not GH_REPO.fullmatch(u):
            raise SystemExit(f'profile.toml: GitHub links must be plain https://github.com/owner/repo (so they can be checked public): {u}')


def all_urls(P):
    out = [P['identity']['site']] + [l['url'] for l in P.get('links', [])]
    for s in ('missions', 'orbit', 'expeditions', 'hangar'):
        for x in P.get(s, []):
            if x.get('url'):
                out.append(x['url'])
            out += [l['url'] for l in x.get('links', [])]
    return out


# ---------------------------------------------------------------- network: fixed hosts, no redirects elsewhere, size cap
FETCH_HOSTS = {'api.github.com', 'raw.githubusercontent.com'}
MAX_BYTES = 4 * 1024 * 1024


class _SameHosts(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = urllib.parse.urlsplit(newurl)
        if new.scheme != 'https' or new.hostname not in FETCH_HOSTS:
            raise ValueError(f'refusing a redirect to {new.scheme}://{new.hostname}')
        out = super().redirect_request(req, fp, code, msg, headers, newurl)
        if out is not None and new.hostname != urllib.parse.urlsplit(req.full_url).hostname:
            for h in [h for h in out.headers if h.lower() == 'authorization']:
                del out.headers[h]
            out.unredirected_hdrs.pop('Authorization', None)
        return out


_OPENER = urllib.request.build_opener(_SameHosts)


def _get_json(url, body=None, headers=None):
    u = urllib.parse.urlsplit(url)
    if u.scheme != 'https' or u.hostname not in FETCH_HOSTS:
        raise ValueError(f'refusing to fetch {url}')
    req = urllib.request.Request(url, data=body, headers={'User-Agent': 'GautamTalksDev-flightlog', 'Accept': 'application/json', **(headers or {})})
    with _OPENER.open(req, timeout=30) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f'{u.hostname} sent more than {MAX_BYTES} bytes')
    return json.loads(data)


def _token():
    """Only in CI: the workflow's own read-only GITHUB_TOKEN, whose viewer is the Actions bot, so it sees exactly
    what a logged-out visitor sees. A local run never uses a personal token (that viewer could see his private
    contributions); locally the build uses CONTRIB_JSON or the last good values. Never printed or written."""
    return os.environ.get('GITHUB_TOKEN') if os.environ.get('GITHUB_ACTIONS') == 'true' else None


def fetch_contrib(handle):
    path = os.environ.get('CONTRIB_JSON')
    if path:
        raw = json.load(open(path, encoding='utf-8'))
    else:
        if not _token():
            raise RuntimeError('no CI token; locally set CONTRIB_JSON or rely on the last good values')
        q = ('query($l:String!){user(login:$l){contributionsCollection{restrictedContributionsCount contributionCalendar{'
             'totalContributions weeks{contributionDays{date contributionCount}}}}}}')
        raw = _get_json('https://api.github.com/graphql', json.dumps({'query': q, 'variables': {'l': handle}}).encode(),
                        {'Authorization': f'bearer {_token()}', 'Content-Type': 'application/json'})
    coll = raw['data']['user']['contributionsCollection']
    if int(coll['restrictedContributionsCount']) != 0:
        # private contribution counts would be mixed in; the page promises public numbers only
        raise ValueError('the calendar includes private contribution counts; refusing to draw them')
    cal = coll['contributionCalendar']
    weeks = [sum(int(d['contributionCount']) for d in wk['contributionDays']) for wk in cal['weeks']]
    first = cal['weeks'][0]['contributionDays'][0]['date']
    last = cal['weeks'][-1]['contributionDays'][-1]['date']
    for d in (first, last):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d, re.ASCII):
            raise ValueError(f'bad date {d!r}')
        date.fromisoformat(d)
    total = int(cal['totalContributions'])
    if not (40 <= len(weeks) <= 60 and 1 <= total < 1_000_000 and all(0 <= w < 100_000 for w in weeks)):
        raise ValueError('implausible contribution calendar')
    return {'weeks': weeks, 'week0': first, 'last_day': last, 'total': total}


def fetch_dodge():
    path = os.environ.get('DODGE_JSON')
    d = json.load(open(path, encoding='utf-8')) if path else _get_json(DODGE_SRC)
    day = str(d.get('day') or d['generated_at'][:10])
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day, re.ASCII):
        raise ValueError(f'bad DODGE day {day!r}')
    date.fromisoformat(day)
    u5, u1 = int(d['totals']['under_5km']), int(d['totals']['under_1km'])
    if not (0 <= u1 <= u5 < 10_000_000):
        raise ValueError('implausible DODGE totals')
    return {'u5': u5, 'u1': u1, 'day': day}


def github_repo_urls(P):
    urls = [x['url'] for s in ('missions', 'orbit', 'expeditions', 'hangar') for x in P.get(s, []) if x.get('url')]
    return sorted({u.rstrip('/') for u in urls if GH_REPO.fullmatch(u)})


def fetch_repo(url):
    """Public metadata for one repository. Locally this runs WITHOUT a token, so a private repository is
    simply invisible (404); in CI the token is scoped to this public repository. Either way we insist on
    private == false before the page may link to it."""
    o, r = GH_REPO.fullmatch(url).groups()
    hdr = {'Authorization': f'bearer {_token()}'} if os.environ.get('FLIGHTLOG_CI') == '1' and _token() else {}
    try:
        d = _get_json(f'https://api.github.com/repos/{o}/{r}', headers=hdr)
    except urllib.error.HTTPError as e:
        if e.code in (404, 410, 451) or (e.code == 403 and e.headers.get('X-RateLimit-Remaining') != '0'):
            raise SystemExit(f'{url} answered {e.code}: not a public repository; remove it from profile.toml')
        raise
    if d.get('private') is not False or d.get('visibility') not in ('public', None):
        raise SystemExit(f'{url} is not a public repository; the README only links to public work')
    lang = d.get('language') or ''
    if not re.fullmatch(r'[\w+#. -]{0,24}', lang, re.ASCII):
        raise ValueError(f'odd language {lang!r}')
    return {'language': lang, 'public': True}


def live_data(P):
    """Fresh values where possible, last good values otherwise; the result is saved for the next build.
    Repository checks fail closed: a repository never confirmed public stops the build."""
    old = json.load(open(LIVE, encoding='utf-8')) if os.path.exists(LIVE) else {}
    out = {k: old[k] for k in ('contrib', 'dodge', 'repos') if k in old}
    for key, fn in (('contrib', lambda: fetch_contrib(P['identity']['handle'])), ('dodge', fetch_dodge)):
        try:
            out[key] = fn()
        except Exception as e:  # keep the page up; the log says what went stale (never the token)
            print(f'live data: {key} failed ({type(e).__name__}); using the last good value', file=sys.stderr)
            if key not in out:
                raise SystemExit(f'live data: no {key} yet and the fetch failed')
    repos = {}
    for u in github_repo_urls(P):
        try:
            repos[u] = fetch_repo(u)
        except SystemExit:
            raise
        except Exception as e:
            if u in out.get('repos', {}):
                print(f'live data: {u} failed ({type(e).__name__}); using the last good value', file=sys.stderr)
                repos[u] = out['repos'][u]
            else:
                raise SystemExit(f'could not confirm {u} is public; refusing to link it')
    out['repos'] = repos
    with open(LIVE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, sort_keys=True)
    return out


def stale_sources(L, days=3):
    today = datetime.now(timezone.utc).date()
    old = [k for k, d in (('contrib', L['contrib']['last_day']), ('dodge', L['dodge']['day'])) if (today - date.fromisoformat(d)).days > days]
    return old


def iso(d):
    return d if isinstance(d, date) else date.fromisoformat(str(d))


def dmy(d, year=True):
    d = iso(d)
    return f'{d.day} {MONTHS[d.month - 1]}' + (f' {d.year}' if year else '')


# =============================================================== drawing helpers
def T(txt, font, size, x, y, anchor='start', ls=0.0, fill=None, extra=''):
    return G.text(txt, font, size, x, y, anchor, ls=ls, fill=fill, extra=extra)


def M(txt, font, size, ls=0.0):
    return G.measure(txt, font, size, ls)


def capH(font, size):
    upm, c, _ = G.metrics(font)
    return c * size / upm


def fit(txt, font, maxw, ls_em=0.0, hi=300.0):
    lo, best = 4.0, 4.0
    while hi - lo > 0.25:
        mid = (lo + hi) / 2
        if M(txt, font, mid, mid * ls_em) <= maxw:
            best, lo = mid, mid
        else:
            hi = mid
    return round(best, 1)


def wrap(txt, font, size, maxw, max_lines=None):
    lines, cur = [], ''
    for wd in txt.split():
        trial = (cur + ' ' + wd).strip()
        if cur and M(trial, font, size) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and M(lines[-1] + '…', font, size) > maxw:
            head, sep, _ = lines[-1].rpartition(' ')
            lines[-1] = head if sep else lines[-1][:-1]
        lines[-1] += '…'
    return lines


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def doc(w, h, label, body, css=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{css}</style>{G.take_defs()}{body}</svg>')


REDUCE = '.rm-show{display:none}@media (prefers-reduced-motion:reduce){*{animation:none!important}.rm-hide{display:none}.rm-show{display:inline}}'
GLOW = ('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
        '<filter id="glow2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>')


def page(w, h, th):
    """The frameless background: GitHub's own page colour, edge to edge."""
    return f'<rect width="{w:.0f}" height="{h:.0f}" fill="{TH[th]["page"]}"/>'


def hairline(y, th, x0=0, x1=W):
    t = TH[th]
    return f'<path d="M{x0} {y:.1f}H{x1}" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>'


def stars(w, h, n, seed, twinkle=True, avoid=None):
    """A star field; `avoid` is a list of (x0, y0, x1, y1) boxes kept clear so no star sits behind text."""
    rnd = random.Random(seed)
    out = []
    for k in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.choice((.5, .6, .7, .8, 1.0, 1.2, 1.5))
        o = rnd.uniform(.15, .9)
        if avoid and any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in avoid):
            continue
        cls = f' class="tw" style="animation-delay:{rnd.uniform(0, 5):.1f}s"' if twinkle and k % 11 == 0 else ''
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{o:.2f}"{cls}/>')
    return ''.join(out)


def topo_lines(w, h, seed, color, opacity, levels=8, width=1.0, fade=None):
    """Contour rings of a small random terrain stretched over w x h: the Climb Log's paper as a texture.
    fade=(x0, x1) fades the rings out from x0 to x1 so they never sit under text."""
    rnd = random.Random(seed)
    peaks = [(rnd.uniform(.2, .8), rnd.uniform(.25, .75), rnd.uniform(.5, 1), rnd.uniform(.12, .25), rnd.uniform(.2, .35)) for _ in range(3)]
    g = TR.heightfield(48, peaks, ripple=.02, seed=seed)
    d = ''
    for k in range(1, levels + 1):
        for lp in TR.contours(g, k / (levels + 1)):
            d += 'M' + 'L'.join(f'{x * w:.0f} {y * h:.0f}' for x, y in lp[::2]) + 'Z'
    path = f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="{width}" stroke-linejoin="round"/>'
    if not fade:
        return path
    mid = f'tf{seed}'
    return (f'<defs><linearGradient id="{mid}g" gradientUnits="userSpaceOnUse" x1="{fade[0]}" y1="0" x2="{fade[1]}" y2="0">'
            f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="{mid}"><rect width="{w:.0f}" height="{h:.0f}" fill="url(#{mid}g)"/></mask></defs><g mask="url(#{mid})">{path}</g>')


def chip(x, y, txt, color, font='p600', size=13, h=28, anchor='start', dot=True, fill_op=.10):
    """A status pill with an optional lamp; returns (svg, width)."""
    tw = M(txt, font, size, 1.2)
    w = tw + (40 if dot else 24)
    x0 = x if anchor == 'start' else x - w
    out = f'<rect x="{x0:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{color}" fill-opacity="{fill_op}" stroke="{color}" stroke-opacity=".38"/>'
    tx = x0 + (28 if dot else 12)
    if dot:
        out += f'<circle cx="{x0 + 15:.1f}" cy="{y + h / 2:.1f}" r="4" fill="{color}"/>'
    out += T(txt, font, size, tx, y + h / 2 + capH(font, size) / 2, ls=1.2, fill=color)
    return out, w


def arrow(x, y, color, r=16, ring_op=.22):
    """The little 'opens a link' mark: an arrow in a ring, centred on (x, y)."""
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" stroke-opacity="{ring_op}"/>'
            f'<path d="M{x - 5} {y + 5}l10-10M{x - 3} {y - 5}h8v8" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')


def css_ease_time(x1, y1, x2, y2, progress):
    """Time fraction at which a CSS cubic-bezier(x1,y1,x2,y2) timing reaches the given progress."""
    def B(p1, p2, s):
        return 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if B(y1, y2, mid) < progress:
            lo = mid
        else:
            hi = mid
    return B(x1, x2, (lo + hi) / 2)


def odometer(value, font, size, x_right, y, color, delay, uid, dur=1.6):
    """Digits that spin once and land on the value; the resting state IS the value (reduced motion safe)."""
    lh = size * 1.3
    x = x_right - M(value, font, size)
    top = y - capH(font, size) - size * .18
    out = [f'<clipPath id="od{uid}"><rect x="{x - 4:.1f}" y="{top:.1f}" width="{x_right - x + 8:.1f}" height="{capH(font, size) + size * .4:.1f}"/></clipPath>',
           f'<g class="odf{uid}"><g clip-path="url(#od{uid})">']
    css = [f'.odf{uid}{{animation:odf{uid} .35s {delay:.2f}s both}}@keyframes odf{uid}{{from{{opacity:0}}}}']
    for k, ch in enumerate(value):
        adv = M(ch, font, size)
        if ch.isdigit():
            seq = list(range(10)) + list(range(int(ch) + 1))
            col = ''.join(T(str(dg), font, size, x + adv / 2, y + i * lh, 'middle', fill=color) for i, dg in enumerate(seq))
            final = -(len(seq) - 1) * lh
            cls = f'o{uid}_{k}'
            out.append(f'<g class="{cls}" style="transform:translateY({final:.1f}px)">{col}</g>')
            css.append(f'.{cls}{{animation:{cls} {dur}s {delay + k * .07:.2f}s cubic-bezier(.2,.75,.1,1) both}}@keyframes {cls}{{from{{transform:translateY(0)}}}}')
        else:
            out.append(T(ch, font, size, x, y, fill=color))
        x += adv
    out.append('</g></g>')
    return ''.join(out), ''.join(css)


# =============================================================== hero: the climb log rises into the flight log
# A layered-paper terrain model of his real numbers floats on the page. Elevation is public contributions
# (1 m = 1 contribution, last 12 months), so the summit is today's total. The route climbs it with a camp
# at every release date from profile.toml; from the summit the trajectory leaves the map.
PEAKS = [(0.58, 0.36, 1.0, 0.17, 0.15), (0.84, 0.22, .42, .12, .11), (0.28, 0.27, .32, .13, .12),
         (0.84, 0.68, .24, .11, .10), (0.40, 0.56, .16, .10, .09), (0.70, 0.50, .22, .09, .12)]
ROUTE = [(0.10, 0.80), (0.24, 0.85), (0.38, 0.82), (0.50, 0.76), (0.62, 0.66), (0.52, 0.59), (0.66, 0.53),
         (0.55, 0.47), (0.63, 0.42), (0.58, 0.36)]
LAYERS = 22
MAP_OX, MAP_OY, MAP_A, MAP_B, MAP_KZ, MAP_T = 690, 476, 440, 190, 280, 14
PAPER = dict(sheet='#EFE7D6', top0='#ECE3CF', top1='#FBF8F0', rise0='#CDBEA2', rise1='#E4D9C4', line='#9C7B55',
             index='#7A5C3A', side_l='#D8CAB0', side_r='#C1AF92', ink='#1D1A16', dim='#6E655A', card='#FBF8F1',
             edge='#D9D0BE', route='#D63600')
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']


def proj(x, y, z=0.0):
    return (MAP_OX + (x - y) * MAP_A, MAP_OY + (x + y) * MAP_B - z * MAP_KZ)


def _mix(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * t):02X}' for x, y in zip(a, b))


def _loops_d(loops, z, step=2):
    d = ''
    for lp in loops:
        pts = lp[::step] if len(lp) > 24 else lp
        d += 'M' + 'L'.join('%.0f %.0f' % proj(x, y, z) for x, y in pts) + 'Z'
    return d


def _catmull_plane(pts, per=24):
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                   + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1])
    return out


def cum_through(cal, d):
    """Public contributions from the start of the window through the end of day d (spread evenly within a week)."""
    weeks, week0 = cal['weeks'], iso(cal['week0'])
    f = ((iso(d) - week0).days + 1) / 7
    i = max(0, min(int(f), len(weeks)))
    return sum(weeks[:i]) + (weeks[i] * (f - i) if i < len(weeks) else 0)


def camps_from(P):
    """Releases from profile.toml, grouped into camps when they land within two days of each other."""
    rel = sorted([(iso(m['launched']), m['name']) for m in P['missions']] +
                 [(iso(o['since']), o['name']) for o in P['orbit'] if o['status'] != 'docked'])
    camps = []
    for d, name in rel:
        if camps and (d - camps[-1]['end']).days <= 2:
            camps[-1]['end'] = d
            camps[-1]['names'].append(name)
        else:
            camps.append({'start': d, 'end': d, 'names': [name]})
    return camps


def hero(P, L, th, n=False):
    t_ = TH[th]
    I = P['identity']
    cal = L['contrib']
    weeks, total = cal['weeks'], cal['total']
    week0 = iso(cal['week0'])
    last = iso(cal['last_day'])
    peak_i = max(range(len(weeks)), key=lambda i: weeks[i])
    lift_i = next((i for i, v in enumerate(weeks) if v >= max(weeks) * .35), peak_i)
    base_day = week0 + timedelta(days=7 * lift_i)
    W_, H = (720, 1350) if n else (W, 900)
    css = []
    b = ['<defs>'
         f'<radialGradient id="tipglow"><stop offset="0" stop-color="{C["flame"]}" stop-opacity="{.22 if th == "dark" else .08}"/><stop offset="1" stop-color="{C["flame"]}" stop-opacity="0"/></radialGradient>'
         f'<radialGradient id="mapglow"><stop offset="0" stop-color="#FFE9C7" stop-opacity="{.10 if th == "dark" else 0}"/><stop offset="1" stop-color="#FFE9C7" stop-opacity="0"/></radialGradient>'
         f'{GLOW}<filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="22"/></filter>'
         '</defs>']
    b.append(page(W_, H, th))
    if t_['stars']:
        b.append(f'<g class="starsin">{stars(W_, H, 230 if not n else 170, 7)}</g>')
        train = ''.join(f'<circle cx="{-k * 11:.0f}" cy="{k * 1.6:.1f}" r="1.25" fill="#fff" opacity="{.9 - k * .07:.2f}"/>' for k in range(9))
        b.append(f'<g class="train rm-hide" style="transform:translate(-120px,250px)">{train}</g>')
        css.append('.train{animation:train 46s 8s linear infinite}@keyframes train{0%{transform:translate(-120px,250px)}55%{transform:translate(1330px,150px)}100%{transform:translate(1330px,150px)}}')

    # ---------------- the floating map
    grid = TR.heightfield(110, PEAKS, ripple=.025, seed=1.3)
    b.append(('<g transform="translate(-174 392) scale(.78)">' if n else '<g>') + '<g class="float">')
    b.append('<g class="sheetin">')
    cx_, cy_ = proj(.5, .5)
    b.append(f'<ellipse cx="{cx_:.0f}" cy="{cy_ + 60:.0f}" rx="{MAP_A:.0f}" ry="{MAP_B * .9:.0f}" fill="{t_["shadow"]}" opacity="{t_["shadow_op"]}" filter="url(#shadow)"/>')
    b.append(f'<ellipse cx="{cx_:.0f}" cy="{cy_:.0f}" rx="{MAP_A * 1.25:.0f}" ry="{MAP_B * 1.6:.0f}" fill="url(#mapglow)"/>')
    c00, c10, c11, c01 = proj(0, 0), proj(1, 0), proj(1, 1), proj(0, 1)
    tk = MAP_T
    b.append(f'<path d="M{c01[0]:.0f} {c01[1]:.0f}L{c11[0]:.0f} {c11[1]:.0f}L{c11[0]:.0f} {c11[1] + tk:.0f}L{c01[0]:.0f} {c01[1] + tk:.0f}Z" fill="{PAPER["side_l"]}"/>')
    b.append(f'<path d="M{c11[0]:.0f} {c11[1]:.0f}L{c10[0]:.0f} {c10[1]:.0f}L{c10[0]:.0f} {c10[1] + tk:.0f}L{c11[0]:.0f} {c11[1] + tk:.0f}Z" fill="{PAPER["side_r"]}"/>')
    b.append(f'<path d="M{c00[0]:.0f} {c00[1]:.0f}L{c10[0]:.0f} {c10[1]:.0f}L{c11[0]:.0f} {c11[1]:.0f}L{c01[0]:.0f} {c01[1]:.0f}Z" fill="{PAPER["sheet"]}"/>')
    gl = ''
    for k in range(1, 10):
        a0, a1 = proj(k / 10, 0), proj(k / 10, 1)
        b0, b1 = proj(0, k / 10), proj(1, k / 10)
        gl += f'M{a0[0]:.0f} {a0[1]:.0f}L{a1[0]:.0f} {a1[1]:.0f}M{b0[0]:.0f} {b0[1]:.0f}L{b1[0]:.0f} {b1[1]:.0f}'
    b.append(f'<path d="{gl}" stroke="#D9CDB6" stroke-width=".8" fill="none"/>')
    unit = f'matrix({MAP_A / 1000:.4f} {MAP_B / 1000:.4f} {-MAP_A / 1000:.4f} {MAP_B / 1000:.4f} {MAP_OX} {MAP_OY})'
    ci = total / LAYERS
    b.append(f'<g transform="{unit}">' + T('THE CLIMB LOG  ·  SHEET GK-001  ·  1 M = 1 PUBLIC CONTRIBUTION', 'p600', 19, 40, 972, ls=3, fill='#9A8A70') + '</g>')
    b.append(f'<g transform="{unit} translate(972 960) rotate(-90)">' + T(f'CONTOUR INTERVAL {ci:.0f} M  ·  OTTAWA', 'p600', 19, 0, 0, ls=3, fill='#9A8A70') + '</g>')
    b.append('</g>')
    css.append('.sheetin{animation:sheetin 1s .25s cubic-bezier(.2,.8,.2,1) both}@keyframes sheetin{from{opacity:0;transform:translateY(30px)}}')
    # terrain: one paper layer per contour, each with its riser; they rise off the sheet in order
    for k in range(1, LAYERS):
        lv = k / LAYERS
        loops = TR.contours(grid, lv)
        if not loops:
            continue
        f = k / (LAYERS - 1)
        idx = k % 5 == 0
        z0, z1 = (k - 1) / LAYERS, lv
        b.append(f'<g class="ly{k}">'
                 f'<path d="{_loops_d(loops, z0)}" fill="{_mix(PAPER["rise0"], PAPER["rise1"], f)}" fill-rule="evenodd"/>'
                 f'<path d="{_loops_d(loops, z1)}" fill="{_mix(PAPER["top0"], PAPER["top1"], f)}" fill-rule="evenodd" '
                 f'stroke="{PAPER["index"] if idx else PAPER["line"]}" stroke-width="{1.2 if idx else .7}" stroke-opacity="{.85 if idx else .55}" stroke-linejoin="round"/></g>')
        css.append(f'.ly{k}{{animation:ly{k} .7s {.75 + k * .055:.2f}s cubic-bezier(.2,.8,.2,1) both}}@keyframes ly{k}{{from{{opacity:0;transform:translateY({z1 * MAP_KZ:.0f}px)}}}}')
    # the route: Catmull-Rom across the plane, stepped onto the layer it stands on
    plane = _catmull_plane(ROUTE)
    hs = [TR.height_at(grid, x, y) for x, y in plane]
    scr = [proj(x, y, math.floor(h * LAYERS) / LAYERS) for (x, y), h in zip(plane, hs)]
    rlen = [0.0]
    for p0, p1 in zip(scr, scr[1:]):
        rlen.append(rlen[-1] + math.dist(p0, p1))
    rd = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in scr)
    R0, RDUR, REASE = 2.15, 2.4, (.45, .05, .35, 1)
    b.append(f'<mask id="rmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><path class="rdraw" d="{rd}" pathLength="1" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></mask>')
    b.append(f'<g mask="url(#rmask)"><path d="{rd}" fill="none" stroke="{PAPER["card"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path class="ants" d="{rd}" fill="none" stroke="{PAPER["route"]}" stroke-width="2.6" stroke-dasharray="7 5" stroke-linecap="round" stroke-linejoin="round"/></g>')
    css.append(f'.rdraw{{stroke-dasharray:1;animation:rdraw {RDUR}s {R0}s cubic-bezier({",".join(map(str, REASE))}) both}}@keyframes rdraw{{from{{stroke-dashoffset:1}}}}'
               f'.ants{{animation:ants 1.3s {R0 + RDUR:.2f}s linear infinite}}@keyframes ants{{to{{stroke-dashoffset:-24}}}}')
    # the trailhead, printed flat on the paper where the route (and the window) begins
    hx, hy = plane[0]
    b.append(f'<g class="trail"><circle cx="{scr[0][0]:.1f}" cy="{scr[0][1]:.1f}" r="4" fill="{PAPER["card"]}" stroke="{PAPER["route"]}" stroke-width="2"/>'
             f'<g transform="{unit}">' + T(f'TRAILHEAD  ·  {MONTHS[week0.month - 1]} {week0.year}', 'p600', 17, hx * 1000 + 26, hy * 1000 - 40, ls=2.4, fill='#8A7A60') + '</g></g>')
    css.append(f'.trail{{animation:fadein .5s {R0 - .1:.2f}s both}}')

    def at_height(target):
        for i, h in enumerate(hs):
            if h >= target:
                return i
        return len(hs) - 1

    def t_reach(i):
        return R0 + RDUR * css_ease_time(*REASE, rlen[i] / rlen[-1])

    marks = [('BASE CAMP', dmy(base_day), at_height(cum_through(cal, base_day) / total), 'left')]
    for k, cp in enumerate(camps_from(P)):
        if not (week0 <= cp['start'] <= last):
            continue
        names = [n.upper() for n in cp['names']]
        what = names[0] if len(names) == 1 else ' · '.join(names) if len(names) == 2 else f'{len(names)} RELEASES'
        side = 'right' if k % 2 == 0 else 'left'
        marks.append((f'CAMP {ROMAN[k] if k < len(ROMAN) else k + 1}', f'{what} · {dmy(cp["start"], False)}', at_height(cum_through(cal, cp['end']) / total), side))
    placed = {'left': [], 'right': []}
    for k, (l1, l2, i, side) in enumerate(marks):
        x, y = scr[i]
        cls = f'cm{k}'
        w1 = max(M(l1, 'p600', 13, 1.2), M(l2, 'p500', 12, .8)) + 24
        lx = x - 40 - w1 if side == 'left' else x + 40
        ly = y - 58
        for py in sorted(placed[side]):
            if abs(ly - py) < 52:
                ly = py + 52
        placed[side].append(ly)
        ax = lx + w1 if side == 'left' else lx
        b.append(f'<g class="{cls}">'
                 f'<path d="M{x:.1f} {y - 24:.1f}L{ax:.1f} {ly + 23:.1f}" stroke="{PAPER["ink"]}" stroke-width=".8" stroke-opacity=".5" fill="none"/>'
                 f'<path d="M{x:.1f} {y:.1f}V{y - 26:.1f}" stroke="{PAPER["ink"]}" stroke-width="1.6"/><path d="M{x:.1f} {y - 26:.1f}l14 5-14 5z" fill="{PAPER["route"]}"/>'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{PAPER["ink"]}"/>'
                 f'<g class="lbl"><rect x="{lx:.1f}" y="{ly:.1f}" width="{w1:.1f}" height="46" rx="6" fill="{PAPER["card"]}" stroke="{PAPER["edge"]}"/>'
                 + T(l1, 'p600', 13, lx + 12, ly + 19, ls=1.2, fill=PAPER['ink'])
                 + T(l2, 'p500', 12, lx + 12, ly + 36, ls=.8, fill=PAPER['dim']) + '</g></g>')
        css.append(f'.{cls}{{animation:pop .5s {t_reach(i):.2f}s cubic-bezier(.2,1.4,.4,1) both}}')
    css.append('@keyframes pop{from{opacity:0;transform:translateY(8px)}}@keyframes fadein{from{opacity:0}}')
    # summit: today's total, then the next leg leaves the map
    sx, sy = scr[-1]
    t_sum = R0 + RDUR
    sl1, sl2 = f'SUMMIT · {total:,} M', f'YOU ARE HERE · {dmy(last)}'
    sw = max(M(sl1, 'p600', 13, 1.2), M(sl2, 'p500', 12, .8)) + 24
    b.append(f'<g class="summit"><path d="M{sx:.1f} {sy - 2:.1f}V{sy - 34:.1f}" stroke="{PAPER["ink"]}" stroke-width="1.8"/><path d="M{sx:.1f} {sy - 34:.1f}l18 6-18 6z" fill="{PAPER["route"]}"/>'
             f'<g class="lbl"><rect x="{sx - sw - 30:.1f}" y="{sy - 92:.1f}" width="{sw:.1f}" height="46" rx="6" fill="{PAPER["ink"]}"/>'
             + T(sl1, 'p600', 13, sx - sw - 18, sy - 73, ls=1.2, fill=PAPER['card'])
             + T(sl2, 'p500', 12, sx - sw - 18, sy - 56, ls=.8, fill='#BFB4A2') + '</g></g>')
    css.append(f'.summit{{animation:pop .5s {t_sum - .1:.2f}s cubic-bezier(.2,1.4,.4,1) both}}')
    tip = (1070, 150)  # far enough from the edges that its glow fades out inside the image (no visible box)
    traj = f'M{sx:.1f} {sy - 30:.1f}C{sx + 14:.1f} {sy - 150:.1f} {tip[0] - 210:.1f} {tip[1] + 60:.1f} {tip[0]} {tip[1]}'
    b.append(f'<circle cx="{tip[0]}" cy="{tip[1]}" r="120" fill="url(#tipglow)" class="tipglow"/>')
    b.append(f'<circle class="burst0" cx="{sx:.1f}" cy="{sy - 30:.1f}" r="14" fill="none" stroke="{t_["accent"]}" stroke-width="2"/>')
    b.append(f'<path d="{traj}" fill="none" stroke="{C["flame"]}" stroke-width="9" opacity=".33" filter="url(#glow)" class="draw" pathLength="1"/>')
    b.append(f'<path d="{traj}" fill="none" stroke="{C["hot"] if th == "dark" else C["flame"]}" stroke-width="2.6" stroke-linecap="round" class="draw" pathLength="1"/>')
    T0, TD = t_sum + .2, 1.3
    css.append(f'.draw{{stroke-dasharray:1;animation:draw {TD}s {T0:.2f}s cubic-bezier(.55,0,.3,1) both}}@keyframes draw{{from{{stroke-dashoffset:1}}}}'
               f'.tipglow{{animation:fadein .8s {T0 + TD - .2:.2f}s both}}'
               f'.burst0{{opacity:0;transform-box:fill-box;transform-origin:center;animation:burst 1s {T0 - .1:.2f}s ease-out}}'
               '@keyframes burst{0%{opacity:1;transform:scale(.3)}100%{opacity:0;transform:scale(4)}}')
    b.append(f'<circle class="burst1" cx="{tip[0]}" cy="{tip[1]}" r="16" fill="none" stroke="{t_["accent"]}" stroke-width="2"/>')
    b.append(f'<g class="tip"><circle cx="{tip[0]}" cy="{tip[1]}" r="14" fill="{C["hot"]}" opacity=".3" filter="url(#glow)"/><circle cx="{tip[0]}" cy="{tip[1]}" r="4.2" fill="{t_["tipcore"]}"/></g>')
    b.append('<g class="nextl">' + T('NEXT LEG', 'p600', 13, tip[0] - 22, tip[1] + 5, 'end', ls=1.6, fill=t_['accent']) + '</g>')
    css.append(f'.burst1{{opacity:0;transform-box:fill-box;transform-origin:center;animation:burst 1.1s {T0 + TD - .1:.2f}s ease-out}}'
               f'.tip{{animation:fadein .2s {T0 + TD - .15:.2f}s both,pulse 2.4s {T0 + TD + .4:.2f}s ease-in-out infinite}}@keyframes pulse{{50%{{opacity:.5}}}}'
               f'.nextl{{animation:fadein .6s {T0 + TD:.2f}s both}}')
    b.append('</g></g>')  # float, and the phone wrapper
    css.append(f'.float{{animation:float 7s {T0 + TD + 1:.1f}s ease-in-out infinite alternate}}@keyframes float{{to{{transform:translateY(-6px)}}}}')

    if n:
        css.append('.lbl,.nextl{display:none}')  # map labels would be about 5 px on a phone; the numbers row says it
        # ---------------- identity, stacked for a phone
        b.append('<g class="kick">' + T(f'CLIMB LOG + FLIGHT LOG  ·  {I["place"].upper()}', 'p500', 20, 40, 64, ls=1.6, fill=t_['dim']) + '</g>')
        css.append('.kick{animation:fadein .8s .1s both}')
        words = I['name'].upper().split()
        size = min(fit(w_, 'ac900', 640, .02) for w_ in words)
        y = 80
        for k, word in enumerate(words):
            y += capH('ac900', size) + (14 if k else 10)
            b.append(f'<clipPath id="nc{k}"><rect x="0" y="{y - capH("ac900", size) - 8:.0f}" width="{W_}" height="{capH("ac900", size) + 22:.0f}"/></clipPath>'
                     f'<g clip-path="url(#nc{k})"><g class="nw{k}">' + T(word, 'ac900', size, 36, y, ls=size * .02, fill=t_['ink']) + '</g></g>')
            css.append(f'.nw{k}{{animation:rise .9s {.15 + k * .14:.2f}s cubic-bezier(.2,.8,.2,1) both}}')
        css.append('@keyframes rise{from{transform:translateY(110%)}}')
        y += 70
        b.append('<g class="id0">' + T(I['motto'].upper(), 'ac800', 46, 40, y, ls=4, fill=C['flame']) + '</g>')
        for k, ln in enumerate(wrap(I['line'], 'a500', 28, 640)):
            b.append(f'<g class="id1">' + T(ln, 'a500', 28, 40, y + 50 + k * 36, fill=t_['soft']) + '</g>')
        css.append('.id0{animation:fadeup .7s .55s cubic-bezier(.2,.8,.2,1) both}.id1{animation:fadeup .7s .7s cubic-bezier(.2,.8,.2,1) both}'
                   '@keyframes fadeup{from{opacity:0;transform:translateY(10px)}}')
        # ---------------- telemetry: three numbers in a row under the map
        rows = [('SUMMIT', f'{total:,} M'), ('PEAK WEEK', f'+{weeks[peak_i]:,}'), ('BASE CAMP', dmy(base_day, False))]
        ty0 = H - 150
        for k, (lab, val) in enumerate(rows):
            x0 = 40 + k * 228
            b.append(f'<g class="tl{k}">' + T(lab, 'p500', 18, x0, ty0, ls=1.6, fill=t_['dim']) + '</g>')
            css.append(f'.tl{k}{{animation:fadein .6s {1.5 + k * .15:.2f}s both}}')
            if k < 2:
                svg, oc = odometer(val, 'ac800', 44, x0 + M(val, 'ac800', 44), ty0 + 50, t_['ink'], 1.6 + k * .2, k)
                b.append(svg)
                css.append(oc)
            else:
                b.append(f'<g class="tl{k}">' + T(val, 'ac800', 44, x0, ty0 + 50, ls=.6, fill=t_['ink']) + '</g>')
        b.append(f'<circle class="blink" cx="46" cy="{H - 34}" r="6" fill="{t_["green"]}"/>')
        b.append(T(f'LIVE  ·  REBUILT NIGHTLY  ·  {dmy(last)}', 'p500', 17, 62, H - 28, ls=1.4, fill=t_['dim']))
        css.append('.blink{animation:blink 1.8s steps(1) infinite}@keyframes blink{50%{opacity:.2}}')
    else:
        # ---------------- identity
        b.append('<g class="kick">' + T(f'CLIMB LOG + FLIGHT LOG  ·  {I["place"].upper()}  ·  {I["coords"]}', 'p500', 14, 56, 86, ls=1.6, fill=t_['dim']) + '</g>')
        css.append('.kick{animation:fadein .8s .1s both}')
        name_size = fit(I['name'].upper(), 'ac900', 690, .02)
        name_base = 96 + capH('ac900', name_size) + 18
        b.append(f'<clipPath id="namec"><rect x="0" y="96" width="{W}" height="{name_base - 96 + 14:.0f}"/></clipPath><g clip-path="url(#namec)">')
        x = 52
        for k, word in enumerate(I['name'].upper().split()):
            b.append(f'<g class="nw{k}">' + T(word, 'ac900', name_size, x, name_base, ls=name_size * .02, fill=t_['ink']) + '</g>')
            css.append(f'.nw{k}{{animation:rise .9s {.15 + k * .14:.2f}s cubic-bezier(.2,.8,.2,1) both}}')
            x += M(word + ' ', 'ac900', name_size, name_size * .02)
        b.append('</g>')
        css.append('@keyframes rise{from{transform:translateY(110%)}}')
        for k, (txt, font, size, yy, col, ls) in enumerate((
                (I['motto'].upper(), 'ac800', 34, name_base + 54, C['flame'], 3),
                (I['line'], 'a500', 19, name_base + 92, t_['soft'], 0),
                (I['school'], 'a500', 19, name_base + 120, t_['dim'], 0))):
            b.append(f'<g class="id{k}">' + T(txt, font, size, 56, yy, ls=ls, fill=col) + '</g>')
            css.append(f'.id{k}{{animation:fadeup .7s {.55 + k * .12:.2f}s cubic-bezier(.2,.8,.2,1) both}}')
        css.append('@keyframes fadeup{from{opacity:0;transform:translateY(10px)}}')
        # ---------------- telemetry (left): odometers that land on the real numbers
        tx0, ty0 = 56, name_base + 182
        rows = [('SUMMIT ELEVATION', f'{total:,} M'), ('STEEPEST WEEK', f'+{weeks[peak_i]:,} M'), ('BASE CAMP', dmy(base_day))]
        for k, (lab, val) in enumerate(rows):
            yy = ty0 + k * 62
            b.append(f'<g class="tl{k}">' + T(lab, 'p500', 13, tx0, yy, ls=1.6, fill=t_['dim']) + '</g>')
            css.append(f'.tl{k}{{animation:fadein .6s {1.5 + k * .15:.2f}s both}}')
            if k < 2:
                svg, oc = odometer(val, 'ac800', 32, tx0 + M(val, 'ac800', 32), yy + 34, t_['ink'], 1.6 + k * .2, k)
                b.append(svg)
                css.append(oc)
            else:
                b.append(f'<g class="tl{k}">' + T(val, 'ac800', 32, tx0, yy + 34, ls=.6, fill=t_['ink']) + '</g>')
        b.append('<g class="tl3">' + T('1 M = 1 PUBLIC CONTRIBUTION · 12 MONTHS', 'p500', 11, tx0, ty0 + 3 * 62 - 6, ls=1.2, fill=t_['faint']) + '</g>')
        css.append('.tl3{animation:fadein .6s 2.1s both}')
        stamp = f'TELEMETRY LIVE  ·  REBUILT NIGHTLY  ·  LAST RUN {dmy(last)}'
        b.append(f'<circle class="blink" cx="62" cy="{H - 34}" r="4" fill="{t_["green"]}"/>')
        b.append(T(stamp, 'p500', 12, 76, H - 30, ls=1.4, fill=t_['dim']))
        css.append('.blink{animation:blink 1.8s steps(1) infinite}@keyframes blink{50%{opacity:.2}}')
    css.append('.starsin{animation:fadein 1.4s both}.tw{animation:tw 3.6s ease-in-out infinite}@keyframes tw{50%{opacity:.08}}')
    label = (f'{I["name"]}. {I["motto"]} {I["line"]} A layered paper map floats on the page: the mountain is his real public GitHub '
             f'contributions, 1 metre each, so the summit stands at {total:,} m on {dmy(last)}. The route climbs from base camp '
             f'({dmy(base_day)}) through a camp at each release, and from the summit a trajectory leaves the map.')
    css.append(REDUCE)
    return doc(W_, H, label, ''.join(b), ''.join(css))


# =============================================================== links
def link_pill(label, primary, th):
    t_ = TH[th]
    h = 52
    tw = M(label, 'p600', 17, .8)
    w = tw + 74
    if primary:
        fill, stroke, sop, ink, ar = ('#1A0E08', C['flame'], .75, '#FFE2D2', C['flame']) if th == 'dark' else ('#FFF3EC', C['flame'], .8, '#B23A0E', '#D63600')
    else:
        fill, stroke, sop, ink, ar = ('#0F1623', '#FFFFFF', .2, t_['ink'], t_['soft']) if th == 'dark' else ('#FFFFFF', '#14151A', .2, t_['ink'], t_['soft'])
    body = (page(w, h, th) +
            f'<rect x=".75" y=".75" width="{w - 1.5:.1f}" height="{h - 1.5}" rx="{h / 2 - 1}" fill="{fill}" stroke="{stroke}" stroke-opacity="{sop}" stroke-width="1.5"/>'
            + T(label, 'p600', 17, 26, h / 2 + capH('p600', 17) / 2, ls=.8, fill=ink))
    ax = 26 + tw + 16
    body += f'<path d="M{ax:.1f} {h / 2 + 6:.1f}l11-11M{ax + 2:.1f} {h / 2 - 5:.1f}h9v9" fill="none" stroke="{ar}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    return doc(round(w), h, f'{label} (link)', body)


# =============================================================== section headers
def section_header(idx, title, caption, th):
    t_ = TH[th]
    H = 112
    b = [page(W, H, th),
         T(idx, 'p600', 15, 0, 62, ls=1.4, fill=C['flame']),
         T(title.upper(), 'ac900', 46, 44, 66, ls=1.2, fill=t_['ink']),
         T(caption.upper(), 'p500', 13, W, 62, 'end', ls=1.6, fill=t_['dim']),
         f'<path d="M0 92H{W}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .04}" stroke-width="1.2"/>']
    ticks = ''.join(f'<path d="M{x} 92v{6 if x % 120 == 0 else 3}"/>' for x in range(0, W + 1, 24))
    b.append(f'<g stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .04}" stroke-width="1.2">{ticks}</g>')
    accent = 44 + M(title.upper(), 'ac900', 46, 1.2)
    b.append(f'<rect class="acc" x="0" y="90.5" width="{accent:.0f}" height="3" rx="1.5" fill="{C["flame"]}"/>')
    b.append(f'<rect class="glint" x="{accent - 60:.0f}" y="90.5" width="60" height="3" rx="1.5" fill="#FFD2B8"/>')
    css = (f'.acc{{transform-box:fill-box;transform-origin:0 50%;animation:acc 1s .3s cubic-bezier(.2,.8,.2,1) both}}@keyframes acc{{from{{transform:scaleX(0)}}}}'
           f'.glint{{opacity:0;animation:glint 2.2s 1.2s cubic-bezier(.6,0,.2,1)}}'
           f'@keyframes glint{{0%{{opacity:.9;transform:translateX(0)}}100%{{opacity:0;transform:translateX({W - accent:.0f}px)}}}}' + REDUCE)
    return doc(W, H, f'{idx} {title}. {caption}.', ''.join(b), css)


# =============================================================== mission patches
def ring_text(txt, font, size, cx, cy, r, color, bottom=False, ls=0.0):
    upm = G.metrics(font)[0]
    s = size / upm
    advs = [(ch, G.glyph_path(ch, font)[0] * s, G.glyph_path(ch, font)[1]) for ch in txt]
    total = sum(a for _, a, _ in advs) + ls * (len(advs) - 1)
    out, pos = [], -total / 2
    for ch, a, d in advs:
        mid = pos + a / 2
        ang = (-90 + math.degrees(mid / r)) if not bottom else (90 - math.degrees(mid / r))
        rot = ang + 90 if not bottom else ang - 90
        px, py = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
        if d:
            out.append(f'<use href="#{G._ref(font, ch, d)}" transform="translate({px:.2f} {py:.2f}) rotate({rot:.2f}) translate({-a / 2:.2f} 0) scale({s:.5f})"/>')
        pos += a + ls
    return f'<g fill="{color}">{"".join(out)}</g>'


def _blob(cx, cy, r, k=36, wob=.07, seed=2.3):
    pts = []
    for i in range(k):
        a = 2 * math.pi * i / k
        rr = r * (1 - wob + wob * math.sin(i * seed) * math.cos(i * .9))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pts.append(pts[0])
    d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
    for i in range(1, len(pts)):
        p0, p1 = pts[i - 1], pts[i]
        d += f' Q{p0[0]:.1f} {p0[1]:.1f} {(p0[0] + p1[0]) / 2:.1f} {(p0[1] + p1[1]) / 2:.1f}'
    return d + 'Z'


def emblem(kind, cx, cy, ir, acc, uid):
    o, css = [], []
    if kind == 'seal':
        o.append(f'<path d="{_blob(cx, cy + 3, ir * .64)}" fill="#2E6B3A"/>')
        o.append(f'<circle cx="{cx}" cy="{cy + 3}" r="{ir * .44:.1f}" fill="#24582F" stroke="{acc}" stroke-width="1.2"/>')
        rays = ''.join(f'<path d="M{cx:.1f} {cy + 3:.1f}L{cx + ir * .38 * math.cos(2 * math.pi * k / 12):.1f} {cy + 3 + ir * .38 * math.sin(2 * math.pi * k / 12):.1f}"/>' for k in range(12))
        o.append(f'<g class="rose{uid}" style="transform-origin:{cx}px {cy + 3}px" stroke="{acc}" stroke-width="1.1" opacity=".85">{rays}</g>')
        o.append(f'<circle cx="{cx}" cy="{cy + 3}" r="5" fill="{acc}"/>')
        o.append(f'<defs><linearGradient id="sh{uid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                 f'<clipPath id="sc{uid}"><path d="{_blob(cx, cy + 3, ir * .64)}"/></clipPath></defs>')
        o.append(f'<g clip-path="url(#sc{uid})"><rect class="sheen{uid}" x="{cx - ir:.1f}" y="{cy - ir:.1f}" width="{ir * .5:.1f}" height="{ir * 2:.1f}" fill="url(#sh{uid})" transform="skewX(-18)"/></g>')
        css.append(f'.rose{uid}{{animation:spin 40s linear infinite}}@keyframes spin{{to{{transform:rotate(360deg)}}}}'
                   f'.sheen{uid}{{animation:sheen{uid} 5.5s 1.2s ease-in-out infinite}}@keyframes sheen{uid}{{0%{{transform:skewX(-18deg) translateX(-60px)}}45%,100%{{transform:skewX(-18deg) translateX({ir * 2.4:.0f}px)}}}}')
    elif kind == 'clock':
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{ir * .66:.1f}" fill="#F4F4F0"/>')
        for a in range(0, 360, 30):
            ra = math.radians(a)
            o.append(f'<path d="M{cx + ir * .53 * math.cos(ra):.1f} {cy + ir * .53 * math.sin(ra):.1f}L{cx + ir * .62 * math.cos(ra):.1f} {cy + ir * .62 * math.sin(ra):.1f}" stroke="#141516" stroke-width="{2.6 if a % 90 == 0 else 1.8}"/>')
        o.append(f'<path d="M{cx} {cy}L{cx - ir * .3:.1f} {cy - ir * .2:.1f}" stroke="#141516" stroke-width="3.4" stroke-linecap="round"/>')
        o.append(f'<path d="M{cx} {cy}L{cx + ir * .36:.1f} {cy - ir * .3:.1f}" stroke="#141516" stroke-width="2.6" stroke-linecap="round"/>')
        o.append(f'<g class="sec{uid}" style="transform-origin:{cx}px {cy}px"><path d="M{cx} {cy + 9}V{cy - ir * .55:.1f}" stroke="#E2231A" stroke-width="1.4"/><circle cx="{cx}" cy="{cy - ir * .46:.1f}" r="4" fill="#E2231A"/></g>')
        o.append(f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="#E2231A"/>')
        css.append(f'.sec{uid}{{animation:sec{uid} 60s linear infinite}}@keyframes sec{uid}{{to{{transform:rotate(360deg)}}}}')
    elif kind == 'flame':
        fl = (f'M{cx} {cy - ir * .56:.1f} C{cx + ir * .12:.1f} {cy - ir * .25:.1f} {cx + ir * .42:.1f} {cy - ir * .12:.1f} {cx + ir * .34:.1f} {cy + ir * .2:.1f}'
              f' C{cx + ir * .28:.1f} {cy + ir * .42:.1f} {cx - ir * .28:.1f} {cy + ir * .42:.1f} {cx - ir * .34:.1f} {cy + ir * .2:.1f}'
              f' C{cx - ir * .42:.1f} {cy - ir * .02:.1f} {cx - ir * .18:.1f} {cy - ir * .2:.1f} {cx} {cy - ir * .56:.1f}Z')
        o.append(f'<defs><linearGradient id="fl{uid}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#FFD27A"/><stop offset=".6" stop-color="{acc}"/><stop offset="1" stop-color="#E24A12"/></linearGradient></defs>')
        o.append(f'<ellipse class="halo{uid}" cx="{cx}" cy="{cy + ir * .2:.1f}" rx="{ir * .55:.1f}" ry="{ir * .32:.1f}" fill="{acc}" opacity=".2" filter="url(#glow)"/>')
        for k in (1, -1):
            o.append(f'<rect x="{cx - ir * .42:.1f}" y="{cy + ir * .38:.1f}" width="{ir * .84:.1f}" height="8" rx="4" fill="#5A3A22" transform="rotate({12 * k} {cx} {cy + ir * .42:.1f})"/>')
        o.append(f'<path class="flk{uid}" style="transform-origin:{cx}px {cy + ir * .4:.1f}px" d="{fl}" fill="url(#fl{uid})"/>')
        rnd = random.Random(3)
        for k in range(6):
            o.append(f'<circle class="sp{uid}" style="animation-delay:{k * .45:.2f}s" cx="{cx + rnd.uniform(-ir * .28, ir * .28):.1f}" cy="{cy - ir * .42:.1f}" r="1.7" fill="#FFD27A"/>')
        css.append(f'.flk{uid}{{animation:flk{uid} 1.2s ease-in-out infinite alternate}}@keyframes flk{uid}{{to{{transform:scale(.93,1.07) skewX(2deg)}}}}'
                   f'.halo{uid}{{animation:halo{uid} 2.4s ease-in-out infinite}}@keyframes halo{uid}{{50%{{opacity:.32}}}}'
                   f'.sp{uid}{{opacity:0;animation:sp{uid} 2.7s ease-out infinite}}@keyframes sp{uid}{{0%{{opacity:0;transform:translateY(0)}}15%{{opacity:1}}100%{{opacity:0;transform:translate(6px,-44px)}}}}')
    else:  # 'orbit', the default for new products until they get their own emblem
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{ir * .3:.1f}" fill="{acc}" opacity=".85"/>')
        o.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{ir * .62:.1f}" ry="{ir * .22:.1f}" fill="none" stroke="{acc}" stroke-width="1.4" transform="rotate(-20 {cx} {cy})"/>')
    return ''.join(o), ''.join(css)


def patch(cx, cy, r, m, uid, th):
    acc = m['color']
    hexes = {'seal': ('#0F2A18', '#1D4A2A'), 'clock': ('#2A0B0A', '#4A1412'), 'flame': ('#1A1209', '#3A220E')}
    bg0, bg1 = hexes.get(m['patch'], ('#0B1424', '#16233D'))
    lab = STATUS[m['status']][0]
    o = [f'<defs><radialGradient id="pg{uid}" cx=".5" cy=".38" r=".7"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg0}"/></radialGradient></defs>',
         f'<circle cx="{cx}" cy="{cy + 6}" r="{r + 4}" fill="#000" opacity="{.5 if th == "dark" else .22}" filter="url(#glow)"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0C1424"/>',
         f'<circle class="stitch{uid}" style="transform-origin:{cx}px {cy}px" cx="{cx}" cy="{cy}" r="{r - 3}" fill="none" stroke="#C9D2E3" stroke-width="3" stroke-dasharray="2.2 2.6" opacity=".9"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r - 32}" fill="url(#pg{uid})"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r - 32}" fill="none" stroke="{acc}" stroke-width="1.6" opacity=".9"/>',
         ring_text(m['name'].upper(), 'p600', 17, cx, cy, r - 24, '#EEF2F8', ls=3.2),
         ring_text(f'{lab} · {iso(m["launched"]).year}', 'p500', 14, cx, cy, r - 25, '#9AA6BC', bottom=True, ls=2.6)]
    em, css = emblem(m['patch'], cx, cy, r - 32, acc, uid)
    o.append(em)
    css += f'.stitch{uid}{{animation:spin{uid} 90s linear infinite}}@keyframes spin{uid}{{to{{transform:rotate(360deg)}}}}'
    return ''.join(o), css


def mission_row(m, idx, camp, th):
    """A product, frameless: patch on the page, text beside it, a hairline below."""
    t_ = TH[th]
    tx, tw_ = 330, 790
    about = wrap(m['about'], 'a500', 18, tw_)
    H = 206 + 26 * len(about) + 72
    css = []
    b = [f'<defs>{GLOW}</defs>', page(W, H, th),
         topo_lines(W, H, 40 + idx, t_['topo'], t_['topo_op'], levels=9, fade=(240, 520)),
         f'<circle cx="170" cy="{H / 2:.0f}" r="132" fill="{m["color"]}" opacity="{t_["glow_op"]}" filter="url(#glow2)"/>']
    p, pc = patch(170, H / 2, 112, m, idx, th)
    b.append(p)
    css.append(pc)
    kick = f'MISSION {idx:02d}  ·  ' + (f'CAMP {camp}  ·  ' if camp else '') + f'LAUNCHED {dmy(m["launched"])}'
    b.append(T(kick, 'p500', 14, tx, 62, ls=1.6, fill=t_['dim']))
    host = m['url'].split('//', 1)[-1].rstrip('/')
    b.append(T(host, 'p500', 14, W - 44, 62, 'end', ls=.6, fill=t_['dim']))
    b.append(arrow(W - 16, 57, t_['soft']))
    b.append(T(m['name'].upper(), 'ac900', 56, tx - 2, 126, ls=.8, fill=t_['ink']))
    lab, col = status(m['status'], th)
    cx_ = tx + M(m['name'].upper(), 'ac900', 56, .8) + 22
    c1, w1 = chip(cx_, 98, lab, col)
    b.append(c1)
    b.append(T(m['note'].upper(), 'p500', 13, cx_ + w1 + 12, 117, ls=1.2, fill=t_['dim']))
    b.append(T(m['tagline'], 'a600', 25, tx, 172, fill=t_['ink']))
    for k, ln in enumerate(about):
        b.append(T(ln, 'a500', 18, tx, 206 + k * 26, fill=t_['dim']))
    cy = 206 + 26 * len(about) + 10
    cmd_w = M(m['command'], 'p500', 15) + 32
    b.append(f'<rect x="{tx}" y="{cy:.0f}" width="{cmd_w:.0f}" height="38" rx="9" fill="{t_["chip"]}" fill-opacity="{t_["chip_op"]}" stroke="{t_["chip"]}" stroke-opacity="{t_["chip_line"]}"/>')
    b.append(T(m['command'], 'p500', 15, tx + 16, cy + 24, fill=t_['cmd']))
    b.append(hairline(H - .5, th))
    css.append(REDUCE)
    label = f'Mission {idx:02d}: {m["name"]}. {m["tagline"]} {m["about"]} Status: {lab.lower()}, {m["note"]}. Launched {dmy(m["launched"])}. {m["command"]}. Opens {host}.'
    return doc(W, H, label, ''.join(b), ''.join(css))


# =============================================================== in orbit
def orbit_row(o, idx, L, camp, th):
    t_ = TH[th]
    lab, col = status(o['status'], th)
    about = wrap(o['about'], 'a500', 17, 520)
    live_line = ''
    if o.get('live') == 'dodge' and 'dodge' in L:
        D = L['dodge']
        live_line = f'{D["u5"]:,} PREDICTED PASSES UNDER 5 KM  ·  {D["u1"]:,} UNDER 1 KM  ·  RUN OF {dmy(D["day"], False)}'
    lines = len(about) + (1 if live_line else 0)
    H = max(128, 62 + 25 * lines + 22)
    css = []
    b = [page(W, H, th)]
    cx, cy = 52, H / 2
    b.append(f'<defs><radialGradient id="pl{idx}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="{t_["planet0"]}"/><stop offset="1" stop-color="{t_["planet1"]}"/></radialGradient></defs>')
    orbit_d = f'M{cx - 34} {cy} A34 11 0 1 0 {cx + 34} {cy} A34 11 0 1 0 {cx - 34} {cy}'
    b.append(f'<g transform="rotate(-18 {cx} {cy:.1f})"><path d="{orbit_d}" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .1}" stroke-dasharray="2 3"/></g>')
    b.append(f'<circle cx="{cx}" cy="{cy:.1f}" r="15" fill="url(#pl{idx})" stroke="{t_["rim"]}" stroke-opacity=".45"/>')
    if o['status'] in ('live', 'beta'):
        dur = (6.5, 8.5, 10.5, 12.5)[idx % 4]
        b.append(f'<g transform="rotate(-18 {cx} {cy:.1f})"><circle class="rm-hide" r="3.6" fill="{col}"><animateMotion dur="{dur}s" repeatCount="indefinite" path="{orbit_d}"/></circle>'
                 f'<circle class="rm-show" cx="{cx + 34}" cy="{cy:.1f}" r="3.6" fill="{col}"/></g>')
    elif o['status'] == 'docked':
        b.append(f'<circle cx="{cx + 17}" cy="{cy - 10:.1f}" r="5" fill="{col}" stroke="{t_["page"]}" stroke-width="2"/>')
    else:
        b.append(f'<g transform="rotate(-18 {cx} {cy:.1f})"><circle cx="{cx - 34}" cy="{cy:.1f}" r="3.6" fill="none" stroke="{col}" stroke-width="1.6"/></g>')
    kick = {'live': f'IN ORBIT SINCE {dmy(o["since"])}', 'beta': f'IN ORBIT SINCE {dmy(o["since"])}',
            'parked': f'PARKED  ·  SINCE {dmy(o["since"])}', 'docked': f'DOCKED WITH {o.get("docked_with", "").upper()}'}[o['status']]
    if camp:
        kick = f'CAMP {camp}  ·  ' + kick
    top = H / 2 - 12
    b.append(T(kick, 'p500', 12, 116, top - 6, ls=1.4, fill=t_['dim']))
    nsize = min(32, fit(o['name'].upper(), 'ac800', 320, .02))
    b.append(T(o['name'].upper(), 'ac800', nsize, 115, top + 30, ls=nsize * .02, fill=t_['ink']))
    ty = H / 2 - (25 * lines) / 2 + 17
    for k, ln in enumerate(about):
        b.append(T(ln, 'a500', 17, 470, ty + k * 25, fill=t_['soft'] if k == 0 else t_['dim']))
    if live_line:
        yy = ty + len(about) * 25
        hot = C['hot'] if th == 'dark' else '#C2410C'
        b.append(f'<circle class="blink" cx="476" cy="{yy - 5:.1f}" r="3.5" fill="{hot}"/>')
        b.append(T(live_line, 'p600', 12, 488, yy, ls=1, fill=hot))
        css.append('.blink{animation:blink 1.8s steps(1) infinite}@keyframes blink{50%{opacity:.2}}')
    c1, w1 = chip(W - (44 if o.get('url') else 0), H / 2 - 14, lab, col, anchor='end')
    b.append(c1)
    if o.get('url'):
        b.append(arrow(W - 16, H / 2, t_['soft']))
    b.append(hairline(H - .5, th))
    css.append(REDUCE)
    label = f'{o["name"]}: {kick.lower()}. {o["about"]}' + (f' Live: {live_line.lower()}.' if live_line else '') + f' Status: {lab.lower()}.'
    return doc(W, H, label, ''.join(b), ''.join(css))


# =============================================================== expeditions (open research)
# One tile per study: a looping animation of the subject itself, the question it asked and what is
# published. No verdicts on the page; the repository holds the full log.
EXP_W, EXP_H, VIS_H = 600, 440, 240
BLUE = '#3B82F6'


def _bond(x1, y1, x2, y2, color, double, cls, w=3):
    if not double:
        return f'<path class="{cls}" pathLength="1" d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy)
    ox, oy = -dy / n * 4, dx / n * 4
    return (f'<path class="{cls}" pathLength="1" d="M{x1 + ox:.1f} {y1 + oy:.1f}L{x2 + ox:.1f} {y2 + oy:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path class="{cls}" pathLength="1" d="M{x1 - ox:.1f} {y1 - oy:.1f}L{x2 - ox:.1f} {y2 - oy:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')


def vis_molecule(cx, cy, th, u):
    """Acrylamide, H2C=CH-C(=O)-NH2: bonds draw in, atoms pop, then the molecule drifts."""
    t_ = TH[th]
    A = {'C1': ('C', -120, 28), 'C2': ('C', -60, -6), 'C3': ('C', 0, 28), 'O': ('O', 0, 92), 'N': ('N', 60, -6),
         'H1': ('H', -170, -2), 'H2': ('H', -120, 90), 'H3': ('H', -60, -66), 'H4': ('H', 112, 22), 'H5': ('H', 60, -66)}
    bonds = [('C1', 'C2', True), ('C2', 'C3', False), ('C3', 'O', True), ('C3', 'N', False), ('C1', 'H1', False),
             ('C1', 'H2', False), ('C2', 'H3', False), ('N', 'H4', False), ('N', 'H5', False)]
    col = {'C': '#5B6576', 'O': '#E5484D', 'N': '#3E63DD', 'H': '#E6EDF3' if th == 'dark' else '#FFFFFF'}
    ox, oy = cx + 30, cy - 12
    o, css = [f'<g class="mfl{u}"><g transform="translate({ox} {oy})">'], []
    o.append(f'<ellipse class="mring{u}" cx="-30" cy="12" rx="190" ry="96" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .08}" stroke-dasharray="3 7" style="transform-origin:-30px 12px"/>')
    bc = t_['soft']
    for k, (a, b, dbl) in enumerate(bonds):
        _, x1, y1 = A[a]
        _, x2, y2 = A[b]
        o.append(_bond(x1, y1, x2, y2, bc, dbl, f'bd{u}_{k}'))
        css.append(f'.bd{u}_{k}{{stroke-dasharray:1;animation:bd{u} .5s {.3 + k * .09:.2f}s ease-out both}}')
    css.append(f'@keyframes bd{u}{{from{{stroke-dashoffset:1}}}}')
    for k, (key, (el, x, y)) in enumerate(A.items()):
        r = 9 if el == 'H' else 16
        ink = '#14151A' if el == 'H' else '#FFFFFF'
        o.append(f'<g class="at{u}_{k}" style="transform-origin:{x}px {y}px"><circle cx="{x}" cy="{y}" r="{r}" fill="{col[el]}" stroke="{t_["line"]}" stroke-opacity=".25"/>'
                 + T(el, 'p600', 11 if el == 'H' else 14, x, y + (4 if el == 'H' else 5), 'middle', fill=ink) + '</g>')
        css.append(f'.at{u}_{k}{{animation:at{u} .45s {.55 + k * .07:.2f}s cubic-bezier(.3,1.6,.5,1) both}}')
    css.append(f'@keyframes at{u}{{from{{opacity:0;transform:scale(.2)}}}}')
    _, xo, yo = A['O']
    o.append(f'<circle class="ecl{u}" cx="{xo}" cy="{yo}" r="26" fill="#E5484D" opacity=".14"/>')
    o.append('</g></g>')
    css.append(f'.mfl{u}{{animation:mfl{u} 6s 1.6s ease-in-out infinite alternate}}@keyframes mfl{u}{{to{{transform:translate(0,-6px) rotate(-2deg)}}}}'
               f'.mring{u}{{animation:spin{u} 40s linear infinite}}@keyframes spin{u}{{to{{transform:rotate(360deg)}}}}'
               f'.ecl{u}{{transform-box:fill-box;transform-origin:center;animation:ecl{u} 2.6s ease-in-out infinite}}@keyframes ecl{u}{{50%{{transform:scale(1.35);opacity:.05}}}}')
    return ''.join(o), ''.join(css), 'ACRYLAMIDE  ·  C3H5NO'


def vis_bitgrid(cx, cy, th, u):
    """A bfloat16 matrix: a bit flips, and the checksum row and column point straight at it."""
    t_ = TH[th]
    cols, rows, cw, ch, g = 12, 6, 24, 16, 5
    gw, gh = cols * (cw + g) - g, rows * (ch + g) - g
    x0, y0 = cx - (gw + 10 + cw) / 2, cy - (gh + 10 + ch) / 2
    rnd = random.Random(u)
    o, css = [], []
    cell = lambda c, r: (x0 + c * (cw + g), y0 + r * (ch + g))
    for r in range(rows):
        for c in range(cols):
            x, y = cell(c, r)
            o.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{cw}" height="{ch}" rx="3" fill="{BLUE}" fill-opacity="{rnd.uniform(.12, .55):.2f}"/>')
    xc, yr = x0 + gw + 10, y0 + gh + 10
    for r in range(rows):
        o.append(f'<rect x="{xc:.0f}" y="{cell(0, r)[1]:.0f}" width="{cw}" height="{ch}" rx="3" fill="{C["flame"]}" fill-opacity=".08" stroke="{C["flame"]}" stroke-opacity=".6"/>')
    for c in range(cols):
        o.append(f'<rect x="{cell(c, 0)[0]:.0f}" y="{yr:.0f}" width="{cw}" height="{ch}" rx="3" fill="{C["flame"]}" fill-opacity=".08" stroke="{C["flame"]}" stroke-opacity=".6"/>')
    red = '#FF4D4F'
    for k, (r, c) in enumerate(((1, 3), (4, 8), (2, 10))):
        x, y = cell(c, r)
        d = k * 3
        o.append(f'<g class="fx{u}" style="animation-delay:{d}s">'
                 f'<path d="M{x + cw:.0f} {y + ch / 2:.0f}H{xc:.0f}M{x + cw / 2:.0f} {y + ch:.0f}V{yr:.0f}" stroke="{red}" stroke-width="1.4" stroke-dasharray="3 3"/>'
                 f'<rect x="{xc:.0f}" y="{y:.0f}" width="{cw}" height="{ch}" rx="3" fill="{red}" fill-opacity=".85"/>'
                 f'<rect x="{x:.0f}" y="{yr:.0f}" width="{cw}" height="{ch}" rx="3" fill="{red}" fill-opacity=".85"/></g>')
        o.append(f'<g class="ff{u}" style="animation-delay:{d}s"><rect x="{x - 2:.0f}" y="{y - 2:.0f}" width="{cw + 4}" height="{ch + 4}" rx="4" fill="{red}"/>'
                 + T('1', 'p600', 11, x + cw / 2, y + ch / 2 + 4, 'middle', fill='#FFFFFF') + '</g>')
    css.append(f'.ff{u},.fx{u}{{opacity:0;animation:ff{u} 9s infinite}}.fx{u}{{animation-name:fx{u}}}'
               f'@keyframes ff{u}{{0%,3%{{opacity:0}}6%,30%{{opacity:1}}36%,100%{{opacity:0}}}}'
               f'@keyframes fx{u}{{0%,9%{{opacity:0}}13%,30%{{opacity:1}}36%,100%{{opacity:0}}}}')
    return ''.join(o), ''.join(css), 'BFLOAT16 GEMM  ·  CHECKSUM ROW AND COLUMN'


def vis_hexscan(cx, cy, th, u):
    """A shipped binary read byte by byte: a real ELF64 x86-64 header, then the body, under a moving scan."""
    t_ = TH[th]
    head = '7F 45 4C 46 02 01 01 00 00 00 00 00 00 00 00 00 02 00 3E 00 01 00 00 00'.split()
    rnd = random.Random(u * 3)
    data = head + [f'{rnd.randrange(256):02X}' for _ in range(7 * 12 - len(head))]
    rows, per, lh = 7, 12, 22
    bw = M('00 ', 'p500', 13)
    gw = 78 + per * bw
    x0, y0 = cx - gw / 2, cy - rows * lh / 2 + 12
    o, css = [], []
    o.append(f'<rect class="scan{u}" x="{x0 - 10:.0f}" y="{y0 - 16:.0f}" width="{gw + 16:.0f}" height="{lh}" rx="4" fill="{C["flame"]}" fill-opacity=".14"/>')
    o.append(f'<rect class="scan{u}" x="{x0 - 10:.0f}" y="{y0 - 16:.0f}" width="3" height="{lh}" fill="{C["flame"]}"/>')
    css.append(f'.scan{u}{{animation:scan{u} 5.6s steps({rows},end) infinite}}@keyframes scan{u}{{to{{transform:translateY({rows * lh}px)}}}}')
    for r in range(rows):
        y = y0 + r * lh
        o.append(T(f'{r * per:08X}', 'p500', 12, x0, y, fill=t_['faint']))
        for c in range(per):
            i = r * per + c
            colr = C['flame'] if i < 4 else (t_['soft'] if i < len(head) else t_['dim'])
            o.append(T(data[i], 'p500', 13, x0 + 78 + c * bw, y, fill=colr))
    o.append(f'<rect x="{x0 + 72:.0f}" y="{y0 - 15:.0f}" width="{bw * 4 + 2:.0f}" height="20" rx="4" fill="none" stroke="{C["flame"]}" stroke-width="1.4"/>')
    for k, (r, c) in enumerate(((3, 2), (5, 7), (6, 4))):
        o.append(f'<rect class="hit{u}" style="animation-delay:{k * 1.9:.1f}s" x="{x0 + 72 + c * bw:.0f}" y="{y0 + r * lh - 15:.0f}" width="{bw * 2:.0f}" height="20" rx="4" fill="none" stroke="{BLUE}" stroke-width="1.6"/>')
    css.append(f'.hit{u}{{opacity:0;animation:hit{u} 5.6s infinite}}@keyframes hit{u}{{0%,40%{{opacity:0}}48%,70%{{opacity:1}}80%,100%{{opacity:0}}}}')
    return ''.join(o), ''.join(css), 'SHIPPED BINARY  ·  ELF64 X86-64, BYTE BY BYTE'


def vis_crowd(cx, cy, th, u):
    """People who disagree (two colours that keep shifting) around one model whose confidence ring breathes."""
    t_ = TH[th]
    rnd = random.Random(u * 5)
    ny = cy + 54
    o, css = [], []
    pts = []
    for rad, n in ((92, 11), (128, 15)):
        for k in range(n):
            a = math.radians(200 + 140 * k / (n - 1))
            pts.append((cx + rad * math.cos(a), ny + rad * math.sin(a)))
    for x, y in pts:
        o.append(f'<path d="M{cx} {ny}L{x:.1f} {y:.1f}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"]}"/>')
    for k, (x, y) in enumerate(pts):
        a, b = (BLUE, C['flame']) if rnd.random() < .55 else (C['flame'], BLUE)
        o.append(f'<circle class="pp{u}" style="fill:{a};animation-duration:{rnd.uniform(3, 7):.1f}s;animation-delay:{rnd.uniform(0, 4):.1f}s;--b:{b}" cx="{x:.1f}" cy="{y:.1f}" r="7"/>')
    css.append(f'.pp{u}{{animation-name:pp{u};animation-iteration-count:infinite;animation-direction:alternate;animation-timing-function:steps(1,end)}}'
               f'@keyframes pp{u}{{to{{fill:var(--b)}}}}')
    o.append(f'<circle cx="{cx}" cy="{ny}" r="36" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .05}" stroke-width="5"/>')
    o.append(f'<circle class="cf{u}" cx="{cx}" cy="{ny}" r="36" fill="none" stroke="{C["flame"]}" stroke-width="5" stroke-linecap="round" pathLength="100" stroke-dasharray="62 100" transform="rotate(-90 {cx} {ny})"/>')
    o.append(f'<circle cx="{cx}" cy="{ny}" r="24" fill="{t_["ink"]}"/>')
    o.append(T('M', 'ac800', 20, cx, ny + 7, 'middle', fill=t_['page']))
    css.append(f'.cf{u}{{animation:cf{u} 4.5s ease-in-out infinite alternate}}@keyframes cf{u}{{from{{stroke-dasharray:30 100}}to{{stroke-dasharray:88 100}}}}')
    return ''.join(o), ''.join(css), 'HUMAN DISAGREEMENT  ·  MODEL CONFIDENCE'


def vis_plimsoll(cx, cy, th, u):
    """A ship's load line: the mark is painted before the voyage, and the water rises to meet it."""
    t_ = TH[th]
    paint = '#E6EDF3' if th == 'dark' else '#14151A'
    mx, my = cx - 70, cy + 4
    o, css = [], []
    for y in range(int(cy - 110), int(cy + 130), 58):
        o.append(f'<path d="M0 {y}H{EXP_W}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"]}"/>')
        for x in range(18, EXP_W, 46):
            o.append(f'<circle cx="{x}" cy="{y + 7}" r="1.8" fill="{t_["line"]}" fill-opacity="{t_["line_op"] + .08}"/>')
    o.append(f'<circle cx="{mx}" cy="{my}" r="46" fill="none" stroke="{paint}" stroke-width="6"/>')
    o.append(f'<path d="M{mx - 72} {my}H{mx + 72}" stroke="{paint}" stroke-width="6"/>')
    o.append(T('L', 'ac800', 20, mx - 40, my - 54, 'middle', fill=paint) + T('R', 'ac800', 20, mx + 40, my - 54, 'middle', fill=paint))
    lx = cx + 70
    o.append(f'<path d="M{lx} {my - 52}V{my + 40}" stroke="{paint}" stroke-width="4"/>')
    for k, lab in enumerate(('TF', 'F', 'T', 'S', 'W', 'WNA')):
        y = my + (k - 3) * 16
        o.append(f'<path d="M{lx} {y}h30" stroke="{paint}" stroke-width="3"/>')
        o.append(T(lab, 'p600', 11, lx + 36, y + 4, fill=paint))
    wave = 'M-80 0' + ''.join(f' q20 -7 40 0 t40 0' for _ in range(10)) + f' V200 H-80 Z'
    water = '#1F6FEB' if th == 'dark' else '#54AEFF'
    o.append(f'<g class="wl{u}"><g class="wb{u}"><path class="wv{u}" transform="translate(0 {my})" d="{wave}" fill="{water}" fill-opacity=".34"/>'
             f'<path class="wv{u}" style="animation-duration:5s" transform="translate(-30 {my + 4})" d="{wave}" fill="{water}" fill-opacity=".22"/></g></g>')
    css.append(f'.wl{u}{{animation:wl{u} 2.6s .4s cubic-bezier(.2,.8,.2,1) both}}@keyframes wl{u}{{from{{transform:translateY(130px)}}}}'
               f'.wb{u}{{animation:wb{u} 3.2s 3s ease-in-out infinite alternate}}@keyframes wb{u}{{to{{transform:translateY(3px)}}}}'
               f'.wv{u}{{animation:wv{u} 3.4s linear infinite}}@keyframes wv{u}{{to{{translate:40px 0}}}}')
    return ''.join(o), ''.join(css), 'LOAD LINE  ·  PAINTED BEFORE THE VOYAGE'


def vis_orbit(cx, cy, th, u):
    t_ = TH[th]
    o = (f'<circle cx="{cx}" cy="{cy}" r="30" fill="{t_["planet1"]}" stroke="{t_["rim"]}" stroke-opacity=".5"/>'
         f'<ellipse cx="{cx}" cy="{cy}" rx="110" ry="34" fill="none" stroke="{C["flame"]}" stroke-opacity=".6" transform="rotate(-14 {cx} {cy})"/>')
    return o, '', 'NEW EXPEDITION'


VIS = {'molecule': vis_molecule, 'bitgrid': vis_bitgrid, 'hexscan': vis_hexscan, 'crowd': vis_crowd,
       'plimsoll': vis_plimsoll, 'orbit': vis_orbit}


def expedition_tile(e, idx, th):
    t_ = TH[th]
    panel = '#0F1520' if th == 'dark' else '#F6F8FA'
    b = [page(EXP_W, EXP_H, th),
         f'<clipPath id="vc{idx}"><rect x="1" y="1" width="{EXP_W - 2}" height="{VIS_H + 20}" rx="15"/></clipPath>',
         f'<g clip-path="url(#vc{idx})"><rect width="{EXP_W}" height="{VIS_H}" fill="{panel}"/>']
    grid = ''.join(f'M{x} 0V{VIS_H}' for x in range(20, EXP_W, 20)) + ''.join(f'M0 {y}H{EXP_W}' for y in range(20, VIS_H, 20))
    b.append(f'<path d="{grid}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] * .45:.3f}"/>')
    vis, css, caption = VIS[e['visual']](EXP_W / 2, VIS_H / 2, th, idx)
    b.append(vis)
    b.append(T(caption, 'p500', 10, 18, VIS_H - 14, ls=1.3, fill=t_['dim']))
    b.append('</g>')
    b.append(f'<path d="M1 {VIS_H}H{EXP_W - 1}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .03}"/>')
    b.append(f'<rect x="1" y="1" width="{EXP_W - 2}" height="{EXP_H - 2}" rx="15" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .03}" stroke-width="1.2"/>')
    k1 = f'EXPEDITION {idx:02d}'
    b.append(T(k1, 'p600', 12, 24, VIS_H + 36, ls=1.4, fill=C['flame']))
    b.append(T(f'·  {e["field"].upper()}  ·  PRE-REGISTERED', 'p500', 12, 24 + M(k1, 'p600', 12, 1.4) + 10, VIS_H + 36, ls=1.4, fill=t_['dim']))
    b.append(arrow(EXP_W - 34, VIS_H + 32, t_['soft']))
    nsize = min(30, fit(e['name'].upper(), 'ac800', EXP_W - 100, .02))
    b.append(T(e['name'].upper(), 'ac800', nsize, 24, VIS_H + 76, ls=nsize * .02, fill=t_['ink']))
    for k, ln in enumerate(wrap(e['question'], 'a500', 18, EXP_W - 48, 2)):
        b.append(T(ln, 'a500', 18, 24, VIS_H + 108 + k * 24, fill=t_['soft']))
    x = 24
    for s in e.get('published', []):
        w = M(s.upper(), 'p600', 11, 1.2) + 22
        b.append(f'<rect x="{x}" y="{EXP_H - 46}" width="{w:.0f}" height="24" rx="12" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .12}"/>')
        b.append(T(s.upper(), 'p600', 11, x + 11, EXP_H - 30, ls=1.2, fill=t_['dim']))
        x += w + 8
    label = (f'Expedition {idx:02d}: {e["name"]}, {e["field"].lower()}, pre-registered. {e["question"]} '
             f'Published: {", ".join(s.lower() for s in e.get("published", []))}. Opens the repository.')
    return doc(EXP_W, EXP_H, label, ''.join(b), css + REDUCE)


# =============================================================== the hangar
def hangar_tile(h, idx, lang, th):
    t_ = TH[th]
    Wt, Ht = 380, 148
    tag = wrap(h.get('tag') or h['about'], 'a500', 16, Wt - 44, 2)
    b = [page(Wt, Ht, th),
         f'<rect x="1" y="1" width="{Wt - 2}" height="{Ht - 2}" rx="14" fill="{t_["chip"]}" fill-opacity="{t_["chip_op"] * .6:.3f}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .03}" stroke-width="1.2"/>',
         T(f'B-{idx:02d}', 'p600', 12, 22, 34, ls=1.4, fill=C['flame'])]
    if lang:
        lw = M(lang.upper(), 'p500', 11, 1.2)
        b.append(f'<circle cx="{Wt - 30 - lw:.1f}" cy="30" r="5" fill="{LANG.get(lang, "#8A94A8")}"/>')
        b.append(T(lang.upper(), 'p500', 11, Wt - 20, 34, 'end', ls=1.2, fill=t_['dim']))
    nsize = min(26, fit(h['name'].upper(), 'ac800', Wt - 70, .02))
    b.append(T(h['name'].upper(), 'ac800', nsize, 22, 74, ls=nsize * .02, fill=t_['ink']))
    for k, ln in enumerate(tag):
        b.append(T(ln, 'a500', 16, 22, 102 + k * 21, fill=t_['dim']))
    b.append(f'<path d="M{Wt - 30} {Ht - 22}l9-9M{Wt - 28} {Ht - 31}h7v7" fill="none" stroke="{t_["soft"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>')
    return doc(Wt, Ht, f'{h["name"]}: {h["about"]}' + (f' Main language: {lang}.' if lang else ''), ''.join(b))


# =============================================================== footer
def footer(P, L):
    """Back on the ground: a sheet of the Climb Log's paper closes the page (the same in both themes)."""
    H = 190
    last = dmy(L['contrib']['last_day'])
    b = [f'<defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath></defs><g clip-path="url(#frame)">',
         f'<rect width="{W}" height="{H}" fill="{PAPER["sheet"]}"/>', topo_lines(W, H, 5, PAPER['line'], .5, levels=10, width=.9)]
    bw = 560
    b.append(f'<rect x="{(W - bw) / 2:.0f}" y="44" width="{bw}" height="104" rx="10" fill="{PAPER["card"]}" stroke="{PAPER["edge"]}"/>')
    b.append(T('END OF LOG', 'ax900', 30, W / 2, 92, 'middle', ls=4, fill=PAPER['ink']))
    b.append(T(f'BASE CAMP  ·  {P["identity"]["place"].upper()}  ·  EL. 70 M', 'p600', 13, W / 2, 116, 'middle', ls=1.4, fill=PAPER['route']))
    b.append(T(f'LAST TELEMETRY {last}  ·  REDRAWN NIGHTLY FROM PROFILE.TOML', 'p500', 11, W / 2, 136, 'middle', ls=1.2, fill=PAPER['dim']))
    b.append('</g>')
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{PAPER["edge"]}"/>')
    return doc(W, H, f'End of log. Base camp, {P["identity"]["place"]}, elevation 70 m. Last telemetry {last}. Every image on this page is redrawn nightly from profile.toml.', ''.join(b))


# =============================================================== phone versions (shown below 768px wide)
# Each is drawn 720 wide (or keeps its tile width) with text sized for a phone, where GitHub shows the README
# about 340 px wide. Same data, same animations.
NW = 720


def section_header_n(idx, title, caption, th):
    t_ = TH[th]
    H = 170
    accent = 64 + M(title.upper(), 'ac900', 66, 1.4)
    b = [page(NW, H, th), T(idx, 'p600', 22, 0, 82, ls=1.4, fill=C['flame']),
         T(title.upper(), 'ac900', min(66, fit(title.upper(), 'ac900', NW - 70, .02)), 60, 88, ls=1.4, fill=t_['ink']),
         T(caption.upper(), 'p500', 18, 0, 128, ls=1.4, fill=t_['dim']),
         f'<path d="M0 150H{NW}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .04}" stroke-width="1.6"/>',
         f'<rect class="acc" x="0" y="148" width="{min(accent, NW):.0f}" height="4" rx="2" fill="{C["flame"]}"/>']
    css = '.acc{transform-box:fill-box;transform-origin:0 50%;animation:acc 1s .3s cubic-bezier(.2,.8,.2,1) both}@keyframes acc{from{transform:scaleX(0)}}' + REDUCE
    return doc(NW, H, f'{idx} {title}. {caption}.', ''.join(b), css)


def mission_row_n(m, idx, camp, th):
    t_ = TH[th]
    tag = wrap(m['tagline'], 'a600', 34, NW - 40)
    about = wrap(m['about'], 'a500', 27, NW - 40)
    y_tag = 300
    y_about = y_tag + 44 * len(tag) + 14
    y_cmd = y_about + 38 * len(about) + 10
    H = y_cmd + 96
    css = []
    b = [f'<defs>{GLOW}</defs>', page(NW, H, th),
         f'<circle cx="120" cy="140" r="110" fill="{m["color"]}" opacity="{t_["glow_op"]}" filter="url(#glow2)"/>']
    p, pc = patch(120, 140, 108, m, idx, th)
    b.append(p)
    css.append(pc)
    x = 262
    b.append(T(f'MISSION {idx:02d}' + (f' · CAMP {camp}' if camp else ''), 'p500', 19, x, 74, ls=1.4, fill=t_['dim']))
    nsize = min(64, fit(m['name'].upper(), 'ac900', NW - x, .01))
    b.append(T(m['name'].upper(), 'ac900', nsize, x - 2, 74 + 16 + capH('ac900', nsize), ls=nsize * .01, fill=t_['ink']))
    lab, col = status(m['status'], th)
    c1, w1 = chip(x, 176, lab, col, size=20, h=42)
    b.append(c1)
    b.append(T(m['note'].upper(), 'p500', 18, x, 254, ls=1, fill=t_['dim']))
    for k, ln in enumerate(tag):
        b.append(T(ln, 'a600', 34, 20, y_tag + 34 + k * 44, fill=t_['ink']))
    for k, ln in enumerate(about):
        b.append(T(ln, 'a500', 27, 20, y_about + 30 + k * 38, fill=t_['dim']))
    cw = min(M(m['command'], 'p500', 23) + 40, NW - 40)
    b.append(f'<rect x="20" y="{y_cmd:.0f}" width="{cw:.0f}" height="56" rx="12" fill="{t_["chip"]}" fill-opacity="{t_["chip_op"]}" stroke="{t_["chip"]}" stroke-opacity="{t_["chip_line"]}"/>')
    b.append(T(m['command'], 'p500', 23, 40, y_cmd + 36, fill=t_['cmd']))
    b.append(hairline(H - 1, th, 0, NW))
    css.append(REDUCE)
    return doc(NW, H, f'Mission {idx:02d}: {m["name"]}. {m["tagline"]} {m["about"]} Status: {lab.lower()}, {m["note"]}. {m["command"]}.', ''.join(b), ''.join(css))


def orbit_row_n(o, idx, L, camp, th):
    t_ = TH[th]
    lab, col = status(o['status'], th)
    about = wrap(o['about'], 'a500', 27, NW - 40)
    live = []
    if o.get('live') == 'dodge' and 'dodge' in L:
        D = L['dodge']
        live = [f'{D["u5"]:,} PASSES UNDER 5 KM', f'{D["u1"]:,} UNDER 1 KM  ·  RUN OF {dmy(D["day"], False)}']
    H = 150 + 38 * len(about) + 34 * len(live) + 40
    b = [page(NW, H, th)]
    kick = {'live': f'IN ORBIT SINCE {dmy(o["since"])}', 'beta': f'IN ORBIT SINCE {dmy(o["since"])}',
            'parked': f'PARKED · SINCE {dmy(o["since"])}', 'docked': f'DOCKED WITH {o.get("docked_with", "").upper()}'}[o['status']]
    b.append(T((f'CAMP {camp} · ' if camp else '') + kick, 'p500', 19, 20, 52, ls=1.2, fill=t_['dim']))
    nsize = min(50, fit(o['name'].upper(), 'ac800', NW - 220, .02))
    b.append(T(o['name'].upper(), 'ac800', nsize, 18, 112, ls=nsize * .02, fill=t_['ink']))
    c1, _ = chip(NW - 20, 76, lab, col, size=19, h=40, anchor='end')
    b.append(c1)
    for k, ln in enumerate(about):
        b.append(T(ln, 'a500', 27, 20, 166 + k * 38, fill=t_['soft'] if k == 0 else t_['dim']))
    hot = C['hot'] if th == 'dark' else '#C2410C'
    for k, ln in enumerate(live):
        b.append(T(ln, 'p600', 20, 20, 166 + 38 * len(about) + 6 + k * 34, ls=1, fill=hot))
    b.append(hairline(H - 1, th, 0, NW))
    return doc(NW, H, f'{o["name"]}: {kick.lower()}. {o["about"]} Status: {lab.lower()}.', ''.join(b), REDUCE)


def expedition_tile_n(e, idx, th):
    """On a phone the tile is about 165 px wide: keep the animation, and only the name and field below it."""
    t_ = TH[th]
    panel = '#0F1520' if th == 'dark' else '#F6F8FA'
    H = 420
    b = [page(EXP_W, H, th),
         f'<clipPath id="vc{idx}"><rect x="1" y="1" width="{EXP_W - 2}" height="{VIS_H + 20}" rx="22"/></clipPath>',
         f'<g clip-path="url(#vc{idx})"><rect width="{EXP_W}" height="{VIS_H}" fill="{panel}"/>']
    vis, css, _ = VIS[e['visual']](EXP_W / 2, VIS_H / 2, th, idx)
    b += [vis, '</g>',
          f'<rect x="2" y="2" width="{EXP_W - 4}" height="{H - 4}" rx="22" fill="none" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .06}" stroke-width="3"/>']
    nsize = min(70, fit(e['name'].upper(), 'ac800', EXP_W - 60, .02))
    b.append(T(e['name'].upper(), 'ac800', nsize, 30, VIS_H + 30 + capH('ac800', nsize), ls=nsize * .02, fill=t_['ink']))
    b.append(T(e['field'].upper(), 'p600', 34, 30, H - 34, ls=1.2, fill=C['flame']))
    return doc(EXP_W, H, f'Expedition {idx:02d}: {e["name"]}, {e["field"].lower()}. {e["question"]}', ''.join(b), css + REDUCE)


def hangar_tile_n(h, idx, lang, th):
    t_ = TH[th]
    Wt, Ht = 380, 190
    nsize = min(60, fit(h['name'].upper(), 'ac800', Wt - 40, .02))
    b = [page(Wt, Ht, th),
         f'<rect x="2" y="2" width="{Wt - 4}" height="{Ht - 4}" rx="20" fill="{t_["chip"]}" fill-opacity="{t_["chip_op"] * .6:.3f}" stroke="{t_["line"]}" stroke-opacity="{t_["line_op"] + .06}" stroke-width="3"/>',
         T(h['name'].upper(), 'ac800', nsize, 20, 30 + capH('ac800', nsize) + 20, ls=nsize * .02, fill=t_['ink'])]
    if lang:
        b.append(f'<circle cx="34" cy="{Ht - 44}" r="11" fill="{LANG.get(lang, "#8A94A8")}"/>')
        b.append(T(lang.upper(), 'p600', 30, 56, Ht - 33, ls=1, fill=t_['dim']))
    return doc(Wt, Ht, f'{h["name"]}: {h["about"]}', ''.join(b))


def footer_n(P, L):
    H = 340
    last = dmy(L['contrib']['last_day'])
    b = [f'<defs><clipPath id="frame"><rect width="{NW}" height="{H}" rx="26"/></clipPath></defs><g clip-path="url(#frame)">',
         f'<rect width="{NW}" height="{H}" fill="{PAPER["sheet"]}"/>', topo_lines(NW, H, 5, PAPER['line'], .5, levels=10, width=1.2),
         f'<rect x="40" y="60" width="{NW - 80}" height="220" rx="16" fill="{PAPER["card"]}" stroke="{PAPER["edge"]}" stroke-width="2"/>',
         T('END OF LOG', 'ax900', 54, NW / 2, 150, 'middle', ls=4, fill=PAPER['ink']),
         T(f'BASE CAMP · {P["identity"]["place"].upper()}', 'p600', 22, NW / 2, 198, 'middle', ls=1.2, fill=PAPER['route']),
         T(f'LAST TELEMETRY {last}', 'p500', 19, NW / 2, 238, 'middle', ls=1.2, fill=PAPER['dim']), '</g>']
    return doc(NW, H, f'End of log. Base camp, {P["identity"]["place"]}. Last telemetry {last}.', ''.join(b))


# =============================================================== README
PHONE = '(max-width: 767px)'


def picture(key, alt, width='100%', height=None, q='', phone=True):
    """Dark and light, each with a phone version below 768px (no phone version for the link pills)."""
    size = f' height="{height}"' if height else f' width="{width}"'
    src_ = ''
    if phone:
        src_ += (f'<source media="(prefers-color-scheme: dark) and {PHONE}" srcset="assets/{key}-dark-n.svg{q}">'
                 f'<source media="{PHONE}" srcset="assets/{key}-light-n.svg{q}">')
    src_ += f'<source media="(prefers-color-scheme: dark)" srcset="assets/{key}-dark.svg{q}">'
    return f'<picture>{src_}<img alt="{esc(alt)}" src="assets/{key}-light.svg{q}"{size}></picture>'


def linked(url, inner, name=None):
    """Every picture sits inside an <a>: with no link of our own, GitHub wraps the <img> in an image link
    inside the <picture>, which breaks the dark/light switch. A name-only anchor keeps it intact."""
    return f'<a href="{esc(url)}">{inner}</a>' if url else f'<a name="{esc(name)}">{inner}</a>'


def readme(P, L, alts):
    I = P['identity']
    q = f'?v={L["contrib"]["last_day"]}'
    out = ['<!-- Generated by flightlog/build.py from profile.toml. Edit profile.toml, not this file. -->', '',
           '<div align="center">', '', linked(I['site'], picture('hero', alts['hero'], q=q)), '', '<br>', '']
    out.append(' '.join(linked(l['url'], picture(f'link-{k}', l['label'], height=40, phone=False)) for k, l in enumerate(P['links'])))
    out += ['', '</div>', '', '<br>', '']

    def header(key):
        out.append(linked(None, picture(f'head-{key}', alts[f'head-{key}']), name=key))
        out.append('')

    header('missions')
    for k, m in enumerate(P['missions'], 1):
        out += [linked(m['url'], picture(f'mission-{k}', alts[f'mission-{k}'])), '']
    out += ['<br>', '']
    header('orbit')
    for k, o in enumerate(P['orbit'], 1):
        slug = re.sub(r'[^a-z0-9]+', '-', o['name'].lower()).strip('-')
        out += [linked(o.get('url'), picture(f'orbit-{k}', alts[f'orbit-{k}'], q=q if o.get('live') else ''), name=slug), '']
    out += ['<br>', '']
    header('expeditions')
    out.append('<div align="center">')
    out.append('')
    out.append(' '.join(linked(e['url'], picture(f'expedition-{k}', alts[f'expedition-{k}'], width='49%')) for k, e in enumerate(P['expeditions'], 1)))
    out += ['', '</div>', '']
    papers = [f'<a href="{esc(l["url"])}">{esc(e["name"])} {esc(l["label"])}</a>' for e in P['expeditions'] for l in e.get('links', [])]
    if papers:
        out += ['<div align="center"><sub>Papers and preregistrations: ' + ' · '.join(papers) + '</sub></div>', '']
    out += ['<br>', '']
    header('hangar')
    out.append('<div align="center">')
    out.append('')
    out.append(' '.join(linked(h['url'], picture(f'hangar-{k}', alts[f'hangar-{k}'], width='32%')) for k, h in enumerate(P['hangar'], 1)))
    out += ['', '</div>', '', '<br>', '',
            f'<picture><source media="{PHONE}" srcset="assets/footer-n.svg{q}"><img src="assets/footer.svg{q}" width="100%" alt="{esc(alts["footer"])}"></picture>', '',
            '<div align="center"><sub>Every image here is an SVG in this repository, drawn from <a href="profile.toml">profile.toml</a> by '
            '<a href="flightlog/build.py">flightlog/build.py</a> and redrawn every night by a GitHub Action. '
            'Text is drawn as paths: no fonts, scripts or trackers.</sub></div>', '']
    return '\n'.join(out)


# Nothing executable or external may ever ship in an image: GitHub serves them to every visitor.
# An allowlist, parsed as XML: only these elements and attributes, only same-document references.
SVG_NS = '{http://www.w3.org/2000/svg}'
OK_EL = {'svg', 'title', 'style', 'defs', 'path', 'rect', 'clipPath', 'g', 'ellipse', 'circle', 'use', 'radialGradient',
         'stop', 'filter', 'feGaussianBlur', 'mask', 'linearGradient', 'animateMotion'}
OK_ATTR = {'aria-label', 'class', 'clip-path', 'cx', 'cy', 'd', 'dur', 'fill', 'fill-opacity', 'fill-rule', 'filter',
           'gradientUnits', 'height', 'href', 'id', 'mask', 'maskUnits', 'offset', 'opacity', 'path', 'pathLength', 'r',
           'repeatCount', 'role', 'rx', 'ry', 'stdDeviation', 'stop-color', 'stop-opacity', 'stroke', 'stroke-dasharray',
           'stroke-linecap', 'stroke-linejoin', 'stroke-opacity', 'stroke-width', 'style', 'transform', 'viewBox', 'width',
           'x', 'x1', 'x2', 'y', 'y1', 'y2'}
BAD_CSS = re.compile(r'\\|@(?!keyframes\b|media\b)|url\((?!#[\w-]+\))|image-set|image\(|src\s*:|expression\(', re.I | re.ASCII)
BAD_VAL = re.compile(r'url\((?!#[\w-]+\))|javascript:|data:', re.I | re.ASCII)
ASSET_NAME = re.compile(r'[a-z0-9-]+\.svg', re.ASCII)


def check_svg(name, svg):
    if not svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"') or '<!' in svg or '<?' in svg:
        raise SystemExit(f'{name}: not a plain SVG document')
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        raise SystemExit(f'{name}: not well-formed XML ({e})')
    for e in root.iter():
        tag = e.tag[len(SVG_NS):] if e.tag.startswith(SVG_NS) else None
        if tag not in OK_EL:
            raise SystemExit(f'{name}: element {e.tag!r} not allowed')
        for a, v in e.attrib.items():
            if a not in OK_ATTR:
                raise SystemExit(f'{name}: attribute {a!r} not allowed')
            if a == 'href' and not re.fullmatch(r'#[\w-]+', v, re.ASCII):
                raise SystemExit(f'{name}: href {v!r} is not a same-document reference')
            if BAD_VAL.search(v) or (a == 'style' and BAD_CSS.search(v)):
                raise SystemExit(f'{name}: value {v[:40]!r} not allowed')
        if tag == 'style' and BAD_CSS.search(e.text or ''):
            raise SystemExit(f'{name}: stylesheet construct not allowed')


def write(name, svg):
    if not ASSET_NAME.fullmatch(name):
        raise SystemExit(f'odd asset name {name!r}')
    check_svg(name, svg)
    os.makedirs(ASSETS, exist_ok=True)
    p = os.path.join(ASSETS, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg)
    return os.path.getsize(p)


def alt_of(svg):
    m = re.search(r'aria-label="([^"]*)"', svg)
    return (m.group(1) if m else '').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def main():
    P = load_profile()
    L = live_data(P)
    alts, sizes = {}, {}

    def put(key, fn, fn_n=None):
        """Draw one image in both themes (and its phone version); fn(theme) -> svg."""
        for th in THEMES:
            svg = fn(th)
            sizes[f'{key}-{th}.svg'] = write(f'{key}-{th}.svg', svg)
            if fn_n:
                sizes[f'{key}-{th}-n.svg'] = write(f'{key}-{th}-n.svg', fn_n(th))
        alts[key] = alt_of(svg)

    put('hero', lambda th: hero(P, L, th), lambda th: hero(P, L, th, n=True))
    for k, l in enumerate(P['links']):
        put(f'link-{k}', lambda th, l=l: link_pill(l['label'], l.get('primary', False), th))
    repos = L.get('repos', {})
    lang_of = lambda u: repos.get(u.rstrip('/'), {}).get('language', '')
    n_lang = len({lang_of(h['url']) for h in P['hangar']} - {''})
    heads = {'missions': ('01', 'Missions', f'{len(P["missions"])} in flight · every patch is a link'),
             'orbit': ('02', 'In orbit', 'projects · lighter upkeep'),
             'expeditions': ('03', 'Expeditions', f'open research · {len(P["expeditions"])} studies · pre-registered'),
             'hangar': ('04', 'The hangar', f'{len(P["hangar"])} more builds' + (f' · {n_lang} languages' if n_lang else ''))}
    for key, (i, t, c) in heads.items():
        put(f'head-{key}', lambda th, i=i, t=t, c=c: section_header(i, t, c, th), lambda th, i=i, t=t, c=c: section_header_n(i, t, c, th))
    camp_of = {name: ROMAN[k] for k, cp in enumerate(camps_from(P)) if k < len(ROMAN) for name in cp['names']}
    for k, m in enumerate(P['missions'], 1):
        put(f'mission-{k}', lambda th, m=m, k=k: mission_row(m, k, camp_of.get(m['name']), th), lambda th, m=m, k=k: mission_row_n(m, k, camp_of.get(m['name']), th))
    for k, o in enumerate(P['orbit'], 1):
        put(f'orbit-{k}', lambda th, o=o, k=k: orbit_row(o, k, L, camp_of.get(o['name']), th), lambda th, o=o, k=k: orbit_row_n(o, k, L, camp_of.get(o['name']), th))
    for k, e in enumerate(P['expeditions'], 1):
        put(f'expedition-{k}', lambda th, e=e, k=k: expedition_tile(e, k, th), lambda th, e=e, k=k: expedition_tile_n(e, k, th))
    for k, h in enumerate(P['hangar'], 1):
        put(f'hangar-{k}', lambda th, h=h, k=k: hangar_tile(h, k, lang_of(h['url']), th), lambda th, h=h, k=k: hangar_tile_n(h, k, lang_of(h['url']), th))
    svg = footer(P, L)
    sizes['footer.svg'] = write('footer.svg', svg)
    alts['footer'] = alt_of(svg)
    sizes['footer-n.svg'] = write('footer-n.svg', footer_n(P, L))
    with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(readme(P, L, alts))
    # the manifest lists every drawn image; anything else in assets/ is stale (a removed item, an old design)
    with open(os.path.join(HERE, 'assets.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(sorted(sizes)) + '\n')
    stale = [n for n in os.listdir(ASSETS) if n.endswith('.svg') and n not in sizes]
    for n in stale:
        os.remove(os.path.join(ASSETS, n))
    if stale:
        print(f'removed {len(stale)} stale images from assets/')
    if os.environ.get('FLIGHTLOG_FONTS'):
        G.save_cache(keys_full_ascii=tuple(G.FONTS))
    old = stale_sources(L)
    if old:
        raise SystemExit(f'drawn from last good values, but {", ".join(old)} is more than 3 days old: check the fetch')
    dark = sum(v for k, v in sizes.items() if '-light' not in k and '-n.svg' not in k)
    print(f'{len(sizes)} images, {sum(sizes.values()) / 1024:.0f} KB in all; a dark-mode visitor loads {dark / 1024:.0f} KB')
    for k in ('hero-dark.svg', 'mission-1-dark.svg', 'expedition-1-dark.svg', 'hangar-1-dark.svg', 'footer.svg'):
        print(f'  {k:22s} {sizes[k] / 1024:6.1f} KB')


if __name__ == '__main__':
    main()
