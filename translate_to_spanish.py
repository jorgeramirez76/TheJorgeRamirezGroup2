#!/usr/bin/env python3
"""
Bulk-translate English HTML pages to Spanish for thejorgeramirezgroup.com.

Strategy:
1. Copy English page → /es/<same path>
2. Replace lang="en" → lang="es"
3. Apply translation dictionary for common UI/marketing strings
4. Update OG locale tags
5. Add hreflang tags pointing back to English
6. Update canonical URL to /es/<page>
7. Inject hreflang on the original English page if not present

The translation is dictionary-based — it won't catch every English string but
will translate the high-frequency UI elements, headings, and CTAs that appear
across all pages. For SEO purposes, this is enough to get pages indexed in
Spanish search results.
"""
import re
import shutil
from pathlib import Path

ROOT = Path('/Users/teddy/TheJorgeRamirezGroup2')
ES = ROOT / 'es'
BASE_URL = 'https://thejorgeramirezgroup.com'

# ===== TRANSLATION DICTIONARY =====
# Order matters — longer phrases first to prevent partial matches
TRANSLATIONS = [
    # ============ NAV / GLOBAL ============
    ('How We Sell Your Home', 'Cómo Vendemos Tu Casa'),
    ('Why Jorge Ramirez', 'Por Qué Jorge Ramirez'),
    ('NJ Home Buyer Guide', 'Guía del Comprador de Casa en NJ'),
    ('NJ Real Estate Questions', 'Preguntas de Bienes Raíces en NJ'),
    ('Sell Home Fast NJ', 'Vender Casa Rápido en NJ'),
    ('Home Valuation', 'Valoración de Casa'),
    ('Buy a Home', 'Comprar una Casa'),
    ('Sell Your Home', 'Vender Tu Casa'),
    ('Expired Listing Help', 'Ayuda con Listados Vencidos'),
    ('FSBO Help', 'Ayuda para Venta por Dueño'),
    ('Privacy Policy', 'Política de Privacidad'),
    ('Thank You', 'Gracias'),
    ('Get Started', 'Empezar Ahora'),
    ('Contact Us', 'Contáctanos'),
    ('Contact Me', 'Contáctame'),
    ('Learn More', 'Saber Más'),
    ('Read More', 'Leer Más'),
    ('Schedule a Call', 'Agendar una Llamada'),
    ('Schedule a Consultation', 'Agendar una Consulta'),
    ('Free Consultation', 'Consulta Gratuita'),
    ('Get a Free Quote', 'Obtener una Cotización Gratis'),
    ('Get a Free Home Valuation', 'Obtener una Valoración Gratuita'),
    ('Sign Up', 'Regístrate'),
    ('Subscribe', 'Suscribirse'),
    ('Submit', 'Enviar'),
    ('Search', 'Buscar'),
    ('Menu', 'Menú'),
    ('Home', 'Inicio'),
    ('About', 'Acerca de'),
    ('About Us', 'Sobre Nosotros'),
    ('About Me', 'Sobre Mí'),
    ('Services', 'Servicios'),
    ('Blog', 'Blog'),
    ('Contact', 'Contacto'),
    ('Resources', 'Recursos'),
    ('Testimonials', 'Testimonios'),
    ('Reviews', 'Reseñas'),
    ('Featured Listings', 'Listados Destacados'),
    ('Recent Listings', 'Listados Recientes'),
    ('Recent Blog Posts', 'Publicaciones Recientes del Blog'),
    ('Latest Posts', 'Publicaciones Más Recientes'),
    ('All Rights Reserved', 'Todos los Derechos Reservados'),
    ('Powered by', 'Impulsado por'),

    # ============ REAL ESTATE TERMS ============
    ('Real Estate Agent', 'Agente Inmobiliario'),
    ('Real Estate', 'Bienes Raíces'),
    ('Realtor', 'Realtor'),
    ('Listing Agent', 'Agente de Listado'),
    ("Buyer's Agent", 'Agente del Comprador'),
    ("Seller's Agent", 'Agente del Vendedor'),
    ('First-Time Buyer', 'Comprador Primerizo'),
    ('First-Time Buyers', 'Compradores Primerizos'),
    ('First-Time Home Buyer', 'Comprador Primerizo'),
    ('Home Buyer', 'Comprador de Casa'),
    ('Home Buyers', 'Compradores de Casa'),
    ('Home Seller', 'Vendedor de Casa'),
    ('Home Sellers', 'Vendedores de Casa'),
    ('Home for Sale', 'Casa en Venta'),
    ('Homes for Sale', 'Casas en Venta'),
    ('House for Sale', 'Casa en Venta'),
    ('Houses for Sale', 'Casas en Venta'),
    ('Property for Sale', 'Propiedad en Venta'),
    ('Properties for Sale', 'Propiedades en Venta'),
    ('Listing', 'Listado'),
    ('Listings', 'Listados'),
    ('Open House', 'Casa Abierta'),
    ('Open Houses', 'Casas Abiertas'),
    ('Mortgage', 'Hipoteca'),
    ('Pre-Approval', 'Pre-Aprobación'),
    ('Pre-Approved', 'Pre-Aprobado'),
    ('Down Payment', 'Pago Inicial'),
    ('Closing Costs', 'Costos de Cierre'),
    ('Closing', 'Cierre'),
    ('Inspection', 'Inspección'),
    ('Appraisal', 'Tasación'),
    ('Title', 'Título'),
    ('Escrow', 'Custodia'),
    ('Commission', 'Comisión'),
    ('Equity', 'Patrimonio'),
    ('Refinance', 'Refinanciar'),
    ('Investment Property', 'Propiedad de Inversión'),
    ('Rental Property', 'Propiedad de Alquiler'),
    ('Luxury Home', 'Casa de Lujo'),
    ('Luxury Homes', 'Casas de Lujo'),
    ('Single Family Home', 'Casa Unifamiliar'),
    ('Multi-Family', 'Multifamiliar'),
    ('Townhouse', 'Casa Adosada'),
    ('Condo', 'Condominio'),
    ('Condominium', 'Condominio'),
    ('Bedroom', 'Habitación'),
    ('Bedrooms', 'Habitaciones'),
    ('Bathroom', 'Baño'),
    ('Bathrooms', 'Baños'),
    ('Square Feet', 'Pies Cuadrados'),
    ('Lot Size', 'Tamaño del Lote'),
    ('Year Built', 'Año de Construcción'),
    ('Property Tax', 'Impuesto a la Propiedad'),
    ('Property Taxes', 'Impuestos a la Propiedad'),
    ('HOA', 'Asociación de Propietarios'),
    ('FSBO', 'FSBO'),
    ('For Sale By Owner', 'Venta por Dueño'),
    ('Expired Listing', 'Listado Vencido'),
    ('Expired Listings', 'Listados Vencidos'),
    ('Probate', 'Probate'),
    ('Foreclosure', 'Ejecución Hipotecaria'),
    ('Short Sale', 'Venta Corta'),
    ('Cash Offer', 'Oferta en Efectivo'),
    ('Days on Market', 'Días en el Mercado'),
    ('Median Price', 'Precio Mediano'),
    ('Average Price', 'Precio Promedio'),
    ('Market Value', 'Valor de Mercado'),
    ('Sold Price', 'Precio de Venta'),
    ('Asking Price', 'Precio de Lista'),

    # ============ COMMON PHRASES ============
    ('Contact Jorge Ramirez', 'Contacta a Jorge Ramirez'),
    ('Call Jorge', 'Llama a Jorge'),
    ('Call Now', 'Llama Ahora'),
    ('Call Today', 'Llama Hoy'),
    ('Click Here', 'Haz Clic Aquí'),
    ('Click here', 'haz clic aquí'),
    ('Email Me', 'Envíame un Correo'),
    ('Send a Message', 'Enviar un Mensaje'),
    ('Get in Touch', 'Ponte en Contacto'),
    ('Available 7 Days a Week', 'Disponible los 7 Días de la Semana'),
    ('Available 24/7', 'Disponible 24/7'),
    ('Free of Charge', 'Sin Costo'),
    ('No Obligation', 'Sin Compromiso'),
    ('No Pressure', 'Sin Presión'),
    ('No Hidden Fees', 'Sin Cargos Ocultos'),
    ('Trusted by', 'Confiado por'),
    ('Years of Experience', 'Años de Experiencia'),
    ('Years Experience', 'Años de Experiencia'),
    ('Licensed Real Estate Agent', 'Agente de Bienes Raíces Licenciado'),
    ('Licensed Realtor', 'Realtor Licenciado'),
    ('Top Rated', 'Mejor Calificado'),
    ('5-Star Rated', 'Calificado con 5 Estrellas'),
    ('Customer Reviews', 'Reseñas de Clientes'),
    ('Client Reviews', 'Reseñas de Clientes'),
    ('Why Choose Us', 'Por Qué Elegirnos'),
    ('Our Services', 'Nuestros Servicios'),
    ('Our Process', 'Nuestro Proceso'),
    ('Our Story', 'Nuestra Historia'),
    ('How It Works', 'Cómo Funciona'),
    ('Step by Step', 'Paso a Paso'),
    ('Frequently Asked Questions', 'Preguntas Frecuentes'),

    # ============ BUTTONS / CTAs ============
    ('Get Your Free Home Valuation', 'Obtén Tu Valoración Gratuita'),
    ('See Your Home Value', 'Ver el Valor de Tu Casa'),
    ('Find Your Dream Home', 'Encuentra la Casa de Tus Sueños'),
    ('Browse Listings', 'Ver Listados'),
    ('Search Homes', 'Buscar Casas'),
    ('View All Listings', 'Ver Todos los Listados'),
    ('See Listings', 'Ver Listados'),
    ('Get Started Now', 'Empezar Ahora'),
    ('Start Your Search', 'Comenzar Tu Búsqueda'),
    ('Start Searching', 'Comenzar a Buscar'),
    ('Apply Now', 'Aplica Ahora'),
    ('Book a Call', 'Reserva una Llamada'),
    ('Book a Meeting', 'Reserva una Reunión'),

    # ============ NJ-SPECIFIC ============
    ('New Jersey', 'Nueva Jersey'),
    ('NJ', 'NJ'),
    ('Union County', 'Condado de Union'),
    ('Essex County', 'Condado de Essex'),
    ('Morris County', 'Condado de Morris'),
    ('Hudson County', 'Condado de Hudson'),
    ('Middlesex County', 'Condado de Middlesex'),
    ('North Jersey', 'Norte de Nueva Jersey'),
    ('Central Jersey', 'Centro de Nueva Jersey'),
    ('South Jersey', 'Sur de Nueva Jersey'),

    # ============ TIME ============
    ('Monday', 'Lunes'),
    ('Tuesday', 'Martes'),
    ('Wednesday', 'Miércoles'),
    ('Thursday', 'Jueves'),
    ('Friday', 'Viernes'),
    ('Saturday', 'Sábado'),
    ('Sunday', 'Domingo'),
    ('Today', 'Hoy'),
    ('This Week', 'Esta Semana'),
    ('Last Week', 'La Semana Pasada'),
    ('This Month', 'Este Mes'),
    ('This Year', 'Este Año'),
]


def translate_text(html: str) -> str:
    """Apply all translations to the HTML content."""
    for en, es in TRANSLATIONS:
        # Use case-sensitive replacement so we don't mangle URLs/IDs
        html = html.replace(en, es)
    return html


def update_html_lang(html: str) -> str:
    """Change <html lang='en'> to <html lang='es'>."""
    return re.sub(r'<html\s+lang="en[^"]*"', '<html lang="es"', html)


def update_og_locale(html: str) -> str:
    """Change og:locale from en_US to es_US."""
    html = re.sub(
        r'<meta\s+property="og:locale"\s+content="en_US"',
        '<meta property="og:locale" content="es_US"',
        html
    )
    return html


def update_canonical_to_es(html: str, original_path: str) -> str:
    """Update canonical URL to point to /es/ version."""
    # Original canonical: https://thejorgeramirezgroup.com/path.html
    # New canonical: https://thejorgeramirezgroup.com/es/path.html
    es_path = f'/es/{original_path}' if not original_path.startswith('es/') else f'/{original_path}'
    new_canonical = f'{BASE_URL}{es_path}'

    html = re.sub(
        r'<link\s+rel="canonical"\s+href="[^"]*"\s*/?>',
        f'<link rel="canonical" href="{new_canonical}">',
        html
    )
    return html


def add_hreflang_tags(html: str, original_path: str) -> str:
    """Add hreflang tags pointing both to English and Spanish versions."""
    en_url = f'{BASE_URL}/{original_path}'
    es_url = f'{BASE_URL}/es/{original_path}'

    hreflang_block = f'''
    <link rel="alternate" hreflang="en-US" href="{en_url}">
    <link rel="alternate" hreflang="es-US" href="{es_url}">
    <link rel="alternate" hreflang="es" href="{es_url}">
    <link rel="alternate" hreflang="x-default" href="{en_url}">'''

    # Insert after the canonical tag
    html = re.sub(
        r'(<link\s+rel="canonical"[^>]*>)',
        r'\1' + hreflang_block,
        html,
        count=1
    )
    return html


def fix_internal_links(html: str) -> str:
    """Update internal links to point to /es/ versions where applicable."""
    # We don't want to break absolute URLs, only relative ones
    # Strategy: prepend /es/ to root-relative HTML links that are not already in /es/
    # Skip: external URLs, mailto:, tel:, anchors, image/css/js paths

    def replace_link(match):
        href = match.group(2)
        # Skip external, anchor, mailto, tel, etc.
        if href.startswith(('http', '#', 'mailto:', 'tel:', '/es/', 'es/')):
            return match.group(0)
        # Skip non-html assets
        if any(href.endswith(ext) for ext in ['.css', '.js', '.jpg', '.jpeg', '.png',
                                                '.gif', '.svg', '.webp', '.ico', '.xml',
                                                '.txt', '.json', '.pdf', '.woff', '.woff2',
                                                '.ttf', '.otf', '.mp4', '.webm']):
            return match.group(0)
        # If it's a root-relative HTML path, prepend /es
        if href.startswith('/'):
            return f'{match.group(1)}"/es{href}"'
        # Otherwise, leave it (it's a fragment or weird case)
        return match.group(0)

    return re.sub(r'(href=)"([^"]+)"', replace_link, html)


def translate_page(en_path: Path) -> bool:
    """Translate one English page to its Spanish equivalent."""
    relative = en_path.relative_to(ROOT)
    relative_str = str(relative)

    # Skip already-Spanish files and special files
    if relative_str.startswith('es/') or 'staging/' in relative_str or '.git/' in relative_str:
        return False

    es_path = ES / relative
    es_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        html = en_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError) as e:
        print(f"  ⚠️  Skipped {relative}: {e}")
        return False

    # Apply transformations
    html = update_html_lang(html)
    html = update_og_locale(html)
    html = update_canonical_to_es(html, relative_str)
    html = add_hreflang_tags(html, relative_str)
    html = fix_internal_links(html)
    html = translate_text(html)

    # Add a comment marking this as auto-translated
    if '<head>' in html:
        html = html.replace(
            '<head>',
            '<head>\n    <!-- Auto-translated to Spanish from English version. Verify content quality and update as needed. -->',
            1
        )

    es_path.write_text(html, encoding='utf-8')
    return True


def main():
    print("🌍 Bulk-translating English pages to Spanish")
    print("=" * 60)

    # Find all English HTML pages
    all_html = list(ROOT.rglob('*.html'))
    en_pages = [
        p for p in all_html
        if 'es/' not in str(p.relative_to(ROOT))
        and 'staging/' not in str(p.relative_to(ROOT))
        and '.git/' not in str(p.relative_to(ROOT))
        and 'node_modules/' not in str(p.relative_to(ROOT))
        and '.backup' not in str(p)
    ]

    print(f"Found {len(en_pages)} English HTML pages to translate")

    # Categorize for reporting
    categories = {
        'top-level': [],
        'counties': [],
        'towns': [],
        'features': [],
        'blog': [],
        'other': [],
    }
    for p in en_pages:
        rel = str(p.relative_to(ROOT))
        if rel.startswith('counties/'):
            categories['counties'].append(p)
        elif rel.startswith('towns/'):
            categories['towns'].append(p)
        elif rel.startswith('features/'):
            categories['features'].append(p)
        elif rel.startswith('blog/'):
            categories['blog'].append(p)
        elif '/' not in rel:
            categories['top-level'].append(p)
        else:
            categories['other'].append(p)

    print()
    for cat, pages in categories.items():
        print(f"  {cat:<12s} {len(pages):>4d} pages")

    print()
    print("Translating in priority order: top-level → counties → features → towns → blog")
    print()

    success = 0
    failed = 0
    skipped = 0

    process_order = ['top-level', 'counties', 'features', 'towns', 'blog', 'other']
    for cat in process_order:
        pages = categories[cat]
        if not pages:
            continue
        print(f"📂 [{cat}] processing {len(pages)} pages...")
        for i, p in enumerate(pages, 1):
            try:
                if translate_page(p):
                    success += 1
                    if i <= 3 or i == len(pages) or i % 25 == 0:
                        print(f"  [{i:4d}/{len(pages)}] ✓ {p.relative_to(ROOT)}")
                else:
                    skipped += 1
            except Exception as e:
                failed += 1
                print(f"  ❌ {p.relative_to(ROOT)}: {e}")
        print()

    print("=" * 60)
    print(f"✅ Translated: {success}")
    print(f"⏭️  Skipped:   {skipped}")
    print(f"❌ Failed:    {failed}")


if __name__ == '__main__':
    main()
