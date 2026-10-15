import styles from "./badge.module.css";

/**
 * Небольшой статусный чип: тон задаётся через tone.
 * Используется в списках и карточке пользователя.
 */
function Badge({children, tone = "muted", icon: Icon}) {
    return (
        <span className={styles.badge} data-tone={tone}>
            {Icon ? <Icon/> : null}
            {children}
        </span>
    );
}

export default Badge;
