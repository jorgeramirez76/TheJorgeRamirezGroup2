import pathlib
import unittest
from html.parser import HTMLParser


ROOT = pathlib.Path(__file__).resolve().parents[1]
VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class FormAccessibilityParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._stack = []
        self._label_depth = 0
        self._hidden_depth = 0
        self.label_targets = set()
        self.controls = []
        self.ids = []
        self.fragment_links = []
        self.images_without_alt = []
        self.blank_links_without_noopener = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        style = attributes.get("style", "").replace(" ", "").lower()
        starts_hidden = (
            "hidden" in attributes
            or attributes.get("aria-hidden", "").lower() == "true"
            or "display:none" in style
        )
        if starts_hidden:
            self._hidden_depth += 1

        if tag == "label":
            self._label_depth += 1
            target = attributes.get("for")
            if target:
                self.label_targets.add(target)

        if tag in {"input", "select", "textarea"}:
            control_type = attributes.get("type", "text").lower()
            excluded_type = tag == "input" and control_type in {
                "hidden",
                "button",
                "submit",
                "reset",
                "image",
            }
            directly_named = bool(attributes.get("aria-label") or attributes.get("aria-labelledby"))
            self.controls.append(
                {
                    "descriptor": attributes.get("id") or attributes.get("name") or tag,
                    "id": attributes.get("id"),
                    "already_named": (
                        excluded_type
                        or self._hidden_depth > 0
                        or self._label_depth > 0
                        or directly_named
                    ),
                }
            )

        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)

        if tag == "img" and "alt" not in attributes:
            self.images_without_alt.append(attributes.get("src") or "img")

        if tag == "a":
            href = attributes.get("href", "")
            if href.startswith("#") and len(href) > 1:
                self.fragment_links.append(href[1:])
            if attributes.get("target", "").lower() == "_blank":
                rel = {token.lower() for token in (attributes.get("rel") or "").split()}
                if "noopener" not in rel:
                    self.blank_links_without_noopener.append(href or "a")

        if tag not in VOID_ELEMENTS:
            self._stack.append((tag, starts_hidden))

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            open_tag, starts_hidden = self._stack[index]
            if open_tag != tag:
                continue
            del self._stack[index:]
            if starts_hidden:
                self._hidden_depth -= 1
            if tag == "label":
                self._label_depth -= 1
            break


def html_files():
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", ".vercel", "node_modules"} for part in path.parts):
            continue
        yield path


class SitewideHtmlHygieneTests(unittest.TestCase):
    def test_every_html_document_declares_a_mobile_viewport(self):
        missing = []
        for path in html_files():
            html = path.read_text(encoding="utf-8", errors="replace").lower()
            if 'name="viewport"' not in html and "name='viewport'" not in html:
                missing.append(str(path.relative_to(ROOT)))

        self.assertEqual([], missing, "HTML files missing a viewport: " + ", ".join(missing))

    def test_visible_form_controls_have_accessible_names(self):
        unnamed = []
        for path in html_files():
            parser = FormAccessibilityParser()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            for control in parser.controls:
                if control["already_named"] or control["id"] in parser.label_targets:
                    continue
                unnamed.append(f"{path.relative_to(ROOT)}: {control['descriptor']}")

        self.assertEqual([], unnamed, "Form controls missing accessible names: " + ", ".join(unnamed))

    def test_ids_are_unique_and_same_page_fragments_resolve(self):
        findings = []
        for path in html_files():
            parser = FormAccessibilityParser()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            id_set = set(parser.ids)
            duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
            missing_fragments = sorted({value for value in parser.fragment_links if value not in id_set})
            if duplicate_ids:
                findings.append(f"{path.relative_to(ROOT)}: duplicate ids {', '.join(duplicate_ids)}")
            if missing_fragments:
                findings.append(
                    f"{path.relative_to(ROOT)}: missing fragments {', '.join(missing_fragments)}"
                )

        self.assertEqual([], findings, "Invalid document anchors: " + "; ".join(findings))

    def test_images_have_alt_attributes_and_blank_links_are_safe(self):
        findings = []
        for path in html_files():
            parser = FormAccessibilityParser()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            if parser.images_without_alt:
                findings.append(
                    f"{path.relative_to(ROOT)}: images without alt "
                    + ", ".join(parser.images_without_alt)
                )
            if parser.blank_links_without_noopener:
                findings.append(
                    f"{path.relative_to(ROOT)}: target=_blank without noopener "
                    + ", ".join(parser.blank_links_without_noopener)
                )

        self.assertEqual([], findings, "Unsafe or unnamed media links: " + "; ".join(findings))


if __name__ == "__main__":
    unittest.main()
