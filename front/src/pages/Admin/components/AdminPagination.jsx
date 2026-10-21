import styles from "./adminPagination.module.css";

/**
 * Постраничная навигация списков админки.
 *
 * Компонент только рисует кнопки: страницей управляет вызывающая
 * сторона, потому что списки загружаются разными запросами.
 */
function AdminPagination({
    page,
    totalPages,
    onPrevious,
    onNext,
    label,
    previousLabel,
    nextLabel,
}) {
    if (totalPages <= 1) {
        return null;
    }

    return (
        <nav className={styles.pagination}>
            <button
                type="button"
                className={styles.pageButton}
                onClick={onPrevious}
                disabled={page <= 1}
                aria-label={previousLabel}
            >
                ‹
            </button>

            <div className={styles.pageInfo}>{label}</div>

            <button
                type="button"
                className={styles.pageButton}
                onClick={onNext}
                disabled={page >= totalPages}
                aria-label={nextLabel}
            >
                ›
            </button>
        </nav>
    );
}

export default AdminPagination;
