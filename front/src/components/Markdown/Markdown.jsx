import {useMemo} from "react";
import {markdownService} from "@/services/markdown/MarkdownService.js";
import MarkdownBlocks from "@/components/Markdown/MarkdownBlocks.jsx";
import styles from "./markdown.module.css";

/**
 * Показывает Markdown урока.
 *
 * Компонент ничего не разбирает: дерево блоков готовит сервис
 * markdownService, здесь только отрисовка. Содержимое урока
 * выводится как текст и React-элементы, поэтому HTML и скрипты
 * из Markdown выполниться не могут.
 *
 * media — файлы урока по идентификатору:
 *
 *     {m_0123456789abcdef: {media_key, kind, url, ...}}
 *
 * По нему раскрываются ссылки вида ![Схема](asset:m_0123456789abcdef):
 * в Markdown попадает только идентификатор, а сам файл отдаётся
 * хранилищем по временной ссылке.
 */
function Markdown({content, media, onMediaError, className}) {
    const blocks = useMemo(() => markdownService.parse(content), [content]);

    if (!blocks.length) {
        return null;
    }

    return (
        <div className={className ? `${styles.markdown} ${className}` : styles.markdown}>
            <MarkdownBlocks blocks={blocks} media={media} onMediaError={onMediaError}/>
        </div>
    );
}

export default Markdown;
