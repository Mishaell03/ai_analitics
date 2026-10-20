import {isMediaUrl} from "@/services/markdown/sanitize.js";
import styles from "./markdown.module.css";

/**
 * ИНЛАЙН-РАЗМЕТКА
 *
 * Показывает узлы, которые разобрал сервис: текст, выделение,
 * курсив, зачёркивание, инлайн-код, ссылки и картинки.
 */
function MarkdownInline({nodes}) {
    if (!nodes?.length) {
        return null;
    }

    return (
        <>
            {nodes.map((node, index) => renderNode(node, index))}
        </>
    );
}

function renderNode(node, index) {
    switch (node.type) {
        case "strong":
            return (
                <strong key={index}>
                    <MarkdownInline nodes={node.children}/>
                </strong>
            );

        case "emphasis":
            return (
                <em key={index}>
                    <MarkdownInline nodes={node.children}/>
                </em>
            );

        case "strikethrough":
            return (
                <s key={index}>
                    <MarkdownInline nodes={node.children}/>
                </s>
            );

        case "code":
            return (
                <code className={styles.inlineCode} key={index}>
                    {node.value}
                </code>
            );

        case "link":
            return renderLink(node, index);

        case "image":
            return renderImage(node, index);

        default:
            return <span key={index}>{node.value}</span>;
    }
}

function renderLink(node, index) {
    const isExternal = /^https?:\/\//i.test(node.href);

    return (
        <a
            className={styles.link}
            href={node.href}
            title={node.title || undefined}
            target={isExternal ? "_blank" : undefined}
            rel={isExternal ? "noreferrer noopener" : undefined}
            key={index}
        >
            <MarkdownInline nodes={node.children}/>
        </a>
    );
}

function renderImage(node, index) {
    // без готовой ссылки картинку показать нечем:
    // файлы урока отдаются хранилищем по короткому адресу
    if (!node.src || !isMediaUrl(node.src)) {
        return (
            <span className={styles.imagePlaceholder} key={index}>
                {node.alt || node.src || "изображение"}
            </span>
        );
    }

    return (
        <img
            className={styles.image}
            src={node.src}
            alt={node.alt || ""}
            title={node.title || undefined}
            key={index}
        />
    );
}

export default MarkdownInline;
