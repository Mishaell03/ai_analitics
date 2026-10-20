import assert from "node:assert/strict";
import {renderToStaticMarkup} from "react-dom/server";
import Markdown from "@/components/Markdown/Markdown.jsx";

/**
 * Проверка отрисовки Markdown.
 *
 * Компоненты собираются в SSR-режиме Vite, поэтому здесь проверяется
 * именно разметка: какие элементы появились и как они выглядят.
 *
 * Запуск: npm run test:render
 */

const source = [
    "# Заголовок урока",
    "",
    "Текст с **жирным**, *курсивом* и `кодом`.",
    "",
    "[документация](https://example.com/docs)",
    "",
    "[опасная](javascript:alert(1))",
    "",
    "| Тип | Описание |",
    "| --- | --- |",
    "| `int` | Целое |",
    "",
    "- пункт один",
    "- пункт два",
    "",
    "> Цитата урока",
    "",
    "```python",
    "name = \"Иван\"",
    "```",
    "",
    "![Схема](assets/variables.png)",
    "",
    ":::test",
    "Какой тип вернёт `type(1.0)`?",
    ":::",
    "",
    "<script>alert(1)</script>",
].join("\n");

const markup = renderToStaticMarkup(<Markdown content={source}/>);

// заголовки, абзацы и выделение
assert.match(markup, /<h1[^>]*>[\s\S]*?Заголовок урока[\s\S]*?<\/h1>/);
assert.match(markup, /<strong>[\s\S]*?жирным[\s\S]*?<\/strong>/);
assert.match(markup, /<em>[\s\S]*?курсивом[\s\S]*?<\/em>/);
assert.match(markup, /<code[^>]*>кодом<\/code>/);

// таблица
assert.match(markup, /<table[^>]*>/);
assert.match(markup, /<th[^>]*>[\s\S]*?Тип[\s\S]*?<\/th>/);

// списки и цитата
assert.match(markup, /<ul[^>]*>[\s\S]*?пункт один[\s\S]*?<\/ul>/);
assert.match(markup, /<blockquote[^>]*>/);

// блок кода с подсветкой
assert.match(markup, /<pre[^>]*>/);
assert.match(markup, /python/);
assert.match(markup, /tokenString/);

// картинка без готовой ссылки показывается заглушкой
assert.match(markup, /imagePlaceholder[^>]*>Схема</);

// кастомный блок
assert.match(markup, /data-type="test"/);

// опасная ссылка остаётся текстом, а не ссылкой
assert.ok(!markup.includes('href="javascript:'));
assert.match(markup, /\[опасная\]/);

// html не превращается в элементы
assert.ok(!markup.includes("<script>"));
assert.match(markup, /&lt;script&gt;/);

console.log("Markdown отрисовывается корректно");
