import {useCallback, useEffect, useState} from "react";
import {BookOpen, CheckCircle2, Eye, FileText, Pencil, Plus, TriangleAlert} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {getTranslation} from "@/locales/i18n.js";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import LessonContentModal from "@/pages/Admin/LessonContentModal.jsx";
import LessonEditor from "@/pages/Admin/LessonEditor.jsx";
import styles from "./adminCourses.module.css";

const language = "ru";

const PER_PAGE = 100;

/**
 * Уроки выбранного модуля.
 *
 * Компонент сам решает, какие уроки показать: странице-родителю
 * достаточно передать курс и модуль. При смене модуля список
 * запрашивается заново, а открытый урок закрывается.
 */
function AdminLessons({courseSlug, module}) {
    const t = useCallback(
        (key, params) => getTranslation(`admin.admin.${key}`, language, params),
        []
    );

    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedLesson, setSelectedLesson] = useState(null);

    // редактор урока: null — закрыт, lesson — правка существующего,
    // {mode: "create"} — создание нового
    const [editor, setEditor] = useState(null);

    const [message, setMessage] = useState(null);

    const moduleId = module?.module_id ?? module?.id ?? null;

    const showMessage = useCallback((type, text) => {
        setMessage({type, text});

        window.setTimeout(() => setMessage(null), 4000);
    }, []);

    const fetchLessons = useCallback(async () => {
        if (!courseSlug || !moduleId) {
            return;
        }

        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_COURSE_LESSONS(courseSlug, moduleId), {
                params: {page: 1, page_size: PER_PAGE},
            });

            setLessons(data.lessons ?? []);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [courseSlug, moduleId]);

    useEffect(() => {
        fetchLessons();
    }, [fetchLessons]);

    const handleClose = useCallback(() => {
        setSelectedLesson(null);
    }, []);

    const handleCloseEditor = useCallback(() => {
        setEditor(null);
    }, []);

    // урок сохранён: обновляем список и показываем результат
    const handleSaved = useCallback(async () => {
        const wasCreated = editor?.mode === "create";

        setEditor(null);

        await fetchLessons();

        showMessage(
            "success",
            wasCreated ? t("adminLessonsCreated") : t("adminLessonsSaved")
        );
    }, [editor, fetchLessons, showMessage, t]);

    const renderSkeleton = () => (
        <div className={styles.tableWrap}>
            <table className={styles.table} aria-busy="true">
                <thead>
                <tr>
                    <th>{t("adminLessonsColumnPosition")}</th>
                    <th>{t("adminLessonsColumnTitle")}</th>
                    <th>{t("adminLessonsColumnStatus")}</th>
                    <th>{t("adminLessonsColumnContent")}</th>
                    <th data-align="right">{t("adminLessonsColumnActions")}</th>
                </tr>
                </thead>
                <tbody>
                {Array.from({length: 3}, (_, index) => (
                    <tr className={styles.row} key={index}>
                        <td><span className={styles.skeletonCell} data-width="20%"/></td>
                        <td><span className={styles.skeletonCell} data-width="60%"/></td>
                        <td><span className={styles.skeletonCell} data-width="40%"/></td>
                        <td><span className={styles.skeletonCell} data-width="30%"/></td>
                        <td><span className={styles.skeletonCell} data-width="50%"/></td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );

    return (
        <section className={styles.panel}>
            <div className={styles.panelHeader}>
                <div>
                    <h2>{t("adminLessonsTitle")}</h2>
                    <p>
                        {module
                            ? module.title
                            : t("adminLessonsHint")}
                    </p>
                </div>

                <button
                    type="button"
                    className={styles.primaryButton}
                    onClick={() => setEditor({mode: "create"})}
                    disabled={!module}
                >
                    <Plus/>
                    <span>{t("adminLessonsCreate")}</span>
                </button>
            </div>

            {message && (
                <div className={styles.toast} data-tone={message.type}>
                    {message.type === "success" ? <CheckCircle2/> : <TriangleAlert/>}
                    <span>{message.text}</span>
                </div>
            )}

            {!module && (
                <EmptyState
                    icon={BookOpen}
                    title={t("adminLessonsSelectModuleTitle")}
                    description={t("adminLessonsSelectModuleDescription")}
                />
            )}

            {module && loading && renderSkeleton()}

            {module && !loading && error && (
                <EmptyState
                    icon={TriangleAlert}
                    title={t("errorTitle")}
                    description={t("errorDescription")}
                    action={
                        <button
                            type="button"
                            className={styles.retryButton}
                            onClick={fetchLessons}
                        >
                            {t("errorRetry")}
                        </button>
                    }
                />
            )}

            {module && !loading && !error && lessons.length === 0 && (
                <EmptyState
                    icon={BookOpen}
                    title={t("adminLessonsEmptyTitle")}
                    description={t("adminLessonsEmptyDescription")}
                />
            )}

            {module && !loading && !error && lessons.length > 0 && (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <thead>
                        <tr>
                            <th>{t("adminLessonsColumnPosition")}</th>
                            <th>{t("adminLessonsColumnTitle")}</th>
                            <th>{t("adminLessonsColumnStatus")}</th>
                            <th>{t("adminLessonsColumnContent")}</th>
                            <th data-align="right">{t("adminLessonsColumnActions")}</th>
                        </tr>
                        </thead>
                        <tbody>
                        {lessons.map((lesson) => (
                            <tr className={styles.row} key={lesson.lesson_id}>
                                <td>
                                    <span className={styles.positionBadge}>
                                        {lesson.position}
                                    </span>
                                </td>

                                <td>
                                    <div className={styles.moduleMeta}>
                                        <strong>{lesson.title}</strong>
                                        <br/>
                                        {lesson.description && (
                                            <span>{lesson.description}</span>
                                        )}
                                    </div>
                                </td>

                                <td>
                                    <Badge tone={lesson.is_published ? "focus" : "muted"}>
                                        {lesson.is_published
                                            ? t("adminLessonsPublished")
                                            : t("adminLessonsDraft")}
                                    </Badge>
                                </td>

                                <td>
                                    <Badge tone={lesson.has_content ? "accent" : "muted"} icon={FileText}>
                                        {lesson.has_content
                                            ? t("adminLessonsContentYes")
                                            : t("adminLessonsContentNo")}
                                    </Badge>
                                </td>

                                <td data-align="right">
                                    <div className={styles.actions}>
                                        <button
                                            type="button"
                                            className={styles.actionButton}
                                            onClick={() => setEditor({mode: "edit", lesson})}
                                            title={t("adminLessonsEdit")}
                                        >
                                            <Pencil/>
                                        </button>

                                        <button
                                            type="button"
                                            className={styles.actionButton}
                                            onClick={() => setSelectedLesson(lesson)}
                                            title={t("adminLessonsOpen")}
                                        >
                                            <Eye/>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            )}

            {selectedLesson && (
                <LessonContentModal
                    key={selectedLesson.lesson_id}
                    courseSlug={courseSlug}
                    moduleId={moduleId}
                    lesson={selectedLesson}
                    onClose={handleClose}
                    onEdit={() => {
                        setSelectedLesson(null);
                        setEditor({mode: "edit", lesson: selectedLesson});
                    }}
                />
            )}

            {editor && (
                <LessonEditor
                    key={editor.mode === "create" ? "create" : editor.lesson.lesson_id}
                    courseSlug={courseSlug}
                    moduleId={moduleId}
                    lesson={editor.mode === "create" ? null : editor.lesson}
                    onClose={handleCloseEditor}
                    onSaved={handleSaved}
                />
            )}
        </section>
    );
}

export default AdminLessons;
