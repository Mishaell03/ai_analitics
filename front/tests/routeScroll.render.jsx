import assert from "node:assert/strict";
import {act, StrictMode} from "react";
import {createRoot} from "react-dom/client";
import {MemoryRouter, useNavigate} from "react-router-dom";
import {JSDOM} from "jsdom";
import RouteScrollReset from "@/components/Navigation/RouteScrollReset.jsx";

const dom = new JSDOM('<!doctype html><div id="root"></div>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const scrolls = [];
window.scrollTo = (options) => scrolls.push(options);
const root = createRoot(document.getElementById("root"));
export function Navigation() {
    const navigate = useNavigate();
    return <>
        <RouteScrollReset/>
        <button id="page" onClick={() => navigate("/teachers")}>Page</button>
        <button id="query" onClick={() => navigate("/teachers?page=2")}>Query</button>
        <button id="hash" onClick={() => navigate("/teachers?page=2#team")}>Hash</button>
        <button id="replace" onClick={() => navigate("/", {replace: true})}>Replace</button>
    </>;
}

const render = async () => act(async () => root.render(
    <StrictMode><MemoryRouter initialEntries={["/course/platform-demo"]}>
        <Navigation/>
    </MemoryRouter></StrictMode>
));
const click = async (id) => act(async () => document.getElementById(id).click());

try {
    await render();
    assert.equal(scrolls.length, 0, "Initial load must preserve native reload restoration");
    await click("page");
    assert.deepEqual(scrolls, [{top: 0, left: 0, behavior: "instant"}]);
    await render();
    assert.equal(scrolls.length, 1, "Ordinary rerenders must not reset scroll");
    await click("query");
    assert.equal(scrolls.length, 2, "Query-string page navigation must reset scroll");
    await click("hash");
    assert.equal(scrolls.length, 2, "Hash-only navigation must not force the page to the top");
    await click("hash");
    assert.equal(scrolls.length, 2, "Navigation to the same page must preserve scroll");
    await click("replace");
    assert.equal(scrolls.length, 3, "Redirects must also reset scroll");
    assert.ok(scrolls.every(({top, left, behavior}) => top === 0 && left === 0 && behavior === "instant"));
    await act(async () => root.unmount());
    console.log("Route scroll: page transitions reset; initial load, rerenders and hash changes preserve position");
} finally {
    dom.window.close();
    delete globalThis.window;
    delete globalThis.document;
    delete globalThis.IS_REACT_ACT_ENVIRONMENT;
}
