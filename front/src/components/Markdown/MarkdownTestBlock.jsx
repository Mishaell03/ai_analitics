import {useMemo, useState} from "react";
import {ListChecks} from "lucide-react";
import {parseInline} from "@/services/markdown/MarkdownService.js";
import {ANSWER_TYPE_CHOICE, buildAnswer, parseExercises} from "@/services/exercises.js";
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
function MarkdownTestBlock({block, answers = {}, labels = {}, onCheck}) {
    const exerciseId = block.data?.exercise_id ?? null;

    // варианты и вопрос разбираем из тела блока
    const exercise = useMemo(() => {
        const parsed = parseExercises(`:::test\n${block.data?.body ?? ""}\n:::`);

        return parsed[0] ?? null;
    }, [block.data?.body]);

    const answer = exerciseId ? answers[exerciseId] : null;
    const correctOptions = answer?.type === ANSWER_TYPE_CHOICE ? (answer.correct ?? []) : [];
    const [draftOptions, setDraftOptions] = useState([]);
    const [checking, setChecking] = useState(false);
    const [checkError, setCheckError] = useState(false);
    const [incorrect, setIncorrect] = useState(false);
    const completed = correctOptions.length > 0;
    const selectedOptions = completed ? correctOptions : draftOptions;

    const toggleOption = (optionText) => {
        setDraftOptions((selected) => selected.includes(optionText)
            ? selected.filter((item) => item !== optionText)
            : [...selected, optionText]);
        setIncorrect(false);
        setCheckError(false);
    };

    const checkAnswer = async () => {
        const response = buildAnswer({
            ...exercise,
            options: exercise.options.map((option) => ({
                ...option,
                checked: selectedOptions.includes(option.text),
            })),
        });
        if (!response || !exerciseId || !onCheck || checking) return;
        setChecking(true);
        setCheckError(false);
        setIncorrect(false);
        try {
            const isCorrect = await onCheck(exerciseId, response);
            setIncorrect(!isCorrect);
        } catch {
            setCheckError(true);
        } finally {
            setChecking(false);
        }
    };

    return (
        <div className={styles.testBlock} data-completed={completed}>
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
                        const isCorrect = completed && correctOptions.includes(option.text);

                        return (
                            <li
                                className={styles.testOption}
                                data-correct={isCorrect}
                                key={`${option.text}-${index}`}
                            >
                                <input
                                    id={`exercise-${exerciseId}-${index}`}
                                    type="checkbox"
                                    checked={selectedOptions.includes(option.text)}
                                    onChange={() => toggleOption(option.text)}
                                    disabled={completed || checking}
                                />

                                <label htmlFor={`exercise-${exerciseId}-${index}`}>
                                    <MarkdownInline nodes={parseInline(option.text)}/>
                                </label>
                            </li>
                        );
                    })}
                </ul>
            )}

            {exercise?.options?.length > 0 && (
                <div className={styles.testActions}>
                    {completed ? (
                        <p className={styles.testSuccess} role="status">{labels.correct}</p>
                    ) : (
                        <button type="button" className={styles.testCheckButton}
                                onClick={checkAnswer} disabled={!selectedOptions.length || checking || !exerciseId}>
                            {checking ? labels.checking : labels.check}
                        </button>
                    )}
                    {incorrect && <p className={styles.testError} role="alert">{labels.incorrect}</p>}
                    {checkError && <p className={styles.testError} role="alert">{labels.checkError}</p>}
                </div>
            )}

            {(answer?.type === "text" || answer?.type === "code") && answer.value && (
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
