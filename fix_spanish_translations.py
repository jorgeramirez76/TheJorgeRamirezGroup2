#!/usr/bin/env python3
"""
Fix translation quality issues across all 341 Spanish pages.

Strategy:
- Apply targeted regex replacements with word boundaries
- Avoid breaking URLs, schema @id values, and href attributes
- Skip lines that contain URL patterns (https://, .html, /paths)
- Process line by line so we don't munge multi-line JSON-LD blocks

Safe to run repeatedly (idempotent — fixes only catch English text).
"""
import re
from pathlib import Path

ROOT = Path('/Users/teddy/TheJorgeRamirezGroup2')

# Patterns where we should NOT do replacements (URL contexts)
URL_GUARD = re.compile(r'(https?://|\.html|@id|@type|"url"|"@id"|href=|src=|"item"|"name":\s*"[A-Z])')

# Replacements: (regex pattern, replacement)
# Order matters — more specific phrases first
REPLACEMENTS = [
    # ============ FIX BAD "Inicios" → "Casas" ============
    # "Inicios" only ever came from incorrect translation of "Homes"
    (r'\bInicios\b', 'Casas'),

    # ============ Real Estate → Bienes Raíces ============
    (r'\breal estate agent\b', 'agente de bienes raíces'),
    (r'\bReal Estate Agent\b', 'Agente de Bienes Raíces'),
    (r'\breal estate\b', 'bienes raíces'),
    (r'\bReal Estate\b', 'Bienes Raíces'),
    (r'\bREAL ESTATE\b', 'BIENES RAÍCES'),

    # ============ Common phrases ============
    (r'\bFind homes for sale\b', 'Encuentra casas en venta'),
    (r'\bFind homes\b', 'Encuentra casas'),
    (r'\bhomes for sale\b', 'casas en venta'),
    (r'\bHomes for sale\b', 'Casas en venta'),
    (r'\bHomes for Sale\b', 'Casas en Venta'),
    (r'\bhome for sale\b', 'casa en venta'),
    (r'\bHome for Sale\b', 'Casa en Venta'),
    (r'\bhouses for sale\b', 'casas en venta'),
    (r'\bfor sale\b', 'en venta'),
    (r'\bFor Sale\b', 'En Venta'),
    (r'\bfor Sale\b', 'en Venta'),
    (r'\bFOR SALE\b', 'EN VENTA'),

    # ============ "in NJ" / "in New Jersey" ============
    (r'\bin NJ\b', 'en NJ'),
    (r'\bIn NJ\b', 'En NJ'),
    (r'\bin New Jersey\b', 'en Nueva Jersey'),
    (r'\bIn New Jersey\b', 'En Nueva Jersey'),
    (r'\bof New Jersey\b', 'de Nueva Jersey'),
    (r'\bof NJ\b', 'de NJ'),

    # ============ Common English words sneaking through ============
    (r'\band the\b', 'y la'),  # Note: could be "y el" depending on gender — best guess
    (r'\bAnd the\b', 'Y la'),
    (r'\bwith the\b', 'con la'),
    (r'\bWith the\b', 'Con la'),
    (r'\bof the\b', 'de la'),
    (r'\bOf the\b', 'De la'),
    (r'\bin the\b', 'en la'),
    (r'\bIn the\b', 'En la'),
    (r'\bto the\b', 'a la'),
    (r'\bTo the\b', 'A la'),
    (r'\bfrom the\b', 'desde la'),
    (r'\bFrom the\b', 'Desde la'),

    # ============ Real estate vocab ============
    (r'\bhome value\b', 'valor de casa'),
    (r'\bHome Value\b', 'Valor de Casa'),
    (r'\bhome buyer\b', 'comprador de casa'),
    (r'\bhome buyers\b', 'compradores de casa'),
    (r'\bhome seller\b', 'vendedor de casa'),
    (r'\bhome sellers\b', 'vendedores de casa'),
    (r'\bproperty value\b', 'valor de la propiedad'),
    (r'\bmarket value\b', 'valor de mercado'),
    (r'\blisting agent\b', 'agente de listado'),
    (r'\bbuyer agent\b', "agente del comprador"),
    (r'\bseller agent\b', 'agente del vendedor'),
    (r'\bclosing costs\b', 'costos de cierre'),
    (r'\bdown payment\b', 'pago inicial'),
    (r'\bpre[- ]approval\b', 'pre-aprobación'),
    (r'\bpre[- ]approved\b', 'pre-aprobado'),

    # ============ Common verbs ============
    (r'\bSpecializing in\b', 'Especializado en'),
    (r'\bspecializing in\b', 'especializado en'),
    (r'\bServing\b', 'Sirviendo'),
    (r'\bserving\b', 'sirviendo'),
    (r'\bExperienced\b', 'Experimentado'),
    (r'\bexperienced\b', 'experimentado'),

    # ============ Marketing phrases ============
    (r'\btop[- ]rated\b', 'mejor calificado'),
    (r'\bTop[- ]Rated\b', 'Mejor Calificado'),
    (r'\bTop Rated\b', 'Mejor Calificado'),
    (r'\bfull[- ]time\b', 'tiempo completo'),
    (r'\bFull[- ]Time\b', 'Tiempo Completo'),
    (r'\bFull[- ]time\b', 'Tiempo Completo'),
    (r'\bsince\b', 'desde'),
    (r'\bSince\b', 'Desde'),

    # ============ Numbers/units ============
    (r'\bdays on market\b', 'días en el mercado'),
    (r'\bDays on Market\b', 'Días en el Mercado'),
    (r'\bsquare feet\b', 'pies cuadrados'),
    (r'\bSquare Feet\b', 'Pies Cuadrados'),
    (r'\bbedrooms?\b', lambda m: 'habitación' if m.group(0).endswith('room') else 'habitaciones'),
    (r'\bBedrooms?\b', lambda m: 'Habitación' if m.group(0).endswith('room') else 'Habitaciones'),
    (r'\bbathrooms?\b', lambda m: 'baño' if m.group(0).endswith('room') else 'baños'),
    (r'\bBathrooms?\b', lambda m: 'Baño' if m.group(0).endswith('room') else 'Baños'),

    # ============ Time ============
    (r'\b[Tt]oday\b', 'hoy'),
    (r'\bThis Week\b', 'Esta Semana'),
    (r'\bthis week\b', 'esta semana'),
    (r'\bThis Month\b', 'Este Mes'),
    (r'\bthis month\b', 'este mes'),
    (r'\bThis Year\b', 'Este Año'),
    (r'\bthis year\b', 'este año'),
]

# Compile replacements
COMPILED = [(re.compile(p), r) for p, r in REPLACEMENTS]


def fix_line(line: str) -> str:
    """Apply all replacements to a single line, but skip URL-heavy lines."""
    # If the line is heavily URL-y, only do the safe replacements
    has_url = bool(URL_GUARD.search(line))

    if has_url:
        # For URL-heavy lines (often JSON-LD), only do clearly safe replacements
        # These are inside string values that won't break parsing
        safe_only = [
            (r'\bInicios\b', 'Casas'),
            # JSON-LD strings — translate description text in quotes
            (r'(": "[^"]*?)\bReal Estate\b', r'\1Bienes Raíces'),
            (r'(": "[^"]*?)\breal estate\b', r'\1bienes raíces'),
            (r'(": "[^"]*?)\bfor sale\b', r'\1en venta'),
            (r'(": "[^"]*?)\bin NJ\b', r'\1en NJ'),
            (r'(": "[^"]*?)\bhomes for sale\b', r'\1casas en venta'),
            (r'(": "[^"]*?)\bFind homes for sale\b', r'\1Encuentra casas en venta'),
        ]
        for pat, rep in safe_only:
            line = re.sub(pat, rep, line)
        return line

    # For normal text lines, apply all replacements
    for pat, rep in COMPILED:
        line = pat.sub(rep, line)
    return line


def fix_file(path: Path) -> int:
    """Apply fixes to a single file. Returns number of changes."""
    try:
        original = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return 0

    lines = original.split('\n')
    new_lines = [fix_line(line) for line in lines]
    new = '\n'.join(new_lines)

    if new != original:
        path.write_text(new, encoding='utf-8')
        # Count changes (rough — count differing chars / 5)
        return sum(1 for o, n in zip(lines, new_lines) if o != n)
    return 0


def main():
    print("🔧 Fixing translation quality issues across all Spanish pages")
    print("=" * 60)

    es_pages = sorted((ROOT / 'es').rglob('*.html'))
    print(f"Found {len(es_pages)} Spanish pages")
    print()

    total_changes = 0
    fixed_pages = 0
    by_category = {'top-level': 0, 'counties': 0, 'towns': 0, 'features': 0, 'blog': 0, 'other': 0}

    for i, p in enumerate(es_pages, 1):
        rel = str(p.relative_to(ROOT))
        changes = fix_file(p)
        if changes > 0:
            fixed_pages += 1
            total_changes += changes

            # Categorize
            if rel.startswith('es/counties/'):
                by_category['counties'] += 1
            elif rel.startswith('es/towns/'):
                by_category['towns'] += 1
            elif rel.startswith('es/features/'):
                by_category['features'] += 1
            elif rel.startswith('es/blog/'):
                by_category['blog'] += 1
            elif '/' not in rel.removeprefix('es/'):
                by_category['top-level'] += 1
            else:
                by_category['other'] += 1

        if i % 50 == 0:
            print(f"  [{i:3d}/{len(es_pages)}] processed...")

    print()
    print("=" * 60)
    print(f"✅ Fixed {fixed_pages} of {len(es_pages)} Spanish pages")
    print(f"   ~{total_changes} total line changes")
    print()
    print("By category:")
    for cat, n in by_category.items():
        if n > 0:
            print(f"  {cat:<12s} {n} pages fixed")


if __name__ == '__main__':
    main()
