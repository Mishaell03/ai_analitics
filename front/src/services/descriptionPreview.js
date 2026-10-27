import {parseInline} from "./markdown/inline.js";

export function descriptionPreview(content, maxLength = 250) {
    const text = (content ?? "").replace(/\r\n?/g, "\n").trim();
    const paragraph = text.split(/\n[\t ]*\n/, 1)[0];
    let remaining = maxLength;
    let truncated = paragraph.length < text.length;

    function shorten(nodes) {
        return nodes.flatMap((node) => {
            if (node.children) {
                const children = shorten(node.children);
                return children.length ? [{...node, children}] : [];
            }
            const value = node.type === "break" ? " " : (node.value ?? node.alt ?? "");
            const characters = Array.from(value);
            const visible = characters.slice(0, remaining).join("");
            if (characters.length > remaining) truncated = true;
            remaining = Math.max(0, remaining - characters.length);
            if (!visible) return [];
            return [{...node, type: node.type === "break" ? "text" : node.type, value: visible}];
        });
    }

    const nodes = shorten(parseInline(paragraph));
    if (truncated) nodes.push({type: "text", value: "…"});
    return nodes;
}
