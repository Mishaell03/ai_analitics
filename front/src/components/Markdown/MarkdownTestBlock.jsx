import {useMemo} from "react";
import {ListChecks} from "lucide-react";
import {parseInline} from "@/services/markdown/MarkdownService.js";
import {ANSWER_TYPE_CHOICE, parseExercises} from "@/services/exercises.js";
import MarkdownInline from "@/components/Markdown/MarkdownInline.jsx";
import styles from "./markdown.module.css";

/**
 * ЗАДАНИЕ УРОКА
 *
 * Задание показано как список вариантов с чекбоксами. В режиме
 * чтения отметка правильного варианта подставляется из базы:
 * в самом Markdown её нет, иначе ответ утечёт в файл урока.
 *
 * У задания без вариантов правильный ответ показывается отдельным
 * полем — это ввод кода или текста.
 */
function MarkdownTestBlock({block, answers = {}, labels = {}}) {
    const exerciseId = block.data?.exercise_id ?? null;

    // варианты и вопрос разбираем из тела блока
    const exercise = useMemo(() => {
        const parsed = parseExercises(`:::test\n${block.data?.body ?? ""}\n:::`);

        return parsed[0] ?? null;
    }, [block.data?.body]);

    const answer = exerciseId ? answers[exerciseId] : null;

    const correctOptions = answer?.type === ANSWER_TYPE_CHOICE ? (answer.correct ?? []) : [];

    return (
        <div className={styles.testBlock}>
            <div className={styles.testHeader}>
                <ListChecks/>
                <span>{exerciseId ?? "—"}</span>
            </div>

            {exercise?.question && (
                <p className={styles.testQuestion}>
                    <MarkdownInline nodes={parseInline(exercise.question)}/>
                </p>
            )}

            {exercise?.options?.length > 0 && (
                <ul className={styles.testOptions}>
                    {exercise.options.map((option, index) => {
                        const isCorrect = correctOptions.includes(option.text);

                        return (
                            <li
                                className={styles.testOption}
                                data-correct={isCorrect}
                                key={`${option.text}-${index}`}
                            >
                                <input
                                    type="checkbox"
                                    checked={isCorrect}
                                    readOnly
                                    disabled
                                />

                                <MarkdownInline nodes={parseInline(option.text)}/>
                            </li>
                        );
                    })}
                </ul>
            )}

            {answer?.type === "text" && answer.value && (
                <div className={styles.testAnswer}>
                    {labels.answer && (
                        <span className={styles.testAnswerLabel}>{labels.answer}</span>
                    )}

                    <code className={styles.testAnswerValue}>{answer.value}</code>
                </div>
            )}
        </div>
    );
}

export default MarkdownTestBlock;
