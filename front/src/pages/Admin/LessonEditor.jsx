import {useCallback, useEffect, useMemo, useState} from "react";
import {Eye, FileText, Pencil, Save, TriangleAlert, X} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {getTranslation} from "@/locales/i18n.js";
import {formatBytes} from "@/services/format.js";
import {uploadLessonMarkdown} from "@/services/upload.js";
import Markdown from "@/components/Markdown/Markdown.jsx";
import modalStyles from "./userModal.module.css";
import styles from "./lessonEditor.module.css";

const language = "ru";

const TAB_EDITOR = "editor";
const TAB_PREVIEW = "preview";

// размер файла, который принимает хранилище по умолчанию
const DEFAULT_MAX_SIZE = 512000;

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
 */
function LessonEditor({courseSlug, moduleId, lesson, onClose, onSaved}) {
    const t = (key, params) => getTranslation(`admin.admin.${key}`, language, params);

    const isNew = !lesson;

    const [title, setTitle] = useState(lesson?.title ?? "");
    const [description, setDescription] = useState(lesson?.description ?? "");
    const [isPublished, setIsPublished] = useState(!!lesson?.is_published);
    const [content, setContent] = useState("");

    const [loading, setLoading] = useState(!isNew);
    const [loadError, setLoadError] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [saving, setSaving] = useState(false);

    const [tab, setTab] = useState(TAB_EDITOR);

    // загружаем текущий Markdown урока, чтобы продолжить правку
    const fetchContent = useCallback(async () => {
        if (isNew) {
            return;
        }

        setLoading(true);
        setLoadError(false);

        try {
            const {data} = await api.get(
                API_ROUTES.ADMIN_LESSON_CONTENT(courseSlug, moduleId, lesson.lesson_id)
            );

            setContent(data.content ?? "");
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
    }, [courseSlug, moduleId, lesson, isNew]);

    useEffect(() => {
        fetchContent();
    }, [fetchContent]);

    // закрытие по Escape и блокировка прокрутки фона
    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === "Escape") {
                onClose();
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "hidden";

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "";
        };
    }, [onClose]);

    const size = useMemo(() => new Blob([content]).size, [content]);

    const handleSave = async () => {
        if (saving) return;

        const cleanTitle = title.trim();

        if (!cleanTitle || cleanTitle.length > 255) {
            setSaveError("title");
            return;
        }

        setSaving(true);
        setSaveError(null);

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

                // 2. отправляем Markdown в хранилище
                await uploadLessonMarkdown(data.upload, content);

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

            await uploadLessonMarkdown(upload, content);

            onSaved({...updated, has_content: true});
        } catch (uploadError) {
            setSaveError(uploadError?.message ? "upload" : "request");
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
        <div className={modalStyles.overlay} onClick={onClose} role="presentation">
            <div
                className={modalStyles.modal}
                onClick={(event) => event.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-label={t("adminLessonEditorTitle")}
            >
                <button
                    type="button"
                    className={modalStyles.close}
                    onClick={onClose}
                    aria-label={t("adminLessonEditorClose")}
                >
                    <X/>
                </button>

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

                                    <span className={styles.size}>
                                        {t("adminLessonEditorSize", {
                                            size: formatBytes(size),
                                            limit: formatBytes(DEFAULT_MAX_SIZE),
                                        })}
                                    </span>
                                </div>

                                {tab === TAB_EDITOR ? (
                                    <textarea
                                        className={styles.editor}
                                        value={content}
                                        onChange={(event) => setContent(event.target.value)}
                                        spellCheck={false}
                                        placeholder={t("adminLessonEditorPlaceholder")}
                                    />
                                ) : (
                                    <div className={styles.preview}>
                                        {content
                                            ? <Markdown content={content}/>
                                            : (
                                                <p className={styles.empty}>
                                                    {t("adminLessonEditorEmpty")}
                                                </p>
                                            )}
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
                                    {t("adminLessonEditorErrorDescription")}
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
            </div>
        </div>
    );
}

export default LessonEditor;
