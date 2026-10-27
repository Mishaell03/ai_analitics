import {TriangleAlert} from "lucide-react";
import styles from "./confirmModal.module.css";

/**
 * Диалог подтверждения.
 *
 * Один компонент на все подтверждения админки: удаление курса,
 * модуля или урока, блокировка пользователя. Тон кнопки передаётся
 * параметром tone: danger — опасное действие, ok — безопасное.
 *
 * Тексты кнопок передаёт вызывающий код: компонент не знает
 * про язык и не содержит готовых строк.
 */
function ConfirmModal({
    title,
    description,
    confirmText,
    busyText,
    cancelText,
    tone = "danger",
    icon: Icon = TriangleAlert,
    busy = false,
    onConfirm,
    onClose,
}) {
    return (
        <div className={styles.overlay} onClick={onClose} role="presentation">
            <div
                className={styles.confirm}
                onClick={(event) => event.stopPropagation()}
                role="dialog"
                aria-modal="true"
            >
                <span className={styles.icon} data-tone={tone}>
                    <Icon/>
                </span>

                <h3>{title}</h3>

                {description && <p>{description}</p>}

                <div className={styles.actions}>
                    <button
                        type="button"
                        className={styles.cancel}
                        onClick={onClose}
                        disabled={busy}
                    >
                        {cancelText}
                    </button>

                    <button
                        type="button"
                        className={styles.confirmButton}
                        data-tone={tone}
                        onClick={onConfirm}
                        disabled={busy}
                    >
                        {busy ? busyText : confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ConfirmModal;
