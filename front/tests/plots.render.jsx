import assert from "node:assert/strict";
import {renderToStaticMarkup} from "react-dom/server";
import MarkdownPlots from "@/components/Markdown/MarkdownPlots.jsx";

const png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRTkAAAAASUVORK5CYII=";
const html = renderToStaticMarkup(<MarkdownPlots plots={[png]}/>);
assert.ok(html.includes(`src="data:image/png;base64,${png}"`));
assert.ok(html.includes('alt="График 1"'));
assert.equal((renderToStaticMarkup(<MarkdownPlots plots={[png, png, png, png]}/>).match(/<img/g) ?? []).length, 3);
assert.ok(!renderToStaticMarkup(<MarkdownPlots plots={["<svg onload=alert(1)>", "https://evil.test"]}/>).includes("<img"));
console.log("PNG plots render as responsive images; invalid content rejected");
