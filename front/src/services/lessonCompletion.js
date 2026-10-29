/** Фронтенд проверяет только прогресс; окончательное решение остаётся за сервером. */
export function canCompleteLesson(blocks, completedExercises, expertReviewExercises = []) {
    return (blocks ?? []).every((block) => {
        const id = block.data?.exercise_id;
        return !["test", "code"].includes(block.type) || !id
            || (block.type === "code" && block.data?.practice === true)
            || Object.hasOwn(completedExercises ?? {}, id)
            || (block.type === "code" && expertReviewExercises.includes(id));
    });
}

export function isLessonBrowsingAllowed(value, serverAllowsBrowsing) {
    return String(value ?? "false").trim().toLowerCase() === "true" && serverAllowsBrowsing === true;
}
