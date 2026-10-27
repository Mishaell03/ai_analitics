import {useMemo} from "react";
import {parseInline} from "@/services/markdown/inline.js";
import {descriptionPreview} from "@/services/descriptionPreview.js";
import MarkdownInline from "./MarkdownInline.jsx";
import styles from "./markdown.module.css";

// Описание — текст с инлайн-разметкой, а не документ из Markdown-блоков.
// Разбор целой строки сохраняет каждый Enter, включая пустые строки.
export default function Description({content, className, preview = false}) {
    const nodes = useMemo(
        () => (preview ? descriptionPreview(content) : parseInline((content ?? "").replace(/\r\n?/g, "\n"))).map((node, index, nodes) => (
            node.type === "break" && nodes[index - 1]?.type === "break"
                ? {...node, compact: true}
                : node
        )),
        [content, preview],
    );

    return (
        <div className={`${styles.descriptionText} ${className ?? ""}`}>
            <MarkdownInline nodes={nodes}/>
        </div>
    );
}
