import {
    BookOpen,
    ImageUp,
    Pencil,
    Plus,
    Power,
    Trash2,
} from "lucide-react";
import {formatNumber} from "@/services/format.js";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import AdminPagination from "@/pages/Admin/components/AdminPagination.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {PER_PAGE} from "./useCourses.js";
import styles from "./courses.module.css";

/**
 * Таблица курсов со страницами и действиями.
 *
 * Компонент только показывает данные: выбранный курс, запросы
 * и модальные окна остаются на странице.
 */
function CoursesTable({
    courses,
    page,
    totalPages,
    loading,
    saving,
    onSelectCourse,
    onCreateCourse,
    onOpenCover,
    onEditCourse,
    onToggleStatus,
    onDeleteCourse,
    onPreviousPage,
    onNextPage,
}) {
    const t = useAdminTranslation();

    return (
        <section className={pageStyles.panel}>
            <div className={pageStyles.panelHeader}>
                <div>
                    <h2>{t("coursesPanelTitle")}</h2>
                    <p>{t("coursesPanelHint")}</p>
                </div>

                <button
                    type="button"
                    className={pageStyles.primaryButton}
                    onClick={onCreateCourse}
                >
                    <Plus/>
                    <span>{t("coursesCreate")}</span>
                </button>
            </div>

            {loading && (
                <div className={pageStyles.tableWrap}>
                    <table className={pageStyles.table} aria-busy="true">
                        <thead>
                        <tr>
                            <th>{t("columnTitle")}</th>
                            <th>{t("columnSlug")}</th>
                            <th data-align="right">{t("columnModules")}</th>
                            <th data-align="right">{t("columnLessons")}</th>
                            <th>{t("columnStatus")}</th>
                            <th data-align="right">{t("columnActions")}</th>
                        </tr>
                        </thead>
                        <tbody>
                        {Array.from({length: PER_PAGE}, (_, index) => (
                            <tr className={pageStyles.row} key={index}>
                                <td><span className={pageStyles.skeletonCell} data-width="60%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="40%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="20%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="20%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="30%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="50%"/></td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            )}

            {!loading && courses.length === 0 && (
                <EmptyState
                    icon={BookOpen}
                    title={t("coursesEmptyTitle")}
                    description={t("coursesEmptyDescription")}
                />
            )}

            {!loading && courses.length > 0 && (
                <div className={pageStyles.tableWrap}>
                    <table className={pageStyles.table}>
                        <thead>
                        <tr>
                            <th>{t("columnTitle")}</th>
                            <th>{t("columnSlug")}</th>
                            <th data-align="right">{t("columnModules")}</th>
                            <th data-align="right">{t("columnLessons")}</th>
                            <th>{t("columnStatus")}</th>
                            <th data-align="right">{t("columnActions")}</th>
                        </tr>
                        </thead>
                        <tbody>
                        {courses.map((course) => (
                            <tr
                                className={pageStyles.row}
                                key={course.slug}
                                onClick={() => onSelectCourse(course.slug)}
                                tabIndex={0}
                                role="button"
                                aria-label={course.title}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        onSelectCourse(course.slug);
                                    }
                                }}
                            >
                                <td data-cell="title">
                                    <div className={styles.courseCell}>
                                        {course.main_image_url ? (
                                            <img
                                                className={styles.courseImage}
                                                src={course.main_image_url}
                                                alt={course.title}
                                            />
                                        ) : (
                                            <span className={styles.courseIcon}>
                                                <BookOpen/>
                                            </span>
                                        )}

                                        <div className={styles.courseMeta}>
                                            <strong>{course.title}</strong>
                                            {course.description && (
                                                <span>{course.description}</span>
                                            )}
                                        </div>
                                    </div>
                                </td>

                                <td className={pageStyles.cellMuted} data-label={t("columnSlug")}>
                                    {course.slug}
                                </td>

                                <td
                                    className={pageStyles.cellMuted}
                                    data-align="right"
                                    data-label={t("columnModules")}
                                >
                                    {formatNumber(course.modules_count ?? 0)}
                                </td>

                                <td
                                    className={pageStyles.cellMuted}
                                    data-align="right"
                                    data-label={t("columnLessons")}
                                >
                                    {formatNumber(course.lessons_count ?? 0)}
                                </td>

                                <td data-label={t("columnStatus")}>
                                    <Badge tone={course.is_active ? "focus" : "muted"}>
                                        {course.is_active ? t("statusActive") : t("statusInactive")}
                                    </Badge>
                                </td>

                                <td data-align="right" data-cell="actions" data-label={t("columnActions")}>
                                    <div className={pageStyles.actions}>
                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                onOpenCover(course);
                                            }}
                                            title={t("courseActionCover")}
                                        >
                                            <ImageUp/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                onEditCourse(course);
                                            }}
                                            title={t("actionEdit")}
                                        >
                                            <Pencil/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                onToggleStatus(course);
                                            }}
                                            title={course.is_active ? t("actionDeactivate") : t("actionActivate")}
                                            disabled={saving}
                                        >
                                            <Power/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            data-tone="danger"
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                onDeleteCourse(course);
                                            }}
                                            title={t("actionDelete")}
                                        >
                                            <Trash2/>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            )}

            {!loading && (
                <AdminPagination
                    page={page}
                    totalPages={totalPages}
                    onPrevious={onPreviousPage}
                    onNext={onNextPage}
                    label={t("paginationInfo", {
                        page: formatNumber(page),
                        total: formatNumber(totalPages),
                    })}
                    previousLabel={t("paginationPrev")}
                    nextLabel={t("paginationNext")}
                />
            )}
        </section>
    );
}

export default CoursesTable;
