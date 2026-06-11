#!/usr/bin/env python3
"""Remove the flip-count credential ("60+ house flips" and all variants) site-wide.

Jorge's rule (2026-04-27): never use a flip count in marketing copy. Keep the
investor/renovation framing, drop the number. Run after any content generation
or bulk import; safe to re-run (idempotent).

Usage: python3 scrub_flip_count.py [file ...]   (no args = whole repo)
"""
import os
import re
import sys

SUBS = [
    # long/specific first
    (r'personally bought, renovated, and sold 60\+ investment properties', 'personally bought, renovated, and sold investment properties'),
    (r'has personally bought, renovated, and sold 60\+ homes', 'has personally bought, renovated, and sold homes as an investor'),
    (r'bought, renovated, and sold 60\+ homes', 'bought, renovated, and sold homes as an investor'),
    (r'bought, renovated, and sold over 60 homes', 'bought, renovated, and sold homes'),
    (r'bought, renovated, and resold over 60 homes', 'bought, renovated, and resold homes'),
    (r'bought, renovated, and sold over 60 NJ homes', 'bought, renovated, and sold NJ homes as an investor'),
    (r'Jorge has bought, renovated, and sold over 60\.', 'Jorge has bought, renovated, and sold them himself.'),
    (r'with 60\+ personal home flips', 'with hands-on renovation and investment experience'),
    (r"who's personally flipped 60\+ homes across Northern NJ", 'who has personally renovated and sold homes across Northern NJ as an investor'),
    (r"who's personally flipped 60\+ homes", 'who has personally renovated and sold homes as an investor'),
    (r'<strong>60\+ personal house flips\.</strong>', '<strong>Hands-on investor experience.</strong>'),
    (r', 60\+ personal house flips\.</p>', ', an investor with hands-on renovation experience.</p>'),
    (r'with 60\+ personal investment property transactions', 'with extensive personal investment-property experience'),
    (r'With 60\+ personal investment property transactions,', 'With deep hands-on investment-property experience,'),
    (r'and 60\+ personal investment property transactions', 'and hands-on investment-property experience'),
    (r'a track record of 60\+ personal investment property transactions', 'a hands-on track record of personal investment property transactions'),
    (r'a track record that includes 60\+ personal investment property transactions', 'a track record that includes extensive personal investment property work'),
    (r'has personally completed 60\+ investment property transactions', 'has extensive personal investment-property experience'),
    (r'has personally flipped 60\+ NJ homes as an investor', 'has personally renovated and sold NJ homes as an investor'),
    (r'who has flipped 60\+ NJ homes', 'who has flipped homes across NJ'),
    (r'As someone who has flipped 60\+ NJ homes', 'As an investor who has flipped homes across NJ'),
    (r'with 60\+ personal investment flips', 'with hands-on investment-renovation experience'),
    (r'and 60\+ personal investment flips', 'and extensive personal investment flips'),
    (r'60\+ personal investment property flips', 'extensive personal investment-property flips'),
    (r'60\+ personal fix-and-flip investment properties in NJ', 'extensive personal fix-and-flip investment experience in NJ'),
    (r'60\+ personal NJ fix-and-flips give him', 'Personal NJ fix-and-flips give him'),
    (r'and 60\+ investment flips of experience', 'and hands-on investment flip experience'),
    (r'y 60\+ investment flips of experience', 'y hands-on investment flip experience'),
    (r'60\+ Homes Personally Flipped in NJ', 'Hands-On Renovation &amp; Investment Experience'),
    (r'✓ 60\+ Casas Personally Flipped en NJ', '✓ Experiencia Práctica en Renovación e Inversión'),
    (r'\| 60\+ House Flips ?\|', '|'),
    (r' \| 60\+ House Flips', ''),
    (r' — 60\+ house flips\.', '.'),
    (r', 60\+ house flips\.', '.'),
    (r', 60\+ flips\.', '.'),
    (r'60\+ personal house flips — ', 'Personal house-flipping experience — '),
    (r'He has flipped 60\+ homes and been', 'He has flipped homes as an investor and been'),
    (r'He has flipped 60\+ homes personally and speaks', 'He has flipped homes personally and speaks'),
    (r'He has flipped 60\+ houses personally', 'He has flipped houses personally'),
    (r'He has flipped 60\+ houses in NJ', 'He has flipped houses across NJ'),
    (r'He has flipped 60\+ homes', 'He has flipped homes as an investor'),
    (r'Jorge personally flipped 60\+ houses', 'Jorge personally flipped houses across NJ'),
    (r'Jorge personally flipped 60\+ homes', 'Jorge personally flipped homes'),
    (r'Jorge personally bought and sold 60\+ houses', 'Jorge personally bought and sold houses as an investor'),
    (r'Jorge Ramirez has flipped 60\+ houses personally in NJ', 'Jorge Ramirez has flipped houses personally in NJ'),
    (r'Jorge has personally flipped 60\+ houses in NJ', 'Jorge has personally flipped houses in NJ'),
    (r'Jorge flipped 60\+ homes as an investor', 'Jorge flipped homes as an investor'),
    (r'Jorge Ramirez has 60\+ personal flips and', 'Jorge Ramirez is a hands-on flip investor and'),
    (r"I've personally flipped 60\+ homes in NJ", "I've personally flipped homes across NJ"),
    (r'personally flipped over 60 homes', 'personally flipped homes'),
    (r'personally renovated over 60 homes', 'personally renovated many homes'),
    (r'Having personally renovated 60\+ homes in NJ', 'Having personally renovated homes across NJ'),
    (r'Having renovated 60\+ homes', 'Having renovated homes across NJ'),
    (r'Having renovated 60\+ properties', 'Having renovated properties across NJ'),
    (r'Having bought over 60 homes as an investor', 'Having bought homes as an investor'),
    (r'Having personally flipped 60\+ NJ homes', 'Having personally flipped NJ homes'),
    (r'Having personally flipped 60\+ homes', 'Having personally flipped homes'),
    (r'Having flipped over 60 homes across', 'Having flipped homes across'),
    (r'having flipped 60\+ NJ homes', 'having flipped homes across NJ'),
    (r'having bought 60\+ as-is properties himself', 'having bought as-is properties himself'),
    (r'has bought and sold 60\+ homes in NJ', 'has bought and sold homes across NJ as an investor'),
    (r'bought and sold 60\+ NJ homes', 'bought and sold NJ homes as an investor'),
    (r'with 60\+ personal investment properties', 'with extensive personal investment experience'),
    (r', 60\+ personal investment properties\.', ', hands-on NJ investor.'),
    (r'Jorge Ramirez — 60\+ personal NJ investment properties,', 'Jorge Ramirez — hands-on NJ investor,'),
    (r'sold 60\+ New Jersey investment properties', 'sold New Jersey investment properties'),
    (r'sold 60\+ Nueva Jersey investment properties', 'sold Nueva Jersey investment properties'),
    (r'bought, renovated, and sold 60\+ NJ investment properties', 'bought, renovated, and sold NJ investment properties'),
    (r'invested in, renovated, and sold over 60 properties', 'invested in, renovated, and sold properties'),
    (r"who's owned and sold 60\+ properties in NJ", "who's owned and sold properties across NJ"),
    (r"who's owned and sold 60\+ properties en NJ", "who's owned and sold properties across NJ"),
    (r'who has personally renovated over 60 properties', 'who has personally renovated dozens of properties'),
    (r'evaluation\. 60\+ homes flipped\. 138 communities\.', 'evaluation. 138 communities.'),
    (r'60\+ homes flipped means', 'Investor experience means'),
    (r"Jorge's 60\+ Flip Advantage", "Jorge's Investor Advantage"),
    (r'His 60\+ flip background', 'His flip background'),
    (r'an investor with 60\+ flips', 'a hands-on flip investor'),
    (r'60\+ homes flipped personally\.', 'Hands-on investor experience.'),
    (r'<li>60\+ homes personally bought, renovated, and sold</li>', '<li>Homes personally bought, renovated, and sold as an investor</li>'),
    (r'<li>60\+ homes personally renovated and sold</li>', '<li>Homes personally renovated and sold as an investor</li>'),
    (r'<li>60\+ homes personally flipped in NJ', '<li>Homes personally flipped in NJ'),
    (r'<li>60\+ homes personally flipped', '<li>Homes personally flipped'),
    (r'<h3>60\+ Homes Flipped</h3>', '<h3>Hands-On Investor</h3>'),
    (r'<h3>60\+ Casas Flipped</h3>', '<h3>Inversionista Activo</h3>'),
    (r'<h3>60\+ Inicios Flipped</h3>', '<h3>Inversionista Activo</h3>'),
    (r'<h3>60\+ Flips = Unmatched Condition Expertise</h3>', '<h3>Flip Experience = Unmatched Condition Expertise</h3>'),
    (r'<span>60\+ personal flips</span>', '<span>Hands-on investor experience</span>'),
    (r'Backed by investor insight from 60\+ personally flipped homes', 'Backed by hands-on investor insight from personally flipped homes'),
    (r'informed by 60\+ flip transactions', 'informed by his hands-on flip experience'),
    (r'done them himself on 60\+ properties', 'done them himself on his own investment properties'),
    (r'based on flipping 60\+ homes', 'based on his house-flipping experience'),
    (r'on top of 60\+ investment property transactions before that', 'on top of years of hands-on investment property work before that'),
    (r'purchased and flipped 60\+ properties', 'purchased and flipped properties'),
    (r'With 60\+ personal property flips', 'With extensive personal property flips'),
    (r'flip 60\+ homes for profit', 'flip homes for profit'),
    (r'As a former flipper \(60\+ homes pre-licensing\)', 'As a former flipper before getting licensed'),
    (r'my 60\+ flipped homes experience before licensing', 'my home-flipping experience before licensing'),
    (r'60\+ personal home flips &middot;', 'Hands-on flip experience &middot;'),
    (r"I've done sixty-plus house flips across", "I've flipped houses across"),
    (r'Sixty-plus house flips since 2017\. Nine of them in the towns on this list\.', "I've flipped houses since 2017 — nine of them in the towns on this list."),
    (r'selling 60\+ NJ homes \[thread\]', 'flipping NJ homes [thread]'),
    (r'flipped 60\+ as an investor before that', 'flipped homes as an investor before that'),
    (r'Sixty-plus house flips teaches you', 'House-flipping experience teaches you'),
    (r'has personally flipped 60\+ properties', 'has personally flipped properties'),
    (r'his experience flipping 60\+ homes', 'his hands-on flipping experience'),
    (r'brings 60\+ home flips worth of', 'brings years of hands-on home flips worth of'),
    (r'who has done it 60\+ times with his own money on the line', 'who has done it again and again with his own money on the line'),
    (r'closed 60\+ fix-and-flip properties', 'worked on fix-and-flip properties'),
    # generic catch-alls LAST
    (r'flipped 60-plus houses', 'flipped houses'),
    (r'flipped 60\+ homes', 'flipped homes'),
    (r'flipped 60\+ houses', 'flipped houses'),
    (r'flipped 60\+ NJ homes', 'flipped NJ homes'),
    (r'sold 60\+ homes', 'sold homes'),
    (r'sold 60\+ houses', 'sold houses'),
    (r'sixty-plus house flips', 'house flips'),
    (r'Sixty-plus house flips', 'House flips'),
    (r'60-plus house flips', 'house flips'),
    (r'renovated 60\+ homes', 'renovated many homes'),
    (r'\(60\+ personal flips\)', '(hands-on personal flips)'),
    (r'60\+ personal flips', 'extensive personal flip experience'),
    (r'60\+ personal house flips', 'personal house-flipping experience'),
    (r'60\+ house flips', 'personal house-flipping experience'),
    (r'60\+ homes flipped', 'hands-on flip experience'),
    (r'60\+ flips', 'hands-on flip experience'),
    (r'60\+ casas', 'amplia experiencia en casas'),
    (r'con más de 60 casas renovadas personalmente', 'con experiencia práctica en renovación e inversión inmobiliaria'),
    (r'más de 60 casas renovadas', 'numerosas casas renovadas'),
    (r'más de 60 (?:casas|propiedades|viviendas)', 'numerosas propiedades'),
    (r'as an investor in NJ as an investor', 'as an investor in NJ'),
    (r'as an investor as an investor', 'as an investor'),
    # capitalization repair for sentence-initial replacements
    (r'([.!?]["”]?\s+)personal house-flipping experience', r'\1Personal house-flipping experience'),
    (r'([.!?]["”]?\s+)hands-on flip experience', r'\1Hands-on flip experience'),
    (r'([.!?]["”]?\s+)extensive personal flip experience', r'\1Extensive personal flip experience'),
]

EXTS = ('.html', '.txt', '.json', '.py', '.md')
SELF = os.path.basename(__file__)


def scrub(path):
    try:
        text = open(path, encoding='utf-8').read()
    except (UnicodeDecodeError, OSError):
        return False
    orig = text
    for pat, rep in SUBS:
        text = re.sub(pat, rep, text)
    if text != orig:
        open(path, 'w', encoding='utf-8').write(text)
        return True
    return False


def main():
    targets = sys.argv[1:]
    if not targets:
        for root, dirs, fs in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')]
            targets.extend(os.path.join(root, fn) for fn in fs
                           if fn.endswith(EXTS) and fn != SELF)
    changed = [p for p in targets if scrub(p)]
    print(f"scrubbed {len(changed)} of {len(targets)} files")
    # report leftovers
    leftover_pat = re.compile(
        r'.{0,60}(?:(?<!\d)60\+|sixty[ -]plus|60 plus|flipped (?:over )?60|sold (?:over )?60|over 60 (?:homes|houses|properties)|más de 60|(?<!\d)60 (?:casas|propiedades|viviendas)|done it 60).{0,60}', re.I)
    ignore = re.compile(r'60\+ ?(minut|towns)|last 60|60-90|Age 60\+|60\+ (years|días|days)|walked 60\+ homes', re.I)
    n = 0
    for p in targets:
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for m in leftover_pat.findall(t):
            if ignore.search(m):
                continue
            n += 1
            print(f"LEFTOVER [{p}] {m.strip()[:120]}")
    print(f"{n} leftovers need manual review" if n else "no leftovers")


if __name__ == '__main__':
    main()
