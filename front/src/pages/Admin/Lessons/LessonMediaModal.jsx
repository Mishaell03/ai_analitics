import {useCallback, useEffect, useRef, useState} from "react";
import {
    Check,
    Copy,
    FileImage,
    Film,
    ImageOff,
    Link2,
    RefreshCw,
    Trash2,
    TriangleAlert,
    Upload,
} from "lucide-react";
import {
    deleteLessonMedia,
    listLessonMedia,
    refreshMediaUrl,
    uploadLessonMedia,
} from "@/api/media.js";
import {
    buildAssetMarkdown,
    formatBytes,
    formatDuration,
    getMediaAlt,
    MEDIA_ACCEPT,
    validateMediaFile,
} from "@/services/media.js";
import {getErrorMessage, useFileUpload} from "@/hooks/useFileUpload.js";
import Badge from "@/components/Badge/Badge.jsx";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./lessonMedia.module.css";

/**
 * МЕДИАФАЙЛЫ УРОКА
 *
 * Файлы лежат в приватном хранилище, поэтому список всегда приходит
 * с временными ссылками. Ссылка может протухнуть — тогда она
 * запрашивается заново, а в Markdown попадает только идентификатор:
 *
 *     ![Описание](asset:m_0123456789abcdef)
 */
function LessonMediaModal({courseSlug, moduleId, lesson, onClose, onChanged}) {
    const t = useAdminTranslation();

    const [media, setMedia] = useState([]);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(null);

    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleting, setDeleting] = useState(false);

    const [refreshingKey, setRefreshingKey] = useState(null);
    const [copiedKey, setCopiedKey] = useState(null);
    const [copiedField, setCopiedField] = useState(null);

    const {uploading, progress, error: uploadError, upload, setError} = useFileUpload();

    const inputRef = useRef(null);

    const loadMedia = useCallback(async () => {
        setLoading(true);
        setLoadError(null);

        try {
            const data = await listLessonMedia(courseSlug, moduleId, lesson.lesson_id);

            setMedia(data.media ?? []);
        } catch (requestError) {
            setLoadError(getErrorMessage(requestError, t("mediaLoadError")));
        } finally {
            setLoading(false);
        }
    }, [courseSlug, moduleId, lesson.lesson_id, t]);

    useEffect(() => {
        loadMedia();
    }, [loadMedia]);

    // счётчик "скопировано" сбрасывается сам
    useEffect(() => {
        if (!copiedKey) {
            return;
        }

        const timer = window.setTimeout(() => {
            setCopiedKey(null);
            setCopiedField(null);
        }, 2000);

        return () => window.clearTimeout(timer);
    }, [copiedKey]);

    const handleSelectFile = useCallback(() => {
        setError(null);

        inputRef.current?.click();
    }, [setError]);

    const handleFileChange = useCallback(async (event) => {
        const file = event.target.files?.[0];

        // значение сбрасываем, иначе тот же файл не выберется повторно
        event.target.value = "";

        if (!file) {
            return;
        }

        const invalid = validateMediaFile(file);

        if (invalid) {
            setError(new Error(t(invalid.code, invalid.params)));

            return;
        }

        const result = await upload(
            (selected, options) => uploadLessonMedia(
                courseSlug,
                moduleId,
                lesson.lesson_id,
                selected,
                options
            ),
            file
        );

        if (result) {
            await loadMedia();

            onChanged?.(result);
        }
    }, [courseSlug, moduleId, lesson.lesson_id, upload, loadMedia, onChanged, t, setError]);

    // ссылка протухла — берём новую
    const handleMediaError = useCallback(async (mediaKey) => {
        try {
            const data = await refreshMediaUrl(mediaKey);

            setMedia((current) => current.map((item) => (
                item.media_key === mediaKey ? {...item, url: data.url} : item
            )));
        } catch {
            // ссылку получить не удалось — карточка останется заглушкой
        }
    }, []);

    const handleRefresh = useCallback(async (mediaKey) => {
        setRefreshingKey(mediaKey);

        try {
            const data = await refreshMediaUrl(mediaKey);

            setMedia((current) => current.map((item) => (
                item.media_key === mediaKey ? {...item, url: data.url} : item
            )));
        } catch (requestError) {
            setError(new Error(getErrorMessage(requestError, t("mediaRefreshError"))));
        } finally {
            setRefreshingKey(null);
        }
    }, [t, setError]);

    const handleCopy = useCallback(async (item, field) => {
        const text = field === "key"
            ? item.media_key
            : buildAssetMarkdown(item, getMediaAlt(item));

        try {
            await navigator.clipboard.writeText(text);

            setCopiedKey(item.media_key);
            setCopiedField(field);
        } catch {
            setError(new Error(t("mediaCopyError")));
        }
    }, [t, setError]);

    const handleDelete = useCallback(async () => {
        if (!deleteTarget) {
            return;
        }

        setDeleting(true);

        try {
            await deleteLessonMedia(lesson.lesson_id, deleteTarget.media_key);

            setDeleteTarget(null);

            await loadMedia();

            onChanged?.(null);
        } catch (requestError) {
            setError(new Error(getErrorMessage(requestError, t("mediaDeleteError"))));
            setDeleteTarget(null);
        } finally {
            setDeleting(false);
        }
    }, [deleteTarget, lesson.lesson_id, loadMedia, onChanged, t, setError]);

    const renderPreview = (item) => {
        if (!item.url) {
            return (
                <div className={styles.preview} data-state="empty">
                    <ImageOff/>
                    <span>{t("mediaNoLink")}</span>
                </div>
            );
        }

        if (item.kind === "video") {
            return (
                <div className={styles.preview} data-state="video">
                    <video
                        src={item.url}
                        controls
                        preload="metadata"
                        onError={() => handleMediaError(item.media_key)}
                    >
                        {item.original_name}
                    </video>
                </div>
            );
        }

        return (
            <div className={styles.preview} data-state="image">
                <img
                    src={item.url}
                    alt={item.original_name || item.media_key}
                    onError={() => handleMediaError(item.media_key)}
                />
            </div>
        );
    };

    const renderMeta = (item) => (
        <div className={styles.meta}>
            <Badge tone={item.kind === "video" ? "primary" : "accent"}>
                {item.kind === "video" ? <Film/> : <FileImage/>}
                {item.kind === "video" ? t("mediaKindVideo") : t("mediaKindImage")}
            </Badge>

            {item.width && item.height && (
                <span>{item.width} × {item.height}</span>
            )}

            <span>{formatBytes(item.size_bytes)}</span>

            {item.duration_seconds && (
                <span>{formatDuration(item.duration_seconds)}</span>
            )}
        </div>
    );

    return (
        <AdminModal
            onClose={onClose}
            ariaLabel={t("mediaTitle")}
            closeLabel={t("mediaClose")}
        >
            <header className={styles.header}>
                <span className={styles.headerIcon}>
                    <Link2/>
                </span>

                <div className={styles.headerContent}>
                    <h2>{t("mediaTitle")}</h2>
                    <p>{lesson.title}</p>
                </div>
            </header>

            {/* ---------- toolbar ---------- */}

            <div className={styles.toolbar}>
                <input
                    ref={inputRef}
                    type="file"
                    accept={MEDIA_ACCEPT}
                    className={styles.fileInput}
                    onChange={handleFileChange}
                />

                <button
                    type="button"
                    className={styles.uploadButton}
                    onClick={handleSelectFile}
                    disabled={uploading}
                >
                    <Upload/>
                    <span>
                        {uploading ? t("mediaUploadingShort") : t("mediaUpload")}
                    </span>
                </button>

                <span className={styles.hint}>
                    {t("mediaHint")}
                </span>
            </div>

            {uploading && (
                <div className={styles.progress}>
                    <div className={styles.progressBar}>
                        <span style={{width: `${progress}%`}}/>
                    </div>

                    <span className={styles.progressText}>
                        {t("mediaUploading", {progress})}
                    </span>
                </div>
            )}

            {(uploadError || loadError) && (
                <p className={styles.error}>
                    <TriangleAlert/>
                    {(uploadError || loadError).message}
                </p>
            )}

            {/* ---------- list ---------- */}

            {loading && (
                <div className={styles.skeleton}>
                    <span/>
                    <span/>
                </div>
            )}

            {!loading && !loadError && media.length === 0 && (
                <EmptyState
                    icon={FileImage}
                    title={t("mediaEmptyTitle")}
                    description={t("mediaEmptyDescription")}
                />
            )}

            {!loading && media.length > 0 && (
                <div className={styles.list}>
                    {media.map((item) => (
                        <article className={styles.item} key={item.media_key}>
                            {renderPreview(item)}

                            <div className={styles.itemBody}>
                                {renderMeta(item)}

                                <div className={styles.keyRow}>
                                    <button
                                        type="button"
                                        className={styles.key}
                                        onClick={() => handleCopy(item, "key")}
                                        title={t("mediaCopyKey")}
                                    >
                                        {item.media_key}
                                    </button>

                                    {copiedKey === item.media_key && copiedField === "key" && (
                                        <span className={styles.copied}>
                                            <Check/>
                                            {t("mediaCopied")}
                                        </span>
                                    )}
                                </div>

                                <div className={styles.itemActions}>
                                    <button
                                        type="button"
                                        className={styles.actionButton}
                                        onClick={() => handleCopy(item, "markdown")}
                                    >
                                        <Copy/>
                                        <span>{t("mediaCopyMarkdown")}</span>
                                    </button>

                                    {copiedKey === item.media_key && copiedField === "markdown" && (
                                        <span className={styles.copied}>
                                            <Check/>
                                            {t("mediaCopied")}
                                        </span>
                                    )}

                                    <button
                                        type="button"
                                        className={styles.actionButton}
                                        onClick={() => handleRefresh(item.media_key)}
                                        disabled={refreshingKey === item.media_key}
                                    >
                                        <RefreshCw/>
                                        <span>{t("mediaRefresh")}</span>
                                    </button>

                                    <button
                                        type="button"
                                        className={styles.actionButton}
                                        data-tone="danger"
                                        onClick={() => setDeleteTarget(item)}
                                    >
                                        <Trash2/>
                                        <span>{t("mediaDelete")}</span>
                                    </button>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            )}

            {deleteTarget && (
                <ConfirmModal
                    title={t("mediaDeleteTitle")}
                    description={deleteTarget.original_name || deleteTarget.media_key}
                    confirmText={t("confirmDeleteButton")}
                    busyText={t("confirmDeleteProcess")}
                    cancelText={t("confirmCancelButton")}
                    busy={deleting}
                    onConfirm={handleDelete}
                    onClose={() => setDeleteTarget(null)}
                />
            )}
        </AdminModal>
    );
}

export default LessonMediaModal;
