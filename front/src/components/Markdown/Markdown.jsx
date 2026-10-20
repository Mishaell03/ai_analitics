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
 */
function Markdown({content, className}) {
    const blocks = useMemo(() => markdownService.parse(content), [content]);

    if (!blocks.length) {
        return null;
    }

    return (
        <div className={className ? `${styles.markdown} ${className}` : styles.markdown}>
            <MarkdownBlocks blocks={blocks}/>
        </div>
    );
}

export default Markdown;
