import {RefreshCw} from "lucide-react";
import styles from "./adminPageHeader.module.css";

/**
 * Заголовок раздела админки.
 *
 * Одинаков для дашборда, пользователей и курсов: бейдж-надпись,
 * название с описанием и кнопка обновления данных.
 */
function AdminPageHeader({
    eyebrow,
    title,
    subtitle,
    onRefresh,
    refreshing = false,
    refreshLabel,
    refreshingLabel,
    titleClassName,
}) {
    return (
        <section className={styles.heading}>
            <div className={styles.badge}>
                <span className={styles.badgeDot}/>
                {eyebrow}
            </div>

            <div className={styles.headingRow}>
                <div className={styles.headingContent}>
                    <h1 className={titleClassName}>{title}</h1>
                    <p>{subtitle}</p>
                </div>

                {onRefresh && (
                    <button
                        type="button"
                        className={styles.refreshButton}
                        onClick={onRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw/>
                        <span>
                            {refreshing ? refreshingLabel : refreshLabel}
                        </span>
                    </button>
                )}
            </div>
        </section>
    );
}

export default AdminPageHeader;
