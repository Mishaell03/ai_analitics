import styles from "./statCard.module.css";

/**
 * Карточка одной метрики дашборда.
 *
 * Пока loading — вместо значений показываются скелетоны,
 * поэтому странице не нужно дублировать разметку заглушек.
 */
function StatCard({icon: Icon, value, label, tone = "accent", loading = false}) {
    return (
        <article className={styles.card} data-tone={tone}>
            <span className={styles.icon}>
                {loading ? null : <Icon/>}
            </span>

            {loading ? (
                <div className={styles.skeleton}>
                    <span className={styles.skeletonLabel}/>
                    <span className={styles.skeletonValue}/>
                </div>
            ) : (
                <div className={styles.body}>
                    <span className={styles.label}>{label}</span>
                    <strong className={styles.value}>{value}</strong>
                </div>
            )}
        </article>
    );
}

export default StatCard;
