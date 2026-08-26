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
        if any(part in {".git", "node_modules"} for part in path.parts):
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


if __name__ == "__main__":
    unittest.main()
