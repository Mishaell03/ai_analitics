import {getCustomBlockRenderer} from "@/components/Markdown/customBlockRenderers.js";
import styles from "./markdown.module.css";

/**
 * КАСТОМНЫЙ БЛОК УРОКА
 *
 * Блок вида :::test или :::video. Если у типа есть свой отрисовщик,
 * он получает блок и контекст урока (правильные ответы, подписи),
 * иначе содержимое показывается как есть.
 */
function MarkdownCustomBlock({block, children, answers, labels}) {
    const renderer = getCustomBlockRenderer(block.blockType);

    if (renderer) {
        return renderer(block, {answers, labels});
    }

    return (
        <div className={styles.customBlock} data-type={block.blockType}>
            <span className={styles.customBlockLabel}>
                {block.blockType}
            </span>

            <div className={styles.customBlockBody}>
                {children}
            </div>
        </div>
    );
}

export default MarkdownCustomBlock;
