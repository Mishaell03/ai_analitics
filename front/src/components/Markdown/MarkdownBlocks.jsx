import MarkdownCode from "@/components/Markdown/MarkdownCode.jsx";
import MarkdownCustomBlock from "@/components/Markdown/MarkdownCustomBlock.jsx";
import MarkdownInline from "@/components/Markdown/MarkdownInline.jsx";
import MarkdownTable from "@/components/Markdown/MarkdownTable.jsx";
import styles from "./markdown.module.css";

/**
 * БЛОКИ УРОКА
 *
 * Отрисовка дерева блоков, которое подготовил сервис разбора
 * Markdown. Здесь нет логики разбора: только соответствие типа
 * блока элементу интерфейса.
 */
function MarkdownBlocks({blocks = [], media, answers, labels, onMediaError, onExerciseCheck, onExpertSolution, expertReviewExercises}) {
    return (
        <>
            {blocks.map((block, index) => (
                <MarkdownBlock
                    block={block}
                    media={media}
                    answers={answers}
                    labels={labels}
                    onMediaError={onMediaError}
                    onExerciseCheck={onExerciseCheck}
                    onExpertSolution={onExpertSolution}
                    expertReviewExercises={expertReviewExercises}
                    key={index}
                />
            ))}
        </>
    );
}

function MarkdownBlock({block, media, answers, labels, onMediaError, onExerciseCheck, onExpertSolution, expertReviewExercises}) {
    switch (block.type) {
        case "heading": {
            const Heading = `h${Math.min(Math.max(block.level, 1), 6)}`;

            return (
                <Heading className={styles.heading} data-level={block.level}>
                    <MarkdownInline
                        nodes={block.children}
                        media={media}
                        labels={labels}
                        onMediaError={onMediaError}
                    />
                </Heading>
            );
        }

        case "paragraph":
            return (
                <p className={styles.paragraph}>
                    <MarkdownInline
                        nodes={block.children}
                        media={media}
                        labels={labels}
                        onMediaError={onMediaError}
                    />
                </p>
            );

        case "list":
            return renderList(block, media, labels, onMediaError, answers, onExerciseCheck, onExpertSolution, expertReviewExercises);

        case "table":
            return (
                <MarkdownTable
                    header={block.header}
                    rows={block.rows}
                    media={media}
                    labels={labels}
                    onMediaError={onMediaError}
                />
            );

        case "quote":
            return (
                <blockquote className={styles.quote}>
                    <MarkdownBlocks
                        blocks={block.children}
                        media={media}
                        answers={answers}
                        labels={labels}
                        onMediaError={onMediaError}
                        onExerciseCheck={onExerciseCheck}
                        onExpertSolution={onExpertSolution}
                        expertReviewExercises={expertReviewExercises}
                    />
                </blockquote>
            );

        case "code":
            return (
                <MarkdownCode
                    language={block.language}
                    code={block.code}
                    tokens={block.tokens}
                />
            );

        case "divider":
            return <hr className={styles.divider}/>;

        case "custom":
            return (
                <MarkdownCustomBlock
                    block={block}
                    media={media}
                    onMediaError={onMediaError}
                    answers={answers}
                    labels={labels}
                    onExerciseCheck={onExerciseCheck}
                    onExpertSolution={onExpertSolution}
                    expertReviewExercises={expertReviewExercises}
                >
                    <MarkdownBlocks
                        blocks={block.children}
                        media={media}
                        answers={answers}
                        labels={labels}
                        onMediaError={onMediaError}
                        onExerciseCheck={onExerciseCheck}
                        onExpertSolution={onExpertSolution}
                        expertReviewExercises={expertReviewExercises}
                    />
                </MarkdownCustomBlock>
            );

        default:
            return null;
    }
}

function renderList(block, media, labels, onMediaError, answers, onExerciseCheck, onExpertSolution, expertReviewExercises) {
    const ListTag = block.ordered ? "ol" : "ul";
    const start = block.ordered && block.start !== 1 ? {start: block.start} : undefined;

    return (
        <ListTag className={styles.list} data-ordered={block.ordered} {...start}>
            {block.items.map((item, index) => (
                <li className={styles.listItem} key={index}>
                    {item.children.length > 0 && (
                        <MarkdownInline
                            nodes={item.children}
                            media={media}
                            onMediaError={onMediaError}
                        />
                    )}

                    {item.blocks.length > 0 && (
                        <MarkdownBlocks
                            blocks={item.blocks}
                            media={media}
                            labels={labels}
                            onMediaError={onMediaError}
                            answers={answers}
                            onExerciseCheck={onExerciseCheck}
                            onExpertSolution={onExpertSolution}
                            expertReviewExercises={expertReviewExercises}
                        />
                    )}
                </li>
            ))}
        </ListTag>
    );
}

export default MarkdownBlocks;
