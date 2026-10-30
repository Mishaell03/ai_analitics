import {useEffect, useRef} from "react";
import {X} from "lucide-react";
import {useBodyScrollLock} from "@/hooks/useBodyScrollLock.js";
import styles from "./adminModal.module.css";

/**
 * Оболочка модального окна админки.
 *
 * Берёт на себя общее для всех окон: затемнение, закрытие по Escape,
 * блокировку прокрутки фона и кнопку закрытия. Содержимое окна
 * передаётся дочерними элементами.
 *
 * overlayChildren рендерятся рядом с окном, но внутри затемнения:
 * так открывается окно медиафайлов поверх редактора урока.
 */
function AdminModal({
    onClose,
    ariaLabel,
    closeLabel,
    maxWidth,
    closeOnEscape = true,
    overlayChildren = null,
    children,
}) {
    // обработчик не пересоздаём на каждом рендере родителя:
    // ссылка всегда указывает на актуальный onClose
    const onCloseRef = useRef(onClose);
    useBodyScrollLock();

    useEffect(() => {
        onCloseRef.current = onClose;
    }, [onClose]);

    useEffect(() => {
        const handleKeyDown = (event) => {
            if (closeOnEscape && event.key === "Escape") {
                onCloseRef.current();
            }
        };

        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [closeOnEscape]);

    return (
        <div
            className={styles.overlay}
            onClick={(event) => {
                // клик по вложенному окну не должен закрывать родительское
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
            role="presentation"
        >
            <div
                className={styles.modal}
                onClick={(event) => event.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-label={ariaLabel}
                style={maxWidth ? {maxWidth} : undefined}
            >
                <button
                    type="button"
                    className={styles.close}
                    onClick={onClose}
                    aria-label={closeLabel}
                >
                    <X/>
                </button>

                {children}
            </div>

            {overlayChildren}
        </div>
    );
}

export default AdminModal;
