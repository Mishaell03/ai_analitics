import {useState} from "react";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "@/pages/Admin/components/adminForm.module.css";

const MAX_TITLE = 255;
const MAX_DESCRIPTION = 2000;
const SLUG_PATTERN = /^[a-z0-9-]+$/;

/**
 * Форма создания и редактирования курса.
 *
 * Проверяет поля до отправки, а сохранение и уведомления остаются
 * на странице: форма не знает, создаётся курс или обновляется.
 */
function CourseFormModal({mode, course, saving, onClose, onSubmit, onError}) {
    const t = useAdminTranslation();

    const [title, setTitle] = useState(course.title);
    const [slug, setSlug] = useState(course.slug);
    const [description, setDescription] = useState(course.description);
    const [isActive, setIsActive] = useState(course.is_active);

    const isCreate = mode === "create";

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
        });
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
                </label>

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
