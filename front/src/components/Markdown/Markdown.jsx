import {useMemo} from "react";
import {markdownService} from "@/services/markdown/MarkdownService.js";
import MarkdownBlocks from "@/components/Markdown/MarkdownBlocks.jsx";
import MarkdownTestBlock from "@/components/Markdown/MarkdownTestBlock.jsx";
import MarkdownCodeExercise from "@/components/Markdown/MarkdownCodeExercise.jsx";
import MarkdownSlides from "@/components/Markdown/MarkdownSlides.jsx";
import {registerCustomBlockRenderer} from "@/components/Markdown/customBlockRenderers.js";
import styles from "./markdown.module.css";

// задание — встроенный тип блока: свой отрисовщик сразу после импорта
registerCustomBlockRenderer("test", (block, context) => (
    <MarkdownTestBlock
        block={block}
        answers={context.answers}
        labels={context.labels}
        onCheck={context.onExerciseCheck}
    />
));
registerCustomBlockRenderer("code", (block, context) => (
    <MarkdownCodeExercise key={`${block.data?.exercise_id}-${block.data?.language}`}
                          block={block} onCheck={context.onExerciseCheck}
                          completed={context.answers?.[block.data?.exercise_id]?.type === "code"}
                          expertSolutionAvailable={context.expertReviewExercises?.includes(block.data?.exercise_id)}
                          onExpertSolution={context.onExpertSolution}/>
));
registerCustomBlockRenderer("slides", (block, context) => (
    <MarkdownSlides key={block.content} slides={block.data?.slides}
                    media={context.media} onMediaError={context.onMediaError}/>
));

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
 *
 * answers — правильные ответы на задания по идентификатору задания.
 * labels — подписи интерфейса (например, «Правильный ответ»).
 */
function Markdown({content, media, answers, labels, onMediaError, onExerciseCheck, onExpertSolution, expertReviewExercises, className}) {
    const blocks = useMemo(() => markdownService.parse(content), [content]);

    if (!blocks.length) {
        return null;
    }

    return (
        <div className={className ? `${styles.markdown} ${className}` : styles.markdown}>
            <MarkdownBlocks
                blocks={blocks}
                media={media}
                answers={answers}
                labels={labels}
                onMediaError={onMediaError}
                onExerciseCheck={onExerciseCheck}
                onExpertSolution={onExpertSolution}
                expertReviewExercises={expertReviewExercises}
            />
        </div>
    );
}

export default Markdown;
