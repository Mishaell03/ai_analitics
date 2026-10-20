from app.core.markdown.sanitizer import MarkdownSanitizer, is_safe_url


def make_sanitizer() -> MarkdownSanitizer:
    return MarkdownSanitizer()


def test_removes_html_tags():
    assert make_sanitizer().sanitize("<div>text</div>") == "text"


def test_removes_dangerous_element_with_content():
    assert make_sanitizer().sanitize("a <script>alert(1)</script> b") == "a  b"


def test_removes_event_handlers():
    assert make_sanitizer().sanitize('<img src="x" onerror="alert(1)">') == ""


def test_removes_html_comments():
    assert make_sanitizer().sanitize("a <!-- secret --> b") == "a  b"


def test_keeps_safe_links():
    source = "[docs](https://docs.python.org/3/)"

    assert make_sanitizer().sanitize(source) == source


def test_removes_dangerous_link_destination():
    assert make_sanitizer().sanitize("[click](javascript:alert(1))") == "[click]()"


def test_removes_dangerous_link_definition():
    source = "[ref]: javascript:alert(1)"

    assert make_sanitizer().sanitize(source) == "[ref]: "


def test_keeps_inline_code_as_is():
    source = "вызов `<div>` и `x`"

    assert make_sanitizer().sanitize(source) == source


def test_is_safe_url():
    assert is_safe_url("https://example.com")
    assert is_safe_url("mailto@example.com")
    assert is_safe_url("assets/schema.png")
    assert is_safe_url("#anchor")
    assert not is_safe_url("javascript:alert(1)")
    assert not is_safe_url("data:text/html;base64,PHNjcmlwdD4=")
    assert not is_safe_url("vbscript:msgbox(1)")
