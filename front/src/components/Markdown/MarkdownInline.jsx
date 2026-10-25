import {isMediaUrl} from "@/services/markdown/sanitize.js";
import {parseAssetReference} from "@/services/media.js";
import styles from "./markdown.module.css";

/**
 * ИНЛАЙН-РАЗМЕТКА
 *
 * Показывает узлы, которые разобрал сервис: текст, выделение,
 * курсив, зачёркивание, инлайн-код, ссылки и картинки.
 *
 * media — файлы урока по идентификатору. Ссылка вида
 * ![Схема](asset:m_0123456789abcdef) раскрывается в картинку или
 * видео по временной ссылке из этого списка.
 */
function MarkdownInline({nodes, media, labels, onMediaError}) {
    if (!nodes?.length) {
        return null;
    }

    return (
        <>
            {nodes.map((node, index) => renderNode(node, index, media, labels, onMediaError))}
        </>
    );
}

function renderNode(node, index, media, labels, onMediaError) {
    switch (node.type) {
        case "break":
            return node.compact
                ? <span className={styles.descriptionSpacer} aria-hidden="true" key={index}/>
                : <br key={index}/>;

        case "strong":
            return (
                <strong key={index}>
                    <MarkdownInline
                        nodes={node.children}
                        media={media}
                        labels={labels}
                        onMediaError={onMediaError}
                    />
                </strong>
            );

        case "emphasis":
            return (
                <em key={index}>
                    <MarkdownInline
                        nodes={node.children}
                        media={media}
                        labels={labels}
                        onMediaError={onMediaError}
                    />
                </em>
            );

        case "strikethrough":
            return (
                <s key={index}>
                    <MarkdownInline
                        nodes={node.children}
                        media={media}
                        labels={labels}
                        onMediaError={onMediaError}
                    />
                </s>
            );

        case "code":
            return (
                <code className={styles.inlineCode} key={index}>
                    {node.value}
                </code>
            );

        case "link":
            return renderLink(node, index, media, labels, onMediaError);

        case "image":
            return renderImage(node, index, media, labels, onMediaError);

        default:
            return <span key={index}>{node.value}</span>;
    }
}

/**
 * Файл урока по идентификатору из ссылки.
 */
function findMedia(source, media) {
    const key = parseAssetReference(source);

    if (!key || !media) {
        return null;
    }

    return media[key] ?? null;
}

function renderLink(node, index, media, labels, onMediaError) {
    const file = findMedia(node.href, media);

    // видео показываем плеером: обычная ссылка на файл неудобна
    if (file?.kind === "video") {
        return renderVideo(file, index, onMediaError);
    }

    if (file) {
        return renderImage(
            {src: node.href, alt: file.original_name},
            index,
            media,
            labels,
            onMediaError
        );
    }

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
            <MarkdownInline
                nodes={node.children}
                media={media}
                labels={labels}
                onMediaError={onMediaError}
            />
        </a>
    );
}

function renderImage(node, index, media, labels, onMediaError) {
    const file = findMedia(node.src, media);

    if (file) {
        if (file.kind === "video") {
            return renderVideo(file, index, onMediaError);
        }

        if (file.url) {
            return (
                <img
                    className={styles.image}
                    src={file.url}
                    alt={node.alt || file.original_name || ""}
                    title={node.title || undefined}
                    onError={() => onMediaError?.(file.media_key)}
                    key={index}
                />
            );
        }

        return (
            <span className={styles.imagePlaceholder} key={index}>
                {node.alt || file.media_key}
            </span>
        );
    }

    // без готовой ссылки картинку показать нечем:
    // файлы урока отдаются хранилищем по короткому адресу
    if (!node.src || !isMediaUrl(node.src)) {
        return (
            <span className={styles.imagePlaceholder} key={index}>
                {node.alt || node.src || labels?.image || ""}
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

function renderVideo(file, index, onMediaError) {
    if (!file.url) {
        return (
            <span className={styles.imagePlaceholder} key={index}>
                {file.original_name || file.media_key}
            </span>
        );
    }

    return (
        <video
            className={styles.video}
            src={file.url}
            controls
            preload="metadata"
            onError={() => onMediaError?.(file.media_key)}
            key={index}
        >
            {file.original_name || file.media_key}
        </video>
    );
}

export default MarkdownInline;
