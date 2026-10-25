import {useRef, useState} from "react";
import {ImageUp, X} from "lucide-react";
import {formatBytes} from "@/services/format.js";
import {IMAGE_ACCEPT, MEDIA_LIMITS} from "@/services/media.js";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "@/pages/Admin/components/adminForm.module.css";

const MAX_TITLE = 255;
const MAX_DESCRIPTION = 2000;
const SLUG_PATTERN = /^[a-z0-9-]+$/;

// обложка — изображение; правила те же, что у отдельного окна обложки
const MAX_COVER_SIZE = MEDIA_LIMITS.image.maxSize;

/**
 * Форма создания и редактирования курса.
 *
 * Проверяет поля до отправки, а сохранение и уведомления остаются
 * на странице: форма не знает, создаётся курс или обновляется.
 *
 * Обложку можно выбрать прямо здесь. У нового курса ещё нет slug,
 * поэтому файл уходит на сервер не сразу: страница сначала создаёт
 * курс, а затем отправляет обложку по полученному slug.
 */
function CourseFormModal({mode, course, saving, onClose, onSubmit, onError}) {
    const t = useAdminTranslation();

    const [title, setTitle] = useState(course.title);
    const [slug, setSlug] = useState(course.slug);
    const [description, setDescription] = useState(course.description);
    const [isActive, setIsActive] = useState(course.is_active);
    const [coverFile, setCoverFile] = useState(null);

    const coverInputRef = useRef(null);

    const isCreate = mode === "create";

    const handleCoverChange = (event) => {
        const file = event.target.files?.[0];

        // значение сбрасываем, иначе тот же файл не выберется повторно
        event.target.value = "";

        if (!file) {
            return;
        }

        if (!file.type.startsWith("image/")) {
            onError(t("coverTypeError"));
            return;
        }

        if (file.size > MAX_COVER_SIZE) {
            onError(t("coverSizeError", {limit: formatBytes(MAX_COVER_SIZE)}));
            return;
        }

        setCoverFile(file);
    };

    const handleSubmit = (event) => {
        event.preventDefault();

        const cleanTitle = title.trim();
        const cleanSlug = slug.trim();
        const cleanDescription = description.trim();

        if (!cleanTitle || cleanTitle.length > MAX_TITLE) {
            onError(t("courseTitleError"));
            return;
        }

        if (cleanSlug && (cleanSlug.length > MAX_TITLE || !SLUG_PATTERN.test(cleanSlug))) {
            onError(t("courseSlugError"));
            return;
        }

        if (cleanDescription.length > MAX_DESCRIPTION) {
            onError(t("courseDescriptionError"));
            return;
        }

        onSubmit({
            title: cleanTitle,
            slug: cleanSlug || null,
            description: cleanDescription || null,
            is_active: isActive,
        }, coverFile);
    };

    return (
        <AdminModal
            onClose={onClose}
            closeLabel={t("modalClose")}
            maxWidth={640}
        >
            <h2 className={styles.modalTitle}>
                {isCreate ? t("courseCreateTitle") : t("courseEditTitle")}
            </h2>

            <form onSubmit={handleSubmit} className={styles.form}>
                <label className={styles.field}>
                    <span>{t("courseTitleField")}</span>
                    <input
                        required
                        maxLength={MAX_TITLE}
                        value={title}
                        onChange={(event) => setTitle(event.target.value)}
                    />
                </label>

                <label className={styles.field}>
                    <span>{t("courseSlugField")}</span>
                    <input
                        maxLength={MAX_TITLE}
                        value={slug}
                        onChange={(event) => setSlug(event.target.value)}
                    />
                </label>

                <label className={styles.field}>
                    <span>{t("courseDescriptionField")}</span>
                    <textarea
                        maxLength={MAX_DESCRIPTION}
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        rows={4}
                    />
                    <small className={styles.fieldHint}>{t("descriptionFormatHint")}</small>
                </label>

                <div className={styles.cover}>
                    <span className={styles.coverLabel}>{t("courseCoverField")}</span>

                    <div className={styles.coverRow}>
                        <input
                            ref={coverInputRef}
                            type="file"
                            accept={IMAGE_ACCEPT}
                            className={styles.fileInput}
                            onChange={handleCoverChange}
                        />

                        <button
                            type="button"
                            className={styles.coverButton}
                            onClick={() => coverInputRef.current?.click()}
                            disabled={saving}
                        >
                            <ImageUp/>
                            <span>
                                {coverFile ? t("courseCoverReplace") : t("courseCoverChoose")}
                            </span>
                        </button>

                        {coverFile && (
                            <>
                                <span className={styles.coverName} title={coverFile.name}>
                                    {coverFile.name}
                                </span>

                                <button
                                    type="button"
                                    className={styles.coverClear}
                                    onClick={() => setCoverFile(null)}
                                    disabled={saving}
                                    title={t("courseCoverClear")}
                                    aria-label={t("courseCoverClear")}
                                >
                                    <X/>
                                </button>
                            </>
                        )}
                    </div>

                    <small className={styles.coverHint}>
                        {t("courseCoverHint", {limit: formatBytes(MAX_COVER_SIZE)})}
                    </small>
                </div>

                <label className={styles.checkboxField}>
                    <input
                        type="checkbox"
                        checked={isActive}
                        onChange={(event) => setIsActive(event.target.checked)}
                    />
                    <span>{t("formActive")}</span>
                </label>

                <div className={styles.formActions}>
                    <button
                        type="button"
                        className={styles.cancelButton}
                        onClick={onClose}
                        disabled={saving}
                    >
                        {t("formCancel")}
                    </button>

                    <button type="submit" className={styles.saveButton} disabled={saving}>
                        {saving ? t("formSaving") : t("formSave")}
                    </button>
                </div>
            </form>
        </AdminModal>
    );
}

export default CourseFormModal;
