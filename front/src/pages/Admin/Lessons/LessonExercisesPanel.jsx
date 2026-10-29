import {useCallback, useId} from "react";
import {ListChecks, TriangleAlert} from "lucide-react";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./lessonExercises.module.css";

/**
 * ЗАДАНИЯ УРОКА
 *
 * Панель показывает задания, найденные в Markdown, и позволяет
 * автору отметить правильные варианты. Отметка попадает в текст
 * редактора как `- [x]` или `- (х)`, но в файл она не записывается: в базу
 * отправляется отдельный ответ.
 *
 * Задания без вариантов — это задачи на код: их эталонный ответ
 * один на урок и вводится над списком заданий. Поэтому ответы
 * панели привязаны к идентификатору задания: по нему отмечаются
 * варианты, а без идентификатора ответ задания не сохранится.
 */
function LessonExercisesPanel({
    exercises,
    onToggleOption,
    onChangeId,
}) {
    const t = useAdminTranslation();
    const groupId = useId();

    const handleIdChange = useCallback((index, event) => {
        onChangeId(index, event.target.value);
    }, [onChangeId]);

    if (!exercises.length) {
        return (
            <div className={styles.empty}>
                <ListChecks/>
                <span>{t("adminLessonExercisesEmpty")}</span>
            </div>
        );
    }

    return (
        <div className={styles.list}>
            {exercises.map((exercise, index) => {
                const hasOptions = exercise.options.length > 0;

                return (
                    <article className={styles.item} key={`${exercise.start}-${index}`}>
                        <header className={styles.itemHeader}>
                            <span className={styles.itemNumber}>{index + 1}</span>

                            <label className={styles.idField}>
                                <span>{t("adminLessonExercisesId")}</span>
                                <input
                                    value={exercise.exercise_id}
                                    onChange={(event) => handleIdChange(index, event)}
                                    placeholder={t("adminLessonExercisesIdPlaceholder")}
                                    spellCheck={false}
                                />
                            </label>
                        </header>

                        {exercise.question && (
                            <p className={styles.question}>{exercise.question}</p>
                        )}

                        {hasOptions && !exercise.exercise_id && (
                            <p className={styles.warning}>
                                <TriangleAlert/>
                                {t("adminLessonExercisesNoId")}
                            </p>
                        )}

                        {hasOptions && (
                            <ul className={styles.options}>
                                {exercise.options.map((option, optionIndex) => (
                                    <li className={styles.option} key={`${option.text}-${optionIndex}`}>
                                        <input
                                            type={exercise.singleChoice ? "radio" : "checkbox"}
                                            name={`${groupId}-${index}`}
                                            aria-label={option.text}
                                            checked={option.checked}
                                            onChange={(event) => onToggleOption(
                                                index,
                                                optionIndex,
                                                event.target.checked
                                            )}
                                        />

                                        <span>{option.text}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </article>
                );
            })}
        </div>
    );
}

export default LessonExercisesPanel;
