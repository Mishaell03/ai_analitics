import styles from "./emptyState.module.css";

/**
 * Заглушка для пустых данных и ошибок загрузки.
 *
 * action — необязательный элемент управления (кнопка повтора,
 * ссылка на профиль и т.п.), рендерится как есть.
 */
function EmptyState({icon: Icon, title, description, action}) {
    return (
        <div className={styles.empty}>
            <span className={styles.icon}>
                {Icon ? <Icon/> : null}
            </span>

            <h3>{title}</h3>

            {description && <p>{description}</p>}

            {action}
        </div>
    );
}

export default EmptyState;
