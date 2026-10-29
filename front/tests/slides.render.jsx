import assert from "node:assert/strict";
import {act} from "react";
import {createRoot} from "react-dom/client";
import {renderToStaticMarkup} from "react-dom/server";
import {JSDOM} from "jsdom";
import Markdown from "@/components/Markdown/Markdown.jsx";

const source = ":::slides\n![One](asset:m_first)\n![Two](asset:m_second)\n![Three](asset:m_third)\n:::";
const media = Object.fromEntries(["first", "second", "third"].map((name) => [
    `m_${name}`, {media_key: `m_${name}`, kind: "image", url: `https://example.com/${name}.png`},
]));
const html = renderToStaticMarkup(<Markdown content={source} media={media}/>);
assert.equal((html.match(/<img /g) || []).length, 1);
assert.match(html, /alt="One"/);
assert.ok(!html.includes("asset:"));

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div><button id="outside">Outside</button></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.getElementById("root"));
const render = async (content = source, files = media, onMediaError) => {
    await act(async () => root.render(<Markdown content={content} media={files} onMediaError={onMediaError}/>));
};
const viewer = () => document.querySelector("section");
const counter = () => viewer().querySelector('[aria-live="polite"]').textContent;
const button = (label) => viewer().querySelector(`button[aria-label="${label}"]`);
const click = async (element) => act(async () => element.click());
const key = async (target, value, options = {}) => act(async () => target.dispatchEvent(
    new window.KeyboardEvent("keydown", {key: value, bubbles: true, cancelable: true, ...options})
));
const swipe = async (dx, dy = 0, cancel = false) => {
    const stage = viewer().querySelector("img").parentElement;
    const touchEvent = (type, touches, changedTouches = []) => {
        const event = new window.Event(type, {bubbles: true});
        Object.assign(event, {touches, changedTouches});
        stage.dispatchEvent(event);
    };
    await act(async () => {
        touchEvent("touchstart", [{clientX: 100, clientY: 100}]);
        if (cancel) touchEvent("touchcancel", []);
        touchEvent("touchend", [], [{clientX: 100 + dx, clientY: 100 + dy}]);
    });
};

try {
    await render();
    assert.equal(counter(), "1 / 3");
    assert.equal(button("Назад").disabled, true);
    await click(button("Далее"));
    assert.equal(counter(), "2 / 3");
    assert.equal(viewer().querySelector("img").alt, "Two");
    await key(button("Далее"), "ArrowRight");
    assert.equal(counter(), "3 / 3");
    assert.equal(button("Далее").disabled, true);
    await key(viewer(), "ArrowRight");
    assert.equal(counter(), "3 / 3");
    await key(viewer(), "ArrowLeft");
    assert.equal(counter(), "2 / 3");
    await key(document.getElementById("outside"), "ArrowLeft");
    await key(viewer(), "ArrowLeft", {ctrlKey: true});
    assert.equal(counter(), "2 / 3");
    await key(viewer(), "ArrowLeft");
    await key(viewer(), "ArrowLeft");
    assert.equal(counter(), "1 / 3");

    await swipe(-80);
    assert.equal(counter(), "2 / 3");
    await swipe(80);
    assert.equal(counter(), "1 / 3");
    await swipe(-20);
    await swipe(-80, 120);
    await swipe(-80, 0, true);
    assert.equal(counter(), "1 / 3");

    await render(`${source}\n\n${source}`);
    const second = document.querySelectorAll("section")[1];
    await key(second, "ArrowRight");
    assert.equal(second.querySelector('[aria-live="polite"]').textContent, "2 / 3");
    assert.equal(counter(), "1 / 3");
    await render();

    // Fallback, включая Escape и восстановление прокрутки.
    document.body.style.overflow = "auto";
    await click(button("На весь экран"));
    assert.equal(viewer().dataset.expanded, "true");
    assert.equal(document.body.style.overflow, "hidden");
    button("Далее").focus();
    await key(button("Далее"), "Tab");
    assert.equal(document.activeElement, button("Выйти из полноэкранного режима"));
    await key(document.activeElement, "Tab", {shiftKey: true});
    assert.equal(document.activeElement, button("Далее"));
    await key(document, "Escape");
    assert.equal(viewer().dataset.expanded, "false");
    assert.equal(document.body.style.overflow, "auto");

    // Нативный API и выход через браузерную кнопку/Escape.
    Object.defineProperty(document, "fullscreenElement", {value: null, writable: true, configurable: true});
    viewer().requestFullscreen = async () => {
        document.fullscreenElement = viewer();
        document.dispatchEvent(new window.Event("fullscreenchange"));
    };
    document.exitFullscreen = async () => {
        document.fullscreenElement = null;
        document.dispatchEvent(new window.Event("fullscreenchange"));
    };
    await click(button("На весь экран"));
    assert.equal(document.fullscreenElement, viewer());
    await click(button("Выйти из полноэкранного режима"));
    assert.equal(viewer().dataset.expanded, "false");
    await click(button("На весь экран"));
    await act(async () => document.exitFullscreen());
    assert.equal(viewer().dataset.expanded, "false");
    viewer().requestFullscreen = async () => { throw new Error("Denied"); };
    await click(button("На весь экран"));
    assert.equal(viewer().dataset.expanded, "true");
    await click(button("Выйти из полноэкранного режима"));

    // Ошибка картинки вызывает существующее обновление URL и показывает заглушку.
    const errors = [];
    await render(source, media, (id) => errors.push(id));
    await act(async () => viewer().querySelector("img").dispatchEvent(new window.Event("error")));
    assert.deepEqual(errors, ["m_first"]);
    assert.equal(viewer().querySelector("img"), null);
    await render(source, {...media, m_first: {...media.m_first, url: "https://example.com/refreshed.png"}});
    assert.match(viewer().querySelector("img").src, /refreshed/);

    // Данные урока меняются: позиция сбрасывается, слайды не превращаются в видео.
    const single = ":::slides\n![Only](asset:m_first)\n:::";
    await key(viewer(), "ArrowRight");
    assert.equal(counter(), "2 / 3");
    await render(single);
    assert.equal(counter(), "1 / 1");
    assert.equal(button("Назад").disabled, true);
    assert.equal(button("Далее").disabled, true);
    await render(single, {m_first: {...media.m_first, kind: "video"}});
    assert.equal(viewer().querySelector("video, img"), null);
    await render(single, {});
    assert.equal(viewer().querySelector("img"), null);
    await render(":::slides\n:::");
    assert.equal(counter(), "0 / 0");
    assert.equal(button("Далее").disabled, true);

    await click(button("На весь экран"));
    await act(async () => root.unmount());
    assert.equal(document.body.style.overflow, "auto");
    console.log("Slides: parsing integration, rendering, navigation, swipe, fullscreen and media recovery passed");
} finally {
    dom.window.close();
    delete globalThis.window;
    delete globalThis.document;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
}
