"""Static regression checks for the site's conversion and accessibility paths."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEAD_VALUATION_HOST = "value.thejorgeramirezgroup.com"
MISLEADING_VALUATION_PROMISE = re.compile(
    r"\b(?:free\s+)?instant(?:\s+online|\s+automated)?\s+"
    r"(?:home\s+)?(?:estimate|valuation)s?\b|"
    r"\b(?:estimaci[oó]n|valoraci[oó]n)\s+instant[aá]nea\b|"
    r"\b(?:under|less than)\s+60\s+seconds\b|\bin under a minute\b|"
    r"\btakes\s+60\s+seconds\b|03 · free · 60 seconds|"
    r"\btoma\s+60\s+segundos\b|\bestimado\s+instant[aá]neo\b|"
    r"\bestimaci[oó]n\s+automatizada\s+al\s+instante\b|"
    r"\bfree home valuation tool\b|\ban automated estimate at\b|"
    r"\buse the automated estimate as a starting point\b",
    re.IGNORECASE,
)


def public_html_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts and "node_modules" not in path.parts
    )


class ConversionUxStaticTests(unittest.TestCase):
    def test_public_forms_do_not_send_leads_to_formsubmit(self) -> None:
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_html_files()
            if "formsubmit.co" in path.read_text(encoding="utf-8").lower()
        ]
        self.assertEqual([], offenders)

    def test_primary_contact_forms_use_the_first_party_delivery_path(self) -> None:
        for relative in ("index.html", "es/index.html", "contact.html"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertRegex(text, r'<form[^>]+action="/api/lead"', relative)
            self.assertIn('name="leadType" value="website-contact"', text, relative)
            self.assertIn('name="_source"', text, relative)
            self.assertIn('name="_next"', text, relative)
            self.assertIn('name="_errorNext"', text, relative)

    def test_dead_valuation_host_is_absent_from_all_public_html(self) -> None:
        offenders = [
            str(path.relative_to(ROOT))
            for path in public_html_files()
            if DEAD_VALUATION_HOST in path.read_text(encoding="utf-8")
        ]
        self.assertEqual([], offenders)

    def test_first_party_valuation_links_stay_in_tab_and_make_no_instant_promise(self) -> None:
        new_tab_offenders: list[str] = []
        promise_offenders: list[str] = []
        for path in public_html_files():
            text = path.read_text(encoding="utf-8")
            if re.search(
                r'<a\b(?=[^>]*href=["\']/home-valuation["\'])(?=[^>]*target=["\']_blank["\'])',
                text,
                re.IGNORECASE,
            ):
                new_tab_offenders.append(str(path.relative_to(ROOT)))
            if (
                "features" not in path.relative_to(ROOT).parts
                and MISLEADING_VALUATION_PROMISE.search(text)
            ):
                promise_offenders.append(str(path.relative_to(ROOT)))

        self.assertEqual([], new_tab_offenders)
        self.assertEqual([], promise_offenders)

    def test_valuation_anchors_use_the_exact_first_party_path(self) -> None:
        failures: list[str] = []
        absolute_anchor = re.compile(
            r'<a\b[^>]*href=["\']https://thejorgeramirezgroup\.com/home-valuation["\']',
            re.IGNORECASE,
        )
        for path in public_html_files():
            if absolute_anchor.search(path.read_text(encoding="utf-8")):
                failures.append(str(path.relative_to(ROOT)))

        self.assertEqual([], failures)

    def test_home_valuation_has_a_first_party_accessible_intake(self) -> None:
        text = (ROOT / "home-valuation.html").read_text(encoding="utf-8")
        spanish_text = (ROOT / "es" / "home-valuation.html").read_text(encoding="utf-8")

        self.assertRegex(text, r'<main\s+id="main"')
        self.assertRegex(text, r'<form[^>]+id="valuationForm"[^>]+action="/api/lead"')
        self.assertIn('name="address"', text)
        self.assertIn('name="name"', text)
        self.assertIn('name="email"', text)
        self.assertIn('name="_honey"', text)
        self.assertIn('name="leadType" value="home-valuation"', text)
        self.assertIn('name="intent" value="Home valuation request"', text)
        self.assertIn('name="_source" value="/home-valuation"', text)
        self.assertIn('name="_next" value="/home-valuation"', text)
        self.assertIn('id="valuation-submitted"', text)
        self.assertIn('id="valuation-error"', text)
        self.assertIn("html:not(.js-enabled) .valuation-nojs-status:target", text)
        self.assertIn('id="valuationStatus"', text)
        self.assertIn('aria-live="polite"', text)
        self.assertIn('type="module" src="/js/home-valuation.js"', text)
        self.assertRegex(
            spanish_text,
            r'<form[^>]+id="valuationForm"[^>]+action="/api/lead"',
        )
        self.assertIn('name="leadType" value="home-valuation"', spanish_text)
        self.assertIn('name="intent" value="Solicitud de valoración de casa"', spanish_text)
        self.assertIn('name="_source" value="/es/home-valuation"', spanish_text)
        self.assertIn('name="_next" value="/es/home-valuation"', spanish_text)
        self.assertIn('href="#solicitud-valoracion"', spanish_text)
        self.assertIn('id="valuationStatus"', spanish_text)
        self.assertIn('aria-live="polite"', spanish_text)
        self.assertIn('type="module" src="/js/home-valuation.js"', spanish_text)
        for misleading_spanish_claim in (
            "la ve en el momento",
            "una primera cifra en el momento",
            "si quiere una cifra rápida",
        ):
            self.assertNotIn(misleading_spanish_claim, spanish_text.lower())

    def test_homepage_skip_link_targets_its_single_main_landmark(self) -> None:
        text = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertEqual(1, len(re.findall(r"<main(?:\s|>)", text, re.IGNORECASE)))
        self.assertEqual(1, len(re.findall(r'id=["\']main["\']', text, re.IGNORECASE)))
        self.assertRegex(text, r'<main\s+id="main"')
        self.assertIn('href="#main" class="skip-link"', text)

    def test_primary_spanish_and_calculator_pages_have_one_main_landmark(self) -> None:
        for relative in (
            "es/index.html",
            "tools/mortgage-calculator.html",
            "es/tools/mortgage-calculator.html",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(
                1,
                len(re.findall(r"<main(?:\s|>)", text, re.IGNORECASE)),
                relative,
            )
            self.assertEqual(1, text.lower().count("</main>"), relative)
            self.assertRegex(text, r'<main\s+id="main"', relative)

    def test_confirmation_and_calculator_pages_follow_homepage_brand_tokens(self) -> None:
        for relative in (
            "thank-you.html",
            "es/thank-you.html",
            "tools/mortgage-calculator.html",
            "es/tools/mortgage-calculator.html",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in ("#C41230", "#B8962E", "#FAFAF8", "Playfair Display", "Inter"):
                self.assertIn(token, text, f"{relative}: missing {token}")

    def test_confirmation_pages_avoid_unverified_delivery_and_response_promises(self) -> None:
        forbidden = (
            "went straight to jorge's inbox and his phone",
            "typically responds within a few hours",
            "always by the next morning",
            "available 8am–9pm, 7 days a week",
            "llegó directo al correo y al teléfono de jorge",
            "siempre antes de la mañana siguiente",
            "disponible de 8am a 9pm, los 7 días",
            "serves 138 communities",
            "atiende a 138 comunidades",
        )
        for relative in ("thank-you.html", "es/thank-you.html"):
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, text, relative)
            self.assertIn("<main", text, relative)

    def test_contact_page_uses_verified_credentials_and_no_response_guarantee(self) -> None:
        text = (ROOT / "contact.html").read_text(encoding="utf-8").lower()
        for forbidden in (
            "serving 138 communities",
            "hands-on renovation and investment experience",
            "openinghours",
            "response-time guarantee",
            "a reply within 24 hours",
            "138 towns across six nj counties",
            "standard nj commission structure",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("nj license #1754604", text)
        self.assertIn("broker compensation is negotiable and is not set by law", text)

    def test_every_town_page_has_exactly_one_main_landmark(self) -> None:
        town_pages = sorted((ROOT / "towns").glob("*.html"))
        town_pages += sorted((ROOT / "es" / "towns").glob("*.html"))
        failures: list[str] = []

        for path in town_pages:
            text = path.read_text(encoding="utf-8")
            opens = len(re.findall(r"<main(?:\s|>)", text, re.IGNORECASE))
            closes = len(re.findall(r"</main>", text, re.IGNORECASE))
            ids = len(re.findall(r'<main[^>]+id=["\']main["\']', text, re.IGNORECASE))
            if (opens, closes, ids) != (1, 1, 1):
                failures.append(
                    f"{path.relative_to(ROOT)}: main opens={opens}, closes={closes}, id=main={ids}"
                )

        self.assertEqual([], failures)

    def test_mobile_hero_video_is_explicitly_opt_in_for_large_screens(self) -> None:
        text = (ROOT / "js" / "main.js").read_text(encoding="utf-8")
        source_position = text.index("/videos/hero-loop.mp4")
        mobile_guard_position = text.index("(max-width: 768px)")

        self.assertLess(mobile_guard_position, source_position)
        self.assertIn("v.preload = 'metadata'", text)

    def test_mobile_containment_rules_cover_known_homepage_overflow_sources(self) -> None:
        text = (ROOT / "css" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("Homepage mobile containment", text)
        for selector in (
            ".stats-grid",
            ".listings-grid",
            ".features-grid",
            ".hero-carousel",
            ".hero-buttons",
        ):
            self.assertIn(selector, text)


if __name__ == "__main__":
    unittest.main()
