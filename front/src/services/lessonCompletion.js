/** Фронтенд проверяет только прогресс; окончательное решение остаётся за сервером. */
export function canCompleteLesson(blocks, completedExercises) {
    return (blocks ?? []).every((block) => {
        const id = block.data?.exercise_id;
        return !["test", "code"].includes(block.type) || !id
            || Object.hasOwn(completedExercises ?? {}, id);
    });
}

export function isLessonBrowsingAllowed(value, serverAllowsBrowsing) {
    return String(value ?? "false").trim().toLowerCase() === "true" && serverAllowsBrowsing === true;
}
