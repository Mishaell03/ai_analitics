import {useState} from "react";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "@/pages/Admin/components/adminForm.module.css";

const MAX_TITLE = 255;
const MAX_DESCRIPTION = 2000;

/**
 * Форма создания и редактирования модуля курса.
 *
 * Как и форма курса, проверяет поля и отдаёт готовые значения
 * странице: запросы и уведомления — её ответственность.
 */
function ModuleFormModal({mode, module, saving, onClose, onSubmit, onError}) {
    const t = useAdminTranslation();

    const [title, setTitle] = useState(module.title);
    const [description, setDescription] = useState(module.description);
    const [isActive, setIsActive] = useState(module.is_active);

    const isCreate = mode === "create";

    const handleSubmit = (event) => {
        event.preventDefault();

        const cleanTitle = title.trim();
        const cleanDescription = description.trim();

        if (!cleanTitle || cleanTitle.length > MAX_TITLE) {
            onError(t("moduleTitleError"));
            return;
        }

        if (cleanDescription.length > MAX_DESCRIPTION) {
            onError(t("moduleDescriptionError"));
            return;
        }

        onSubmit({
            title: cleanTitle,
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
                {isCreate ? t("moduleCreateTitle") : t("moduleEditTitle")}
            </h2>

            <form onSubmit={handleSubmit} className={styles.form}>
                <label className={styles.field}>
                    <span>{t("moduleTitleField")}</span>
                    <input
                        required
                        maxLength={MAX_TITLE}
                        value={title}
                        onChange={(event) => setTitle(event.target.value)}
                    />
                </label>

                <label className={styles.field}>
                    <span>{t("moduleDescriptionField")}</span>
                    <textarea
                        maxLength={MAX_DESCRIPTION}
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        rows={4}
                    />
                    <small className={styles.fieldHint}>{t("descriptionFormatHint")}</small>
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

export default ModuleFormModal;
