import {useCallback, useEffect, useState} from "react";
import {FileText, Link2, Pencil, TriangleAlert} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {listLessonMedia, refreshMediaUrl} from "@/api/media.js";
import Markdown from "@/components/Markdown/Markdown.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import LessonMediaModal from "./LessonMediaModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./lessonContent.module.css";

/**
 * Содержимое урока в Markdown.
 *
 * Содержимое приходит из хранилища уже очищенным на сервере,
 * а разметку собирает сервис markdown: произвольный HTML или
 * скрипт из урока показать нельзя.
 *
 * Ссылки на медиа раскрываются по идентификатору: в Markdown живёт
 * asset:media_key, а картинку и видео отдаёт хранилище по временной
 * ссылке из списка медиафайлов урока.
 */
function LessonContentModal({courseSlug, moduleId, lesson, onClose, onEdit}) {
    const t = useAdminTranslation();

    const [content, setContent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    // медиафайлы урока по идентификатору: для раскрытия ссылок в Markdown
    const [media, setMedia] = useState({});
    const [mediaOpen, setMediaOpen] = useState(false);

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

    const fetchMedia = useCallback(async () => {
        try {
            const data = await listLessonMedia(courseSlug, moduleId, lesson.lesson_id);

            setMedia(Object.fromEntries(
                (data.media ?? []).map((item) => [item.media_key, item])
            ));
        } catch {
            // без списка медиа урок покажется без картинок
            setMedia({});
        }
    }, [courseSlug, moduleId, lesson.lesson_id]);

    // ссылка на файл протухла — берём новую
    const handleMediaError = useCallback(async (mediaKey) => {
        try {
            const data = await refreshMediaUrl(mediaKey);

            setMedia((current) => ({
                ...current,
                [mediaKey]: {...current[mediaKey], url: data.url},
            }));
        } catch {
            // ссылку получить не удалось — останется заглушка
        }
    }, []);

    useEffect(() => {
        fetchContent();
        fetchMedia();
    }, [fetchContent, fetchMedia]);

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

                            <button
                                type="button"
                                className={styles.editButton}
                                onClick={() => setMediaOpen(true)}
                            >
                                <Link2/>
                                <span>{t("mediaTitle")}</span>
                            </button>
                        </div>
                    </div>
                </header>

                {/* ---------- markdown ---------- */}

                <section className={styles.content}>
                    {content.content
                        ? (
                            <Markdown
                                content={content.content}
                                media={media}
                                onMediaError={handleMediaError}
                            />
                        )
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
        <AdminModal
            onClose={onClose}
            ariaLabel={t("lessonContentTitle")}
            closeLabel={t("lessonContentClose")}
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
            {loading && renderSkeleton()}
            {!loading && error && renderError()}
            {!loading && !error && content && renderContent()}
        </AdminModal>
    );
}

export default LessonContentModal;
