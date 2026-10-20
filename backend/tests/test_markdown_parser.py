from app.core.markdown import CustomBlock, CustomBlockHandler, CustomBlockRegistry, MarkdownParser


def make_parser() -> MarkdownParser:
    return MarkdownParser()


def test_keeps_markdown_structure():
    source = "# Заголовок\n\nТекст урока\n"

    parsed = make_parser().parse(source)

    assert parsed.content == source
    assert parsed.custom_blocks == ()
    assert parsed.assets == ()


def test_code_block_is_not_cleaned():
    source = "```html\n<script>alert(1)</script>\n```\n"

    parsed = make_parser().parse(source)

    assert "<script>alert(1)</script>" in parsed.content


def test_html_is_removed():
    parsed = make_parser().parse("<div>\nraw html\n</div>\n\nТекст урока\n")

    assert "raw html" not in parsed.content
    assert "Текст урока" in parsed.content


def test_extracts_custom_block():
    source = ":::test\nКакой тип вернёт `type(1.0)`?\n:::\n"

    parsed = make_parser().parse(source)

    assert len(parsed.custom_blocks) == 1
    assert parsed.custom_blocks[0].type == "test"
    assert parsed.custom_blocks[0].content == "Какой тип вернёт `type(1.0)`?"
    assert parsed.custom_blocks[0].implemented is False


def test_unclosed_custom_block_is_a_text():
    source = ":::test\nбез закрытия\n"

    parsed = make_parser().parse(source)

    assert parsed.custom_blocks == ()


def test_extracts_assets():
    source = "![Схема](assets/schema.png)\n\n[Данные](assets/data.csv)\n"

    parsed = make_parser().parse(source)

    assert [asset.asset_id for asset in parsed.assets] == ["schema.png", "data.csv"]
    assert parsed.assets[0].kind == "image"
    assert parsed.assets[0].alt == "Схема"
    assert parsed.assets[1].kind == "file"


def test_extracts_video_asset():
    source = "[Ролик](assets/lesson.mp4)\n"

    parsed = make_parser().parse(source)

    assert parsed.assets[0].kind == "video"


def test_external_links_are_not_assets():
    source = "![Логотип](https://example.com/logo.png)\n"

    parsed = make_parser().parse(source)

    assert parsed.assets == ()


def test_image_in_code_block_is_not_asset():
    source = "```markdown\n![не ассет](assets/fake.png)\n```\n"

    parsed = make_parser().parse(source)

    assert parsed.assets == ()


def test_table_is_kept_as_is():
    source = "| Тип | Описание |\n| --- | --- |\n| `int` | Целое число |\n"

    parsed = make_parser().parse(source)

    assert parsed.content == source


def test_autolink_is_kept():
    source = "Ссылка: <https://example.com/docs>\n"

    parsed = make_parser().parse(source)

    assert parsed.content == source


def test_custom_block_handler_can_be_registered():
    class VideoHandler(CustomBlockHandler):
        type = "video"

        def parse(self, content: str) -> CustomBlock:
            return CustomBlock(type="video", content=content, implemented=True)

    registry = CustomBlockRegistry(handlers=[VideoHandler()])

    parsed = MarkdownParser(custom_blocks=registry).parse(":::video\nhttps://example.com\n:::\n")

    assert parsed.custom_blocks[0].implemented is True
