import assert from "node:assert/strict";
import {test} from "node:test";
import {JSDOM} from "jsdom";
import {lockBodyScroll} from "../src/services/bodyScrollLock.js";

test("nested scroll locks restore the original style in either release order", () => {
    for (const order of [[0, 1], [1, 0]]) {
        const dom = new JSDOM('<body style="overflow: auto !important; color: red"></body>');
        const {body} = dom.window.document;
        const originalPriority = body.style.getPropertyPriority("overflow");
        const release = [lockBodyScroll(body), lockBodyScroll(body)];
        assert.equal(body.style.overflow, "hidden");
        release[order[0]]();
        assert.equal(body.style.overflow, "hidden", "An active window still needs its lock");
        release[order[1]]();
        assert.equal(body.style.overflow, "auto");
        assert.equal(body.style.getPropertyPriority("overflow"), originalPriority);
        assert.equal(body.style.color, "red");
        dom.window.close();
    }
});

test("cleanup is idempotent and does not release a later lock", () => {
    const dom = new JSDOM("<body></body>");
    const {body} = dom.window.document;
    const releaseFirst = lockBodyScroll(body);
    releaseFirst();
    assert.equal(body.style.overflow, "");
    const releaseSecond = lockBodyScroll(body);
    releaseFirst();
    assert.equal(body.style.overflow, "hidden");
    releaseSecond();
    releaseSecond();
    assert.equal(body.style.overflow, "");
    dom.window.close();
});

test("overlapping windows and a fullscreen presentation release all locks", () => {
    const dom = new JSDOM("<body></body>");
    const {body} = dom.window.document;
    const releaseParent = lockBodyScroll(body);
    const releaseChild = lockBodyScroll(body);
    const releaseSlides = lockBodyScroll(body);
    releaseParent();
    releaseSlides();
    assert.equal(body.style.overflow, "hidden");
    const releaseNext = lockBodyScroll(body);
    releaseChild();
    assert.equal(body.style.overflow, "hidden");
    releaseNext();
    assert.equal(body.style.overflow, "");
    dom.window.close();
});
