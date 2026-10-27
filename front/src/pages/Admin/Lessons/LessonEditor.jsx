import {useCallback, useEffect, useMemo, useState} from "react";
import {Eye, FileText, Link2, ListChecks, Pencil, Plus, Save, TriangleAlert, X} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {listLessonMedia} from "@/api/media.js";
import {
    deleteExerciseAnswer,
    listExerciseAnswers,
    setExerciseAnswer,
} from "@/api/exercises.js";
import {formatBytes} from "@/services/format.js";
import {LESSON_CONTENT_MAX_SIZE} from "@/services/media.js";
import {
    applyAnswers,
    buildAnswer,
    buildAnswerMap,
    buildReferenceAnswer,
    ensureExerciseIds,
    getReferenceAnswer,
    parseAnswer,
    parseExercises,
    setExerciseId,
    setOptionChecked,
    stripCheckedMarks,
    REFERENCE_ANSWER_ID,
} from "@/services/exercises.js";
import {uploadLessonMarkdown} from "@/services/upload.js";
import Markdown from "@/components/Markdown/Markdown.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import LessonExercisesPanel from "./LessonExercisesPanel.jsx";
import LessonMediaModal from "./LessonMediaModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./lessonEditor.module.css";

const TAB_EDITOR = "editor";
const TAB_PREVIEW = "preview";
const TAB_EXERCISES = "exercises";

/**
 * РЕДАКТОР УРОКА
 *
 * Урок состоит из двух частей: метаданные в БД и Markdown в MinIO.
 * Поэтому сохранение идёт в два шага:
 *
 *     1. создаём урок (или просим новую ссылку на загрузку);
 *     2. отправляем Markdown напрямую в хранилище.
 *
 * Метаданные нового урока задаются в этой же форме, а у уже
 * существующего урока меняется только содержимое: отдельного
 * метода правки метаданных у бэкенда пока нет.
 *
 * Правильные ответы на задания лежат в базе отдельно от текста
 * урока: в файл они не попадают, поэтому в разметке варианты
 * остаются без отметок.
 *
 * Код решения хранится как эталонный ответ урока, а не как ответ
 * задания: это пример идеального решения, он не привязан к
 * идентификатору задания и с кодом ученика автоматически не
 * сравнивается.
 */
function LessonEditor({courseSlug, moduleId, lesson, onClose, onSaved}) {
    const t = useAdminTranslation();

    const isNew = !lesson;
    const lessonId = lesson?.lesson_id ?? null;

    const [title, setTitle] = useState(lesson?.title ?? "");
    const [description, setDescription] = useState(lesson?.description ?? "");
    const [isPublished, setIsPublished] = useState(!!lesson?.is_published);
    const [content, setContent] = useState("");

    const [loading, setLoading] = useState(!isNew);
    const [loadError, setLoadError] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [saving, setSaving] = useState(false);

    const [tab, setTab] = useState(TAB_EDITOR);

    // медиафайлы урока: нужны, чтобы в предпросмотре раскрылись
    // ссылки вида ![Схема](asset:m_0123456789abcdef)
    const [media, setMedia] = useState({});
    const [mediaOpen, setMediaOpen] = useState(false);

    // правильные ответы на задания: сырые строки из базы
    const [savedAnswers, setSavedAnswers] = useState({});

    // эталонный ответ урока: пример идеального решения задачи.
    // Он не принадлежит ни одному заданию и хранится отдельно.
    // Поле необязательное: показываем его, только если админ его добавил.
    const [referenceAnswer, setReferenceAnswer] = useState("");
    const [savedReference, setSavedReference] = useState("");
    const [referenceOpen, setReferenceOpen] = useState(false);

    const fetchMedia = useCallback(async () => {
        if (isNew) {
            return;
        }

        try {
            const data = await listLessonMedia(courseSlug, moduleId, lessonId);

            setMedia(Object.fromEntries(
                (data.media ?? []).map((item) => [item.media_key, item])
            ));
        } catch {
            setMedia({});
        }
    }, [courseSlug, moduleId, lessonId, isNew]);

    // правильные ответы грузятся отдельно от текста урока
    const loadAnswerStrings = useCallback(async () => {
        if (isNew) {
            return {};
        }

        try {
            const data = await listExerciseAnswers(lessonId);
            const answers = data.answers ?? [];

            // эталонный ответ урока хранится в базе отдельной записью
            const reference = getReferenceAnswer(answers);

            setSavedReference(reference.raw);
            setReferenceAnswer(reference.value);
            setReferenceOpen(Boolean(reference.value));

            // ответы заданий: запись эталонного ответа к ним не относится
            const raw = Object.fromEntries(
                answers
                    .filter((item) => item.exercise_id !== REFERENCE_ANSWER_ID)
                    .map((item) => [item.exercise_id, item.answer])
            );

            setSavedAnswers(raw);

            return raw;
        } catch {
            setSavedAnswers({});
            setSavedReference("");

            return {};
        }
    }, [lessonId, isNew]);

    // загружаем текущий Markdown урока, чтобы продолжить правку
    const fetchContent = useCallback(async () => {
        if (isNew) {
            return;
        }

        setLoading(true);
        setLoadError(false);

        try {
            // ответы нужны раньше текста: отметки правильных вариантов
            // восстанавливаются в разметке
            const raw = await loadAnswerStrings();

            const {data} = await api.get(
                API_ROUTES.ADMIN_LESSON_CONTENT(courseSlug, moduleId, lessonId)
            );

            setContent(ensureExerciseIds(applyAnswers(data.content ?? "", buildAnswerMap(raw))));
        } catch (requestError) {
            // урока без файла — обычный случай: открываем пустой редактор
            if (requestError.response?.status === 404) {
                setContent("");
            } else {
                setLoadError(true);
            }
        } finally {
            setLoading(false);
        }
    }, [courseSlug, moduleId, lessonId, isNew, loadAnswerStrings]);

    useEffect(() => {
        fetchContent();
    }, [fetchContent]);

    useEffect(() => {
        fetchMedia();
    }, [fetchMedia]);

    const size = useMemo(() => new Blob([content]).size, [content]);

    const exercises = useMemo(() => parseExercises(content), [content]);

    // ответы в том виде, в каком их увидит читатель урока
    const answerMap = useMemo(() => {
        const map = {};

        for (const exercise of exercises) {
            if (!exercise.exercise_id) {
                continue;
            }

            const answer = buildAnswer(exercise);

            if (answer) {
                map[exercise.exercise_id] = parseAnswer(answer);
            }
        }

        return map;
    }, [exercises]);

    const handleToggleOption = useCallback((exerciseIndex, optionIndex, checked) => {
        setContent((current) => setOptionChecked(current, exerciseIndex, optionIndex, checked));
    }, []);

    const handleChangeId = useCallback((exerciseIndex, value) => {
        setContent((current) => setExerciseId(current, exerciseIndex, value));
    }, []);

    const handleChangeReferenceAnswer = useCallback((value) => {
        setReferenceAnswer(value);
    }, []);

    // новым заданиям идентификатор выдаёт фронтенд: открывая вкладку,
    // сразу проставляем хеш всем блокам без `id:`
    const handleOpenExercises = useCallback(() => {
        setTab(TAB_EXERCISES);
        setContent((current) => ensureExerciseIds(current));
    }, []);

    const handleAddReference = useCallback(() => {
        setReferenceOpen(true);
    }, []);

    const handleRemoveReference = useCallback(() => {
        setReferenceAnswer("");
        setReferenceOpen(false);
    }, []);

    /**
     * Синхронизирует ответы заданий с базой.
     *
     * Новые ответы сохраняются, изменившиеся — обновляются,
     * а те, чьё задание удалили из урока, — удаляются.
     * Эталонный ответ урока сюда не входит: у него своя запись.
     */
    const syncAnswers = useCallback(async (lessonId, currentExercises, previous) => {
        const next = {};

        for (const exercise of currentExercises) {
            if (!exercise.exercise_id || exercise.exercise_id === REFERENCE_ANSWER_ID) {
                continue;
            }

            const answer = buildAnswer(exercise);

            if (answer) {
                next[exercise.exercise_id] = answer;
            }
        }

        for (const exerciseId of Object.keys(previous)) {
            if (exerciseId in next || exerciseId === REFERENCE_ANSWER_ID) {
                continue;
            }

            try {
                await deleteExerciseAnswer(lessonId, exerciseId);
            } catch {
                // ответа уже нет — ничего страшного
            }
        }

        for (const [exerciseId, answer] of Object.entries(next)) {
            if (previous[exerciseId] === answer) {
                continue;
            }

            await setExerciseAnswer(lessonId, exerciseId, answer);
        }

        return next;
    }, []);

    /**
     * Сохраняет эталонный ответ урока.
     *
     * Ответ лежит в базе под ключом урока, а не под идентификатором
     * задания: пример решения не зависит от разметки заданий.
     * Код уходит в базу как есть — идентификатор в него не попадает.
     */
    const syncReferenceAnswer = useCallback(async (lessonId, code, previous) => {
        const answer = buildReferenceAnswer(code);

        if (answer === (previous || null)) {
            return;
        }

        if (!answer) {
            if (previous) {
                try {
                    await deleteExerciseAnswer(lessonId, REFERENCE_ANSWER_ID);
                } catch {
                    // ответа уже нет — ничего страшного
                }
            }

            return;
        }

        await setExerciseAnswer(lessonId, REFERENCE_ANSWER_ID, answer);
    }, []);

    const handleSave = async () => {
        if (saving) return;

        const cleanTitle = title.trim();

        if (!cleanTitle || cleanTitle.length > 255) {
            setSaveError("title");
            return;
        }

        setSaving(true);
        setSaveError(null);

        // перед сохранением гарантируем, что у каждого задания есть id:
        // без него ответ не привяжется к заданию в базе
        const preparedContent = ensureExerciseIds(content);

        if (preparedContent !== content) {
            setContent(preparedContent);
        }

        try {
            if (isNew) {
                // 1. создаём урок и получаем ссылку на загрузку
                const {data} = await api.post(
                    API_ROUTES.ADMIN_COURSE_LESSONS(courseSlug, moduleId),
                    {
                        title: cleanTitle,
                        description: description.trim() || null,
                        is_active: isPublished,
                    }
                );

                // 2. отправляем Markdown в хранилище без отметок ответов
                await uploadLessonMarkdown(data.upload, stripCheckedMarks(preparedContent));

                // 3. правильные ответы заданий и эталонный ответ урока
                await syncAnswers(data.lesson_id, parseExercises(preparedContent), {});
                await syncReferenceAnswer(data.lesson_id, referenceAnswer, "");

                onSaved(data);
                return;
            }

            // урок уже существует: сначала метаданные, потом содержимое
            const {data: updated} = await api.patch(
                API_ROUTES.ADMIN_LESSON(courseSlug, moduleId, lesson.lesson_id),
                {
                    title: cleanTitle,
                    description: description.trim() || null,
                    is_active: isPublished,
                }
            );

            const {data: upload} = await api.post(
                API_ROUTES.ADMIN_LESSON_UPLOAD_URL(courseSlug, moduleId, lesson.lesson_id)
            );

            // отметки правильных вариантов в файл урока не попадают
            await uploadLessonMarkdown(upload, stripCheckedMarks(preparedContent));

            await syncAnswers(
                lesson.lesson_id,
                parseExercises(preparedContent),
                savedAnswers
            );

            await syncReferenceAnswer(lesson.lesson_id, referenceAnswer, savedReference);

            onSaved({...updated, has_content: true});
        } catch (saveError) {
            // ошибка API (метаданные) и ошибка хранилища — разные ситуации:
            // у axios-ошибки есть response, у запроса в MinIO — нет
            setSaveError(saveError?.response ? "request" : "upload");
        } finally {
            setSaving(false);
        }
    };

    const renderState = () => (
        <div className={styles.state}>
            <span className={styles.stateIcon} data-tone={loadError ? "error" : "muted"}>
                {loadError ? <TriangleAlert/> : <FileText/>}
            </span>

            {loadError ? (
                <>
                    <h3>{t("adminLessonEditorErrorTitle")}</h3>
                    <p>{t("adminLessonEditorErrorDescription")}</p>

                    <button
                        type="button"
                        className={styles.retryButton}
                        onClick={fetchContent}
                    >
                        {t("adminLessonEditorErrorRetry")}
                    </button>
                </>
            ) : (
                <p>{t("adminLessonEditorLoading")}</p>
            )}
        </div>
    );

    return (
        <AdminModal
            onClose={onClose}
            ariaLabel={t("adminLessonEditorTitle")}
            closeLabel={t("adminLessonEditorClose")}
            closeOnEscape={!mediaOpen}
            overlayChildren={mediaOpen ? (
                <LessonMediaModal
                    courseSlug={courseSlug}
                    moduleId={moduleId}
                    lesson={lesson}
                    onClose={() => setMediaOpen(false)}
                    onChanged={fetchMedia}
                />
            ) : null}
        >
            <header className={styles.header}>
                <span className={styles.headerIcon}>
                    <Pencil/>
                </span>

                <div className={styles.headerContent}>
                    <h2>
                        {isNew
                            ? t("adminLessonEditorNewTitle")
                            : lesson.title}
                    </h2>

                    <p>{t("adminLessonEditorSubtitle")}</p>
                </div>
            </header>

            {loading || loadError
                ? renderState()
                : (
                    <div className={styles.body}>

                        {/* ---------- metadata ---------- */}

                        <section className={styles.section}>
                            <label className={styles.field}>
                                <span>{t("adminLessonEditorTitleField")}</span>
                                <input
                                    required
                                    maxLength={255}
                                    value={title}
                                    onChange={(event) => setTitle(event.target.value)}
                                    placeholder={t("adminLessonEditorTitlePlaceholder")}
                                />
                            </label>

                            <label className={styles.field}>
                                <span>{t("adminLessonEditorDescriptionField")}</span>
                                <textarea
                                    maxLength={5000}
                                    value={description}
                                    onChange={(event) => setDescription(event.target.value)}
                                    rows={3}
                                />
                                <small className={styles.descriptionHint}>{t("descriptionFormatHint")}</small>
                            </label>

                            <label className={styles.checkboxField}>
                                <input
                                    type="checkbox"
                                    checked={isPublished}
                                    onChange={(event) => setIsPublished(event.target.checked)}
                                />
                                <span>{t("adminLessonEditorPublished")}</span>
                            </label>
                        </section>

                        {/* ---------- editor ---------- */}

                        <section className={styles.section}>
                            <div className={styles.tabs}>
                                <button
                                    type="button"
                                    className={styles.tab}
                                    data-active={tab === TAB_EDITOR}
                                    onClick={() => setTab(TAB_EDITOR)}
                                >
                                    <Pencil/>
                                    <span>{t("adminLessonEditorTabEdit")}</span>
                                </button>

                                <button
                                    type="button"
                                    className={styles.tab}
                                    data-active={tab === TAB_PREVIEW}
                                    onClick={() => setTab(TAB_PREVIEW)}
                                >
                                    <Eye/>
                                    <span>{t("adminLessonEditorTabPreview")}</span>
                                </button>

                                <button
                                    type="button"
                                    className={styles.tab}
                                    data-active={tab === TAB_EXERCISES}
                                    onClick={handleOpenExercises}
                                >
                                    <ListChecks/>
                                    <span>{t("adminLessonExercisesTitle")}</span>
                                </button>

                                {!isNew && (
                                    <button
                                        type="button"
                                        className={styles.tab}
                                        onClick={() => setMediaOpen(true)}
                                    >
                                        <Link2/>
                                        <span>{t("mediaTitle")}</span>
                                    </button>
                                )}

                                <span className={styles.size}>
                                    {t("adminLessonEditorSize", {
                                        size: formatBytes(size),
                                        limit: formatBytes(LESSON_CONTENT_MAX_SIZE),
                                    })}
                                </span>
                            </div>

                            {tab === TAB_EDITOR && (
                                <textarea
                                    className={styles.editor}
                                    value={content}
                                    onChange={(event) => setContent(event.target.value)}
                                    onBlur={() => setContent((current) => ensureExerciseIds(current))}
                                    spellCheck={false}
                                    placeholder={t("adminLessonEditorPlaceholder")}
                                />
                            )}

                            {tab === TAB_PREVIEW && (
                                <div className={styles.preview}>
                                    {content
                                        ? (
                                            <Markdown
                                                content={content}
                                                media={media}
                                                answers={answerMap}
                                                labels={{
                                                    answer: t("adminLessonAnswerLabel"),
                                                    image: t("adminLessonImageLabel"),
                                                }}
                                            />
                                        )
                                        : (
                                            <p className={styles.empty}>
                                                {t("adminLessonEditorEmpty")}
                                            </p>
                                        )}
                                </div>
                            )}

                            {tab === TAB_EXERCISES && (
                                <div className={styles.exercises}>
                                    {referenceOpen ? (
                                        <>
                                            <div className={styles.referenceHeader}>
                                                <label className={styles.field}>
                                                    <span>{t("adminLessonReferenceTitle")}</span>
                                                    <textarea
                                                        className={styles.reference}
                                                        value={referenceAnswer}
                                                        onChange={(event) => handleChangeReferenceAnswer(
                                                            event.target.value
                                                        )}
                                                        rows={6}
                                                        spellCheck={false}
                                                        placeholder={t("adminLessonReferencePlaceholder")}
                                                    />
                                                </label>

                                                <button
                                                    type="button"
                                                    className={styles.referenceRemove}
                                                    onClick={handleRemoveReference}
                                                    title={t("adminLessonReferenceRemove")}
                                                >
                                                    <X/>
                                                </button>
                                            </div>

                                            <p className={styles.hint}>
                                                {t("adminLessonReferenceHint")}
                                            </p>
                                        </>
                                    ) : (
                                        <div className={styles.referenceAdd}>
                                            <button
                                                type="button"
                                                className={styles.addReferenceButton}
                                                onClick={handleAddReference}
                                            >
                                                <Plus/>
                                                <span>{t("adminLessonReferenceAdd")}</span>
                                            </button>

                                            <p className={styles.hint}>
                                                {t("adminLessonReferenceAddHint")}
                                            </p>
                                        </div>
                                    )}

                                    <LessonExercisesPanel
                                        exercises={exercises}
                                        onToggleOption={handleToggleOption}
                                        onChangeId={handleChangeId}
                                    />
                                </div>
                            )}
                        </section>

                        {/* ---------- errors ---------- */}

                        {saveError === "title" && (
                            <p className={styles.error}>
                                <TriangleAlert/>
                                {t("adminLessonEditorTitleError")}
                            </p>
                        )}

                        {saveError === "upload" && (
                            <p className={styles.error}>
                                <TriangleAlert/>
                                {t("adminLessonEditorUploadError")}
                            </p>
                        )}

                        {saveError === "request" && (
                            <p className={styles.error}>
                                <TriangleAlert/>
                                {t("adminLessonEditorSaveError")}
                            </p>
                        )}

                        {/* ---------- actions ---------- */}

                        <div className={styles.actions}>
                            <button
                                type="button"
                                className={styles.cancelButton}
                                onClick={onClose}
                                disabled={saving}
                            >
                                {t("adminLessonEditorCancel")}
                            </button>

                            <button
                                type="button"
                                className={styles.saveButton}
                                onClick={handleSave}
                                disabled={saving}
                            >
                                <Save/>
                                <span>
                                    {saving
                                        ? t("adminLessonEditorSaving")
                                        : t("adminLessonEditorSave")}
                                </span>
                            </button>
                        </div>
                    </div>
                )}
        </AdminModal>
    );
}

export default LessonEditor;
