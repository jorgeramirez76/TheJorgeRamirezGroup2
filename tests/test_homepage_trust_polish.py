#!/usr/bin/env python3
"""Homepage-only trust, attribution, and touch-target regression checks."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.normalize_public_trust_claims import normalize as normalize_public_trust
from scripts.normalize_spanish_fair_housing import normalize as normalize_spanish_fair_housing


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "index.html"
SPANISH_HOMEPAGE = ROOT / "es" / "index.html"


class HomepageTrustPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HOMEPAGE.read_text(encoding="utf-8")

    def test_unsupported_service_claims_are_absent(self) -> None:
        forbidden = (
            "i work 7 days a week",
            "available 7 days a week",
            "nyc commuter market specialist",
            "ai-powered",
            "ai powered",
            "knows this market cold",
            "invests here himself",
            "personally bought, renovated, and sold",
            "hands-on investor experience",
            "hands-on renovation &amp; investment experience",
            "hands-on experience on multiple sides of the table",
            "like an investor would",
            "bought and sold homes across nj as an investor",
            "known investor eye",
            "24–48 hours",
            "only on this site",
            "every nj commuter town",
            "no other nj agent",
            "42 sold homes",
            "public record · verified",
            "competitive-market win",
            "priced right from day one",
            "right school district",
            "without overpaying",
            "most sellers leave money on the table",
            "most agents get at least one",
            "almost always fixable",
            "many fsbo sellers end up",
            "the best homes in nj never",
            "12 other offers",
            "you won't overpay",
            "the #1 reason sellers",
            "many of my best results",
            "5.2%",
            "60–90 days",
            "mandatory 3-business-day",
            "2–3x faster",
            "$1,095,000",
            "10–20%",
            "5–13% more",
            "most nj real estate attorneys recommend",
            "best nj towns for families",
        )

        homepage = self.source.lower()
        present = [claim for claim in forbidden if claim in homepage]
        self.assertEqual([], present)
        self.assertIn("Here are the facts:", self.source)
        self.assertNotIn("What I can verify is", self.source)

    def test_market_and_transaction_copy_is_durable_and_attributed(self) -> None:
        self.assertIn("Third-Party Profile Snapshot", self.source)
        self.assertIn("Third-party profile data can change", self.source)
        self.assertIn("Reference tool · Not a live NJ Transit feed", self.source)
        self.assertIn("There is no universal best month", self.source)
        self.assertIn("brokerage compensation, which is negotiable and not set by law", self.source)
        self.assertIn("https://www.nj.gov/treasury/taxation/realty.shtml", self.source)
        self.assertNotIn("thejorgeramirezgroup.com/home-valuation.html", self.source)

    def test_homepage_design_tokens_remain_unchanged(self) -> None:
        for token in (
            "--primary-red:#C41230",
            "--dark-red:#8B0D22",
            "--gold:#B8962E",
            "--gold-light:#D4AF5A",
            "--black:#000000",
            "--light-gray:#F8F6F2",
            "--font-display:'Playfair Display'",
            "--font-body:'Inter'",
        ):
            self.assertIn(token, self.source)

    def test_search_and_social_titles_are_brand_first_and_consistent(self) -> None:
        expected = "Jorge Ramirez, NJ Realtor | The Jorge Ramirez Group"
        self.assertIn(f"<title>{expected}</title>", self.source)
        self.assertIn(f'<meta name="title" content="{expected}">', self.source)
        self.assertIn(f'<meta property="og:title" content="{expected}">', self.source)
        self.assertIn(f'<meta property="twitter:title" content="{expected}">', self.source)
        self.assertLessEqual(len(expected), 60)
        for county in ("Union", "Essex", "Morris", "Hudson", "Middlesex", "Somerset"):
            self.assertIn(county, self.source.split('<meta name="description"', 1)[1].split(">", 1)[0])

    def test_town_guide_copy_uses_durable_six_county_language(self) -> None:
        self.assertNotRegex(self.source, r"\b112\b")
        self.assertIn("Local Guides Across Six New Jersey Counties", self.source)
        self.assertIn("Explore Local NJ Town Guides", self.source)

    def test_testimonials_do_not_claim_an_unverified_platform_source(self) -> None:
        self.assertNotRegex(self.source, re.compile(r"Google Reviews?", re.IGNORECASE))
        self.assertNotIn("See All Reviews on Zillow", self.source)
        self.assertEqual(5, self.source.count(">Client testimonial</div>"))
        self.assertIn("Visit Jorge's Zillow Profile", self.source)

    def test_every_resource_link_has_a_44_pixel_touch_target(self) -> None:
        self.assertRegex(
            self.source,
            re.compile(
                r"\.resource-card\s+a\s*\{[^}]*"
                r"display\s*:\s*inline-flex\s*;[^}]*"
                r"align-items\s*:\s*center\s*;[^}]*"
                r"min-height\s*:\s*44px\s*;",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertIn(
            '<a href="/communities" class="resource-link">Explore Towns →</a>',
            self.source,
        )

    def test_town_guide_card_uses_durable_source_language(self) -> None:
        self.assertIn(
            "Start with local housing context and links to municipal, transit, and school resources.",
            self.source,
        )
        self.assertNotIn(
            "Schools, property taxes, commute times, median prices, and neighborhood feel",
            self.source,
        )


class SpanishHomepageTrustPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SPANISH_HOMEPAGE.read_text(encoding="utf-8")
        cls.folded = cls.source.casefold()

    def test_spanish_homepage_uses_safe_english_parity_baselines(self) -> None:
        for expected in (
            "Estos son los datos: soy agente inmobiliario con licencia en Nueva Jersey",
            "Guías Locales en Seis Condados de Nueva Jersey",
            "Un CMA no equivale a una tasación y no garantiza un precio de venta.",
            "No existe un mes universalmente mejor.",
            "la compensación de corretaje, que es negociable y no está fijada por ley",
            "El abogado de Nueva Jersey que selecciones debe explicar el lenguaje contractual",
            "Las medianas municipales y las estimaciones automatizadas no reflejan todas las diferencias de una propiedad.",
            'href="/es/home-valuation"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.source)

    def test_spanish_homepage_has_no_unsupported_or_fixed_claims(self) -> None:
        forbidden = (
            "personalmente he comprado, renovado y vendido",
            "personalmente he comprado y revendido",
            "como inversionista",
            "experiencia práctica como inversionista",
            "experiencia práctica en renovación e inversión",
            "mis mejores resultados",
            "las mejores casas en nj nunca",
            "clientes favoritos",
            "todo el equipo —inspectores, abogados, contratistas— ya está listo",
            "disponible los 7 días",
            "trabajo los 7 días",
            "respuesta rápida garantizada",
            "días a la semana",
            "24 a 48 horas",
            "24–48 horas",
            "60 a 90 días",
            "60–90 días",
            "del 4% al 5%",
            "entre un 5% y un 13%",
            "$35,000 a $50,000",
            "$650,000 a $665,000",
            "$1,095,000",
            "$850,000 a $900,000",
            "$950,000 a $1,050,000",
            "del 10% al 20%",
            "revisión del abogado de 3 días",
            "período obligatorio de revisión",
            "de 2 a 3 veces más rápido",
            "las familias quieren cerrar antes de que termine el ciclo escolar",
            "maximiza tanto la exposición",
            "te diré exactamente",
            "número más preciso",
            "reseña verificada de google",
            "todas las 138 comunidades",
            "138 comunidades",
            "103 comunidades",
            "109 comunidades",
            "120 comunidades",
        )
        present = [claim for claim in forbidden if claim in self.folded]
        self.assertEqual([], present)
        self.assertNotRegex(
            self.source,
            re.compile(r'"@type"\s*:\s*"FAQPage"', re.IGNORECASE),
        )
        self.assertNotRegex(
            self.source,
            re.compile(r'condado de (?:Union|Essex|Morris|Middlesex|Hudson) \(\d+ pueblos\)', re.IGNORECASE),
        )

    def test_spanish_testimonial_attribution_is_neutral_and_complete(self) -> None:
        self.assertNotRegex(
            self.source,
            re.compile(r"Reseñas? (?:verificadas? )?de Google", re.IGNORECASE),
        )
        self.assertEqual(5, self.source.count(">Testimonio de cliente</div>"))
        self.assertEqual(5, self.source.count('class="testimonial-quote"'))
        self.assertIn("Visitar el Perfil de Jorge en Zillow", self.source)

    def test_spanish_contact_phone_and_footer_invariants_are_preserved(self) -> None:
        self.assertIn('<form id="contactForm" action="/api/lead" method="POST">', self.source)
        self.assertIn('name="_source" value="/es"', self.source)
        self.assertIn('href="tel:+19082307844"', self.source)
        self.assertIn("908-230-7844", self.source)
        self.assertIn("488 Springfield Avenue", self.source)
        self.assertIn("Keller Williams Premier Properties", self.source)
        self.assertIn("Licencia de NJ #1754604", self.source)
        phone_tag = re.search(r'<input\b(?=[^>]*\bname="phone")[^>]*>', self.source)
        self.assertIsNotNone(phone_tag)
        self.assertNotRegex(phone_tag.group(0), re.compile(r"\brequired\b", re.I))
        self.assertIn(
            "las actualizaciones por SMS requieren una suscripción opcional y separada",
            self.source,
        )
        self.assertIn('<a href="/es/counties/somerset-county">Condado de Somerset</a>', self.source)
        for county in ("Union", "Essex", "Morris", "Middlesex", "Hudson", "Somerset"):
            self.assertIn(f">Condado de {county}</a>", self.source)

    def test_spanish_homepage_schema_is_one_verified_entity_graph(self) -> None:
        blocks = re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            self.source,
            flags=re.I | re.S,
        )
        self.assertEqual(1, len(blocks))
        payload = json.loads(blocks[0])
        self.assertEqual("https://schema.org", payload["@context"])
        self.assertEqual(1, len(payload["@graph"]))
        website = payload["@graph"][0]
        self.assertEqual("WebSite", website["@type"])
        self.assertEqual("RealEstateAgent", website["publisher"]["@type"])
        self.assertEqual(
            {
                "Union County, New Jersey",
                "Essex County, New Jersey",
                "Morris County, New Jersey",
                "Hudson County, New Jersey",
                "Middlesex County, New Jersey",
                "Somerset County, New Jersey",
            },
            {area["name"] for area in website["publisher"]["areaServed"]},
        )
        self.assertNotRegex(self.source, re.compile(r'"@type"\s*:\s*"(?:FAQPage|Service|Offer)"'))

    def test_normalizers_remove_legacy_spanish_homepage_trust_claims_idempotently(self) -> None:
        legacy = """<html><body>
<span class="stat-number" data-target="138" data-suffix="">103</span><span class="stat-label">Comunidades de NJ</span>
<p>Personalmente he comprado, renovado y vendido casas en Nueva Jersey como inversionista.</p>
<p>Muchos de mis mejores resultados vienen de casas que no se vendieron.</p>
<p>Trabajo los 7 días de la semana. Respuesta rápida garantizada.</p>
<div class="credential-item">✓ Disponible los 7 días de la semana</div>
<div class="testimonial-location">Reseña verificada de Google</div>
<p>La comisión de bienes raíces es del 4% al 5%; los costos suelen ir de $35,000 a $50,000.</p>
<p>La venta promedio toma de 60 a 90 días y el período obligatorio de revisión del abogado es de 3 días.</p>
<p>En Summit la mediana es de $1,095,000 y el estimado puede desviarse del 10% al 20%.</p>
<p>Un agente vende entre un 5% y un 13% más que una venta por dueño.</p>
<p>Las familias quieren cerrar antes de que termine el ciclo escolar, lo que maximiza tanto la exposición como el precio.</p>
<a href="/es/counties/union-county">Condado de Union (21 pueblos)</a>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage"}</script>
</body></html>"""

        for normalizer in (
            lambda value: normalize_public_trust(value, "es/index.html")[0],
            lambda value: normalize_spanish_fair_housing(value, "es/index.html"),
        ):
            with self.subTest(normalizer=normalizer):
                updated = normalizer(legacy)
                self.assertNotRegex(
                    updated,
                    re.compile(r'"@type"\s*:\s*"FAQPage"', re.IGNORECASE),
                )
                self.assertNotIn("inversionista", updated.casefold())
                self.assertNotIn("mis mejores resultados", updated.casefold())
                self.assertNotIn("7 días", updated.casefold())
                self.assertNotIn("garantizada", updated.casefold())
                self.assertNotIn("Reseña verificada de Google", updated)
                self.assertNotRegex(updated, re.compile(r"(?:103|109|120|138) comunidades", re.I))
                self.assertNotRegex(updated, re.compile(r"Condado de Union \(\d+ pueblos\)", re.I))
                self.assertNotIn("4% al 5%", updated)
                self.assertNotIn("60 a 90 días", updated)
                self.assertNotIn("$1,095,000", updated)
                self.assertNotIn("10% al 20%", updated)
                self.assertNotIn("5% y un 13%", updated)
                self.assertNotIn("familias quieren cerrar", updated.casefold())
                self.assertEqual(updated, normalizer(updated))


if __name__ == "__main__":
    unittest.main(verbosity=2)
