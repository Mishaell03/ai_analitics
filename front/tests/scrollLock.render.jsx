import assert from "node:assert/strict";
import {act, StrictMode} from "react";
import {createRoot} from "react-dom/client";
import {Link, MemoryRouter, Route, Routes} from "react-router-dom";
import {JSDOM} from "jsdom";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import MarkdownSlides from "@/components/Markdown/MarkdownSlides.jsx";

const dom = new JSDOM('<!doctype html><div id="root"></div>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const root = createRoot(document.getElementById("root"));
const close = () => {};

const render = async ({parent = true, child = true, closeOnEscape = true} = {}) => act(async () => root.render(
    <StrictMode><MemoryRouter>
        <Link id="next" to="/next">Next page</Link>
        <Routes>
            <Route path="/" element={parent ? (
                <AdminModal onClose={close} ariaLabel="Parent" closeLabel="Close parent"
                            closeOnEscape={closeOnEscape}
                            overlayChildren={child ? (
                                <AdminModal onClose={close} ariaLabel="Child" closeLabel="Close child">Child</AdminModal>
                            ) : null}>
                    <MarkdownSlides/>
                </AdminModal>
            ) : null}/>
            <Route path="/next" element={<p>Next page</p>}/>
        </Routes>
    </MemoryRouter></StrictMode>
));

try {
    // Вложенные окна монтируются и размонтируются одновременно, в том числе в StrictMode.
    await render();
    assert.equal(document.body.style.overflow, "hidden");
    await render({closeOnEscape: false});
    assert.equal(document.body.style.overflow, "hidden");
    await render({child: false});
    assert.equal(document.body.style.overflow, "hidden");
    await render({parent: false});
    assert.equal(document.body.style.overflow, "");

    // Полноэкранные слайды делят блокировку с обоими окнами.
    await render({child: false});
    await render();
    await act(async () => document.querySelector('button[aria-label="На весь экран"]').click());
    assert.equal(document.querySelector("section").dataset.expanded, "true");
    assert.equal(document.body.style.overflow, "hidden");
    await act(async () => document.querySelector('button[aria-label="Выйти из полноэкранного режима"]').click());
    assert.equal(document.body.style.overflow, "hidden", "The modal still owns a scroll lock");

    // Переход со страницы закрывает сразу все окна и восстанавливает скролл.
    await act(async () => document.querySelector('button[aria-label="На весь экран"]').click());
    await act(async () => document.getElementById("next").click());
    assert.equal(document.querySelector('[role="dialog"]'), null);
    assert.equal(document.body.style.overflow, "");
    await act(async () => root.unmount());
    assert.equal(document.body.style.overflow, "");
    console.log("Scroll locks: nested dialogs, fullscreen slides, StrictMode and route unmount cleanup passed");
} finally {
    dom.window.close();
    delete globalThis.window;
    delete globalThis.document;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
}
