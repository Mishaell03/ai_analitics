import {useCallback, useEffect, useRef, useState} from "react";
import {ImageOff, ImageUp, Loader2, Trash2, TriangleAlert} from "lucide-react";
import {
    deleteCourseImage,
    getCourseImage,
    uploadCourseImage,
} from "@/api/media.js";
import {formatBytes} from "@/services/format.js";
import {IMAGE_ACCEPT, MEDIA_LIMITS} from "@/services/media.js";
import {getLocalizedErrorMessage, useFileUpload} from "@/hooks/useFileUpload.js";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./courseCover.module.css";

// обложка — это изображение, backend сам пережимает его в WebP
const ACCEPT = IMAGE_ACCEPT;
const MAX_SIZE = MEDIA_LIMITS.image.maxSize;

/**
 * ОБЛОЖКА КУРСА
 *
 * Файл лежит в приватном хранилище: backend сам пережимает его в WebP
 * и отдаёт временную ссылку. Здесь только выбор файла, отправка и
 * предпросмотр.
 */
function CourseCoverModal({course, onClose, onSaved}) {
    const t = useAdminTranslation();

    const [image, setImage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(null);
    const [deleteConfirm, setDeleteConfirm] = useState(false);
    const [deleting, setDeleting] = useState(false);

    const {uploading, progress, error, upload, setError} = useFileUpload();

    const inputRef = useRef(null);

    const loadImage = useCallback(async () => {
        setLoading(true);
        setLoadError(null);

        try {
            const data = await getCourseImage(course.slug);

            setImage(data);
        } catch (requestError) {
            // обложки может не быть — это не ошибка
            if (requestError?.response?.status === 404) {
                setImage(null);
            } else {
                setLoadError(getLocalizedErrorMessage(requestError, t, t("coverLoadError")));
            }
        } finally {
            setLoading(false);
        }
    }, [course.slug, t]);

    useEffect(() => {
        loadImage();
    }, [loadImage]);

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

        if (!file.type.startsWith("image/")) {
            setError(new Error(t("coverTypeError")));

            return;
        }

        if (file.size > MAX_SIZE) {
            setError(new Error(t("coverSizeError", {limit: formatBytes(MAX_SIZE)})));

            return;
        }

        const result = await upload(
            (selected, options) => uploadCourseImage(course.slug, selected, options),
            file
        );

        if (result) {
            setImage(result);

            onSaved?.(result);
        }
    }, [course.slug, upload, onSaved, t, setError]);

    const handleDelete = useCallback(async () => {
        setDeleting(true);

        try {
            await deleteCourseImage(course.slug);

            setImage(null);
            setDeleteConfirm(false);

            onSaved?.(null);
        } catch (requestError) {
            setError(new Error(getLocalizedErrorMessage(requestError, t, t("coverDeleteError"))));
            setDeleteConfirm(false);
        } finally {
            setDeleting(false);
        }
    }, [course.slug, onSaved, t, setError]);

    const renderPreview = () => {
        if (loading) {
            return (
                <div className={styles.preview} data-state="loading">
                    <Loader2 className={styles.spinner}/>
                </div>
            );
        }

        if (loadError) {
            return (
                <div className={styles.preview} data-state="error">
                    <TriangleAlert/>
                    <span>{loadError}</span>
                </div>
            );
        }

        if (!image?.url) {
            return (
                <div className={styles.preview} data-state="empty">
                    <ImageOff/>
                    <span>{t("coverEmpty")}</span>
                </div>
            );
        }

        return (
            <div className={styles.preview} data-state="ready">
                <img src={image.url} alt={course.title}/>
            </div>
        );
    };

    const renderMeta = () => {
        if (!image) {
            return null;
        }

        return (
            <div className={styles.meta}>
                {image.width > 0 && image.height > 0 && (
                    <span>
                        {image.width} × {image.height}
                    </span>
                )}

                <span>{formatBytes(image.size_bytes)}</span>

                <span>{image.content_type}</span>
            </div>
        );
    };

    return (
        <AdminModal
            onClose={onClose}
            ariaLabel={t("coverTitle")}
            closeLabel={t("coverClose")}
        >
            <header className={styles.header}>
                <span className={styles.headerIcon}>
                    <ImageUp/>
                </span>

                <div className={styles.headerContent}>
                    <h2>{t("coverTitle")}</h2>
                    <p>{course.title}</p>
                </div>
            </header>

            {renderPreview()}

            {renderMeta()}

            {uploading && (
                <div className={styles.progress}>
                    <div className={styles.progressBar} data-value={progress}>
                        <span style={{width: `${progress}%`}}/>
                    </div>

                    <span className={styles.progressText}>
                        {t("coverUploading", {progress})}
                    </span>
                </div>
            )}

            {error && (
                <p className={styles.error}>
                    <TriangleAlert/>
                    {getLocalizedErrorMessage(error, t, t("coverUploadError"))}
                </p>
            )}

            <p className={styles.hint}>
                {t("coverHint", {limit: formatBytes(MAX_SIZE)})}
            </p>

            <div className={styles.actions}>
                <input
                    ref={inputRef}
                    type="file"
                    accept={ACCEPT}
                    className={styles.fileInput}
                    onChange={handleFileChange}
                />

                <button
                    type="button"
                    className={styles.uploadButton}
                    onClick={handleSelectFile}
                    disabled={uploading}
                >
                    <ImageUp/>
                    <span>
                        {uploading
                            ? t("coverUploadingShort")
                            : image
                                ? t("coverReplace")
                                : t("coverUpload")}
                    </span>
                </button>

                {image && (
                    <button
                        type="button"
                        className={styles.deleteButton}
                        onClick={() => setDeleteConfirm(true)}
                        disabled={uploading || deleting}
                    >
                        <Trash2/>
                        <span>{t("coverDelete")}</span>
                    </button>
                )}
            </div>

            {deleteConfirm && (
                <ConfirmModal
                    title={t("coverDeleteTitle")}
                    description={t("coverDeleteDescription")}
                    confirmText={t("confirmDeleteButton")}
                    busyText={t("confirmDeleteProcess")}
                    cancelText={t("confirmCancelButton")}
                    busy={deleting}
                    onConfirm={handleDelete}
                    onClose={() => setDeleteConfirm(false)}
                />
            )}
        </AdminModal>
    );
}

export default CourseCoverModal;
