"""Writes ../README.md. Every image is linked on purpose (GitHub otherwise links bare images to
their raw file; inside <summary> that link would steal the click, so the black box image sits in an
<a name> anchor, which has no href and so does not) and comes in wide and narrow cuts; the board art also comes in dark and light.

`<source media>` sees the viewport, not the README box: between 768 and 1060 px the profile
sidebar squeezes the README to 383 to 600 px, so "narrow" starts at 1060, not at phone widths.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NARROW = '(max-width: 1060px)'


def themed(base, alt, href, v=''):
    """`v` is a cache-busting query for images that changed (GitHub serves repo images through a CDN that caches them)."""
    a = f'assets/{base}'
    q = f'?v={v}' if v else ''
    return (f'<a href="{href}"><picture>'
            f'<source media="(prefers-color-scheme: dark) and {NARROW}" srcset="{a}-dark-n.svg{q}">'
            f'<source media="{NARROW}" srcset="{a}-light-n.svg{q}">'
            f'<source media="(prefers-color-scheme: dark)" srcset="{a}-dark.svg{q}">'
            f'<img alt="{alt}" src="{a}-light.svg{q}" width="100%">'
            f'</picture></a>')


def card(base, alt, href):
    a = f'assets/{base}'
    return (f'<a href="{href}"><picture>'
            f'<source media="{NARROW}" srcset="{a}-n.svg">'
            f'<img alt="{alt}" src="{a}.svg" width="100%">'
            f'</picture></a>')


HERO = themed('hero', 'Gautam Khosla on a split-flap departure board. Ascend higher, followed by a lightning bolt and a roller coaster. '
              'Now boarding: Counterseal, live. CRA Clock, live. Holdout, in beta.', 'https://gautamkhosla.com', v='ascend')

README = f'''<div align="center">

{HERO}

**Gautam Khosla** · Ottawa, Canada · Computer Engineering at uOttawa

I build software you can check instead of trust: approvals you sign with a passkey, records anyone can verify offline,
and pass or fail rules written down before the results. When something fails, the failure gets published too.

[gautamkhosla.com](https://gautamkhosla.com) · [YouTube](https://www.youtube.com/@GautamKhoslaOfficial) · [LinkedIn](https://www.linkedin.com/in/gautam-khosla/) · [Gautam Talks](https://gautamtalks.com) · [developwith.gt@gmail.com](mailto:developwith.gt@gmail.com)

</div>

<br>

<a name="products"></a>
{themed('head-products', 'Products. Now boarding. Three departures, every card is a link.', '#products')}

{card('card-counterseal', 'Counterseal. Every irreversible action gets a second seal. A brass seal presses green wax while the request goes 428 held, passkey OK, 204 sealed. Opens counterseal.gautamkhosla.com.', 'https://counterseal.gautamkhosla.com')}

**Counterseal** · Every irreversible action gets a second seal.<br>
Your AI agent gets a scoped token instead of your real API key. A call it cannot take back (a delete, a force push, a refund) is held until you approve that exact request, once, with a passkey, and with receipts on, every decision on a write becomes an entry in a public log anyone can check. The irreversible map covers 10 APIs, management APIs only: SQL sent straight over a database connection string never passes through Counterseal. Free public beta.<br>
[Website](https://counterseal.gautamkhosla.com) · [Source](https://github.com/GautamTalksDev/counterseal) · [npm](https://www.npmjs.com/package/counterseal) · `npx counterseal login`

{card('card-cra-clock', 'CRA Clock. 24 hours starts the moment you know. A split-flap countdown starts at 24:00:00 and a station clock starts from twelve the moment this page opens. Opens craclock.gautamkhosla.com.', 'https://craclock.gautamkhosla.com')}

**CRA Clock** · 24 hours starts the moment you know.<br>
The EU Cyber Resilience Act reporting clock, as a GitHub Action. It reads 12 lockfile formats, writes a CycloneDX 1.6 SBOM and checks every component against OSV, CISA KEV and FIRST EPSS. When something you ship is actively exploited, it opens an issue with the Article 14 deadlines and pre-filled early warning and notification drafts. Free and open source.<br>
[Website](https://craclock.gautamkhosla.com) · [GitHub Marketplace](https://github.com/marketplace/actions/cra-clock) · [Source](https://github.com/GautamTalksDev/cra-clock) · `uses: GautamTalksDev/cra-clock@v1`

{card('card-holdout', 'Holdout. Phones down. Together. Ember, the campfire mascot, flickers and blinks while sparks rise. Opens holdout.gautamkhosla.com.', 'https://holdout.gautamkhosla.com')}

**Holdout** · Phones down. Together.<br>
A campfire you keep alive with your friends. Everyone goes dark at the same time; if anyone breaks, everyone sees. No account, no ads, no tracking: your phone is your key. Android, in beta.<br>
[Website](https://holdout.gautamkhosla.com) · [Join the Android beta](https://holdout.gautamkhosla.com/beta/)

<br>

<a name="projects"></a>
{themed('head-projects', 'Projects. En route. Public, lighter upkeep, every row is a link.', '#projects')}
{themed('row-mcp-pin', 'mcp-pin, since 2 September: pins the MCP tools you approved and blocks them if they change. Live.', 'https://mcp-pin.gautamkhosla.com')}
{themed('row-dodge', 'DODGE, since 6 October: who makes Starlink dodge, with the latest daily count of predicted close passes. Live.', 'https://dodge.gautamkhosla.com')}
{themed('row-markd', 'MARKD, since 7 October: signed marks for AI output. Paused.', '#markd')}
{themed('row-merged', 'LEASH, WITNESS and SIGIL, since 7 October: merged into one product, Counterseal.', 'https://counterseal.gautamkhosla.com')}

- **[mcp-pin](https://mcp-pin.gautamkhosla.com)** pins the MCP tool definitions you approved and blocks the session when they change, and keeps a public log of the changes it sees. Zero runtime dependencies, MIT. [Source](https://github.com/GautamTalksDev/mcp-pin) · [npm](https://www.npmjs.com/package/mcp-pin) · [Spot the rug pull](https://mcp-pin.gautamkhosla.com/spot/) (a 60 second game) · [The 7 minute video](https://www.youtube.com/watch?v=tGtbDNr9qvE)
- **[DODGE](https://dodge.gautamkhosla.com)** asks who makes Starlink dodge: a daily screen of predicted close approaches between Starlink and everything else in low Earth orbit, each one attributed to an owner, signed and verifiable. SGP4 on public CelesTrak data; screening grade, not collision probability. [Source](https://github.com/GautamTalksDev/dodge)
- <a name="markd"></a>**MARKD** writes machine-readable "this is AI-generated" marks into images and text, with an Ed25519-signed manifest bound to the content hash, for EU AI Act Article 50(2). **Paused:** it works, but it is not under active development. It has no C2PA support and no robust watermark, and the EU Code of Practice expects those layers together with signed metadata.
- **LEASH, WITNESS and SIGIL** became one product in October 2026: LEASH's passkey-held calls, WITNESS's public receipt log and SIGIL's signed agent requests now live in [Counterseal](https://counterseal.gautamkhosla.com). [LEASH source](https://github.com/GautamTalksDev/leash)

<br>

<details>
<summary><a name="black-box"><picture><source media="{NARROW}" srcset="assets/blackbox-n.svg"><img src="assets/blackbox.svg" width="94%" alt="Flight recorder, do not open. Open the black box: every experiment inside had a pass or fail rule, written down in advance. Click to open."></picture></a></summary>

<br>

Each of these experiments was judged by a pass or fail rule written down before the results. The rules stay in the READMEs, so they cannot be quietly renegotiated later.

| Flight | The rule, written first | How it ended |
|---|---|---|
| [label-to-lab](https://github.com/GautamTalksDev/label-to-lab) | Predict a packaged food's measured acrylamide from its ingredient list: at least a 20% RMSE reduction over the category-median baseline | **FAIL.** 9.8%. A clear negative, published with the data |
| [assay-gpu](https://github.com/GautamTalksDev/assay-gpu) | Catch at least 90% of exponent-bit flips in bfloat16 GEMM | **FAIL.** 76%. The detector was not retuned and the bar was not moved. [Paper](https://doi.org/10.5281/zenodo.22054179) |
| [Lading](https://github.com/GautamTalksDev/Lading) | Prove vulnerabilities absent from shipped binaries | **FAIL.** Both pre-registered tests went against it, so it stopped by its own rule. Paper, corpus and audit trail [published](https://doi.org/10.5281/zenodo.22093232) |
| [jevbench](https://github.com/GautamTalksDev/jevbench) | A [preregistered](https://doi.org/10.5281/zenodo.22971413) test of whether a model's confidence tracks human disagreement | **Done.** Close to calibrated where people agree, overconfident where they split. [Paper](https://doi.org/10.5281/zenodo.22971491) |
| [PLIMSOLL](https://github.com/GautamTalksDev/plimsoll) | A public log that seals an evaluation's metric and threshold before the run | **No field data yet.** Its tests cannot be scored at N=0, and the README says so |

</details>

<details>
<summary><b>The hangar:</b> 19 more public builds, from hackathon projects to research tools</summary>

<br>

| Build | What it is |
|---|---|
| [Refledger](https://github.com/GautamTalksDev/refledger) | Checks whether a workflow runs the code you think it does, pins every action, and backs it with a public signed ledger |
| [Plumbline](https://github.com/GautamTalksDev/Plumbline) | A public, append-only log of MCP tool definitions that catches changes after publication |
| [Cairn](https://github.com/GautamTalksDev/Cairn) | Integrity monitoring for GPS-denied positioning: flags when a robot's pose estimate has silently gone wrong |
| [Vernier](https://github.com/GautamTalksDev/Vernier) | A deterministic diff for agent behaviour: record a run, re-drive it after a change, get a rule-based verdict |
| [Keyring](https://github.com/GautamTalksDev/keyring) | An access governance agent: finds the grants people and agents still hold, waits for a human, writes a verifiable audit trail |
| [Bedrock](https://github.com/GautamTalksDev/Bedrock) | Self-healing web scrapers; every automatic repair is tested against golden fixtures before it ships |
| [Ephemera](https://github.com/GautamTalksDev/Ephemera) | Preview environments without Kubernetes: open a PR, get a full stack with a live URL; close it, it is gone |
| [mayfly-guest](https://github.com/GautamTalksDev/mayfly-guest) | A snapshot-optimised Linux guest for Firecracker microVMs, with open measurement harnesses |
| [Porchlight](https://github.com/GautamTalksDev/porchlight) | An offline-first emergency network for neighbourhoods, for when the grid goes dark |
| [takehome](https://github.com/GautamTalksDev/takehome) | Canadian payroll deduction calculation, versioned by effective date, that shows its work |
| [groundhog](https://github.com/GautamTalksDev/groundhog) | Reads local coding-agent history and ranks the chores you keep paying an agent to redo. Local only |
| [AEGIS](https://github.com/GautamTalksDev/AEGIS) | Edge AI worksite safety on QNX 8.0 and a Raspberry Pi 5 in C++20; the safety loop never touches the network |
| [HyperShift](https://github.com/GautamTalksDev/HyperShift) | Describe infrastructure in plain English; five agents plan, build, scan, deploy and monitor it |
| [MetaShift](https://github.com/GautamTalksDev/MetaShift) | Multi-tenant observability that detects and auto-resolves conflicts across services, with incident replay |
| [Work-Shift](https://github.com/GautamTalksDev/Work-Shift) | An approval inbox for Slack: review AI-drafted messages before they send |
| [AeroGuard](https://github.com/GautamTalksDev/aeroguard-tech) | SOC incident triage built at ConUHacks, with similar-incident search and live updates |
| [gautamtalks.com](https://github.com/GautamTalksDev/gautamtalks-site) | The Gautam Talks creator site: hand written, zero frameworks, with a 3D room hidden inside |
| [gautamkhosla.com](https://github.com/GautamTalksDev/gautamtalksdev.github.io) | A personal site built as an engineering spec sheet; no framework, works offline |
| [DSA assignments](https://github.com/GautamTalksDev/DSA-Programming-Assignments) | Data structures and algorithms in Java, from university programming assignments |

</details>

<br>

<div align="center">
<sub>Every image on this page is a file in this repository: SVG with its text drawn as paths, and no fonts, scripts, trackers or third-party widgets.<br>
The boards flip once when the page loads (with reduced motion they arrive finished). DODGE's numbers come from its public daily data, dated on the row.</sub>
</div>
'''


def main():
    out = README
    prose = '\n'.join(line for line in out.splitlines() if not re.fullmatch(r'\|(-+\|)+', line))
    bad = re.findall(r'[\u2013\u2014]|--', prose)   # en and em dashes, or a double hyphen
    if bad:
        raise SystemExit(f'dashes in README: {bad}')
    for m in re.findall(r'(?:src|srcset)="(assets/[^"?]+)(?:\?[^"]*)?"', out):
        if not os.path.exists(os.path.join(ROOT, m)):
            raise SystemExit(f'missing asset {m}')
    with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print('README.md', len(out), 'chars', len(out.splitlines()), 'lines')


if __name__ == '__main__':
    main()
