import {getCustomBlockRenderer} from "@/components/Markdown/customBlockRenderers.js";
import styles from "./markdown.module.css";

/**
 * КАСТОМНЫЙ БЛОК УРОКА
 *
 * Блок вида :::test или :::video. Пока у типа нет своего
 * отрисовщика, содержимое показывается как есть: логика тестов,
 * видео и заданий появится позже.
 */
function MarkdownCustomBlock({block, children}) {
    const renderer = getCustomBlockRenderer(block.blockType);

    if (renderer) {
        return renderer(block);
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
