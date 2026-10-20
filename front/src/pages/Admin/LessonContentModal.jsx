import {useCallback, useEffect, useState} from "react";
import {FileText, Link2, Pencil, TriangleAlert, X} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {getTranslation} from "@/locales/i18n.js";
import Markdown from "@/components/Markdown/Markdown.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import modalStyles from "./userModal.module.css";
import styles from "./lessonContent.module.css";

const language = "ru";

/**
 * Содержимое урока в Markdown.
 *
 * Содержимое приходит из хранилища уже очищенным на сервере,
 * а разметку собирает сервис markdown: произвольный HTML или
 * скрипт из урока показать нельзя.
 */
function LessonContentModal({courseSlug, moduleId, lesson, onClose, onEdit}) {
    const t = (key, params) => getTranslation(`admin.admin.${key}`, language, params);

    const [content, setContent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const fetchContent = useCallback(async () => {
        setError(false);
        setLoading(true);

        try {
            const {data} = await api.get(
                API_ROUTES.ADMIN_LESSON_CONTENT(courseSlug, moduleId, lesson.lesson_id)
            );

            setContent(data);
        } catch (requestError) {
            // урока без файла — обычный случай: показываем пустой урок
            if (requestError.response?.status === 404) {
                setContent({content: "", custom_blocks: [], assets: []});
            } else {
                setError(true);
            }
        } finally {
            setLoading(false);
        }
    }, [courseSlug, moduleId, lesson.lesson_id]);

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

    const renderSkeleton = () => (
        <div className={styles.skeletonBody}>
            <span className={styles.skeletonLine} data-width="40%"/>
            <span className={styles.skeletonLine} data-width="90%"/>
            <span className={styles.skeletonLine} data-width="80%"/>
            <span className={styles.skeletonLine} data-width="60%"/>
        </div>
    );

    const renderError = () => (
        <div className={styles.state}>
            <span className={styles.stateIcon}>
                <TriangleAlert/>
            </span>

            <h3>{t("lessonContentErrorTitle")}</h3>
            <p>{t("lessonContentErrorDescription")}</p>

            <button type="button" className={styles.retryButton} onClick={fetchContent}>
                {t("lessonContentErrorRetry")}
            </button>
        </div>
    );

    const renderContent = () => {
        const customBlocks = content.custom_blocks ?? [];
        const assets = content.assets ?? [];

        return (
            <div className={styles.body}>

                {/* ---------- header ---------- */}

                <header className={styles.head}>
                    <span className={styles.headIcon}>
                        <FileText/>
                    </span>

                    <div className={styles.headContent}>
                        <h2>{lesson.title}</h2>

                        {lesson.description && (
                            <p>{lesson.description}</p>
                        )}

                        <div className={styles.headTags}>
                            <Badge tone="muted">
                                {t("adminLessonsColumnPosition")}: {lesson.position}
                            </Badge>

                            <Badge tone={lesson.is_published ? "focus" : "muted"}>
                                {lesson.is_published
                                    ? t("adminLessonsPublished")
                                    : t("adminLessonsDraft")}
                            </Badge>

                            {onEdit && (
                                <button
                                    type="button"
                                    className={styles.editButton}
                                    onClick={onEdit}
                                >
                                    <Pencil/>
                                    <span>{t("lessonContentEdit")}</span>
                                </button>
                            )}
                        </div>
                    </div>
                </header>

                {/* ---------- markdown ---------- */}

                <section className={styles.content}>
                    {content.content
                        ? <Markdown content={content.content}/>
                        : <p className={styles.empty}>{t("lessonContentEmpty")}</p>}
                </section>

                {/* ---------- custom blocks ---------- */}

                <section className={styles.section}>
                    <h3>{t("lessonContentBlocksTitle")}</h3>

                    {!customBlocks.length && (
                        <p className={styles.empty}>{t("lessonContentBlocksEmpty")}</p>
                    )}

                    {customBlocks.length > 0 && (
                        <div className={styles.blocks}>
                            {customBlocks.map((block, index) => (
                                <div className={styles.block} key={`${block.type}-${index}`}>
                                    <Badge tone="accent">{block.type}</Badge>

                                    <span>{block.content}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* ---------- assets ---------- */}

                <section className={styles.section}>
                    <h3>
                        <Link2/>
                        {t("lessonContentAssetsTitle")}
                    </h3>

                    {!assets.length && (
                        <p className={styles.empty}>{t("lessonContentAssetsEmpty")}</p>
                    )}

                    {assets.length > 0 && (
                        <div className={styles.blocks}>
                            {assets.map((asset) => (
                                <div className={styles.block} key={asset.asset_id}>
                                    <Badge tone="muted">{asset.kind}</Badge>

                                    <span>{asset.asset_id}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>
        );
    };

    return (
        <div className={modalStyles.overlay} onClick={onClose} role="presentation">
            <div
                className={modalStyles.modal}
                onClick={(event) => event.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-label={t("lessonContentTitle")}
            >
                <button
                    type="button"
                    className={modalStyles.close}
                    onClick={onClose}
                    aria-label={t("lessonContentClose")}
                >
                    <X/>
                </button>

                {loading && renderSkeleton()}
                {!loading && error && renderError()}
                {!loading && !error && content && renderContent()}
            </div>
        </div>
    );
}

export default LessonContentModal;
