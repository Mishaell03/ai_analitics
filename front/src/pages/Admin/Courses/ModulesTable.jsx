import {
    BookOpen,
    BookOpenCheck,
    Pencil,
    Plus,
    Power,
    Trash2,
    TriangleAlert,
} from "lucide-react";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {getModuleId} from "@/pages/Admin/utils/getModuleId.js";
import styles from "./courses.module.css";

const SKELETON_ROWS = 5;

/**
 * Таблица модулей выбранного курса.
 *
 * Перетаскивание строк настраивается страницей: она же сохраняет
 * новый порядок и обновляет список.
 */
function ModulesTable({
    courses,
    selectedCourseSlug,
    selectedModuleId,
    modules,
    loading,
    error,
    reordering,
    saving,
    dragIndex,
    dragOverIndex,
    getDragProps,
    onSelectCourse,
    onCreateModule,
    onRetry,
    onSelectModule,
    onEditModule,
    onToggleStatus,
    onDeleteModule,
}) {
    const t = useAdminTranslation();

    const isSelected = (module) => selectedModuleId !== null
        && selectedModuleId === getModuleId(module);

    // заголовок выбранного курса: его же показывает выпадающий список.
    // курса может не быть в текущей странице списка — тогда показываем slug
    const selectedCourse = courses.find((course) => course.slug === selectedCourseSlug);

    const selectedCourseLabel = selectedCourse
        ? selectedCourse.title
        : selectedCourseSlug || t("modulesPanelHint");

    return (
        <section className={pageStyles.panel}>
            <div className={pageStyles.panelHeader}>
                <div>
                    <h2>{t("modulesPanelTitle")}</h2>
                    <p>{selectedCourseLabel}</p>
                </div>

                <div className={styles.moduleToolbar}>
                    <select
                        className={styles.select}
                        value={selectedCourseSlug}
                        onChange={(event) => onSelectCourse(event.target.value)}
                    >
                        <option value="">{t("courseSelectPlaceholder")}</option>
                        {courses.map((course) => (
                            <option key={course.slug} value={course.slug}>
                                {course.title}
                            </option>
                        ))}
                    </select>

                    <button
                        type="button"
                        className={pageStyles.primaryButton}
                        onClick={onCreateModule}
                        disabled={!selectedCourseSlug}
                    >
                        <Plus/>
                        <span>{t("modulesCreate")}</span>
                    </button>
                </div>
            </div>

            {loading && (
                <div className={pageStyles.tableWrap}>
                    <table className={pageStyles.table} aria-busy="true">
                        <thead>
                        <tr>
                            <th>{t("columnPosition")}</th>
                            <th>{t("columnTitle")}</th>
                            <th>{t("columnStatus")}</th>
                            <th data-align="right">{t("columnActions")}</th>
                        </tr>
                        </thead>
                        <tbody>
                        {Array.from({length: SKELETON_ROWS}, (_, index) => (
                            <tr className={pageStyles.row} key={index}>
                                <td><span className={pageStyles.skeletonCell} data-width="20%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="60%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="30%"/></td>
                                <td><span className={pageStyles.skeletonCell} data-width="50%"/></td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            )}

            {!loading && error && (
                <EmptyState
                    icon={TriangleAlert}
                    title={t("errorTitle")}
                    description={t("errorDescription")}
                    action={
                        <button
                            type="button"
                            className={pageStyles.retryButton}
                            onClick={onRetry}
                        >
                            {t("errorRetry")}
                        </button>
                    }
                />
            )}

            {!loading && !error && selectedCourseSlug && modules.length === 0 && (
                <EmptyState
                    icon={BookOpen}
                    title={t("modulesEmptyTitle")}
                    description={t("modulesEmptyDescription")}
                />
            )}

            {!loading && !error && selectedCourseSlug && modules.length > 0 && (
                <div className={pageStyles.tableWrap}>
                    {reordering && (
                        <div className={pageStyles.reorderHint}>
                            Сохраняем новый порядок…
                        </div>
                    )}

                    <table className={pageStyles.table}>
                        <thead>
                        <tr>
                            <th>{t("columnPosition")}</th>
                            <th>{t("columnTitle")}</th>
                            <th>{t("columnStatus")}</th>
                            <th data-align="right">{t("columnActions")}</th>
                        </tr>
                        </thead>
                        <tbody>
                        {modules.map((module, index) => (
                            <tr
                                className={
                                    `${pageStyles.row}` +
                                    (dragIndex === index ? ` ${pageStyles.rowDragging}` : "") +
                                    (dragOverIndex === index ? ` ${pageStyles.rowDropTarget}` : "")
                                }
                                key={getModuleId(module)}
                                {...getDragProps(index, reordering)}
                            >
                                <td data-label={t("columnPosition")}>
                                    <div className={pageStyles.moduleCell}>
                                        <span className={pageStyles.positionBadge}>
                                            {module.position ?? index + 1}
                                        </span>
                                        <span className={pageStyles.dragHandle} aria-hidden="true">
                                            ⋮⋮
                                        </span>
                                    </div>
                                </td>

                                <td data-cell="title">
                                    <div className={pageStyles.moduleCell}>
                                        <div className={pageStyles.moduleMeta}>
                                            <strong>{module.title}</strong>
                                            {module.description && (
                                                <span>{module.description}</span>
                                            )}
                                        </div>
                                    </div>
                                </td>

                                <td data-label={t("columnStatus")}>
                                    <Badge tone={module.is_active ? "focus" : "muted"}>
                                        {module.is_active ? t("statusActive") : t("statusInactive")}
                                    </Badge>
                                </td>

                                <td data-align="right" data-cell="actions" data-label={t("columnActions")}>
                                    <div className={pageStyles.actions}>
                                        <button
                                            type="button"
                                            className={
                                                isSelected(module)
                                                    ? pageStyles.actionButtonActive
                                                    : pageStyles.actionButton
                                            }
                                            onClick={() => onSelectModule(module)}
                                            title={t("moduleActionLessons")}
                                        >
                                            <BookOpenCheck/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            onClick={() => onEditModule(module)}
                                            title={t("actionEdit")}
                                        >
                                            <Pencil/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            onClick={() => onToggleStatus(module)}
                                            title={module.is_active ? t("actionDeactivate") : t("actionActivate")}
                                            disabled={saving}
                                        >
                                            <Power/>
                                        </button>

                                        <button
                                            type="button"
                                            className={pageStyles.actionButton}
                                            data-tone="danger"
                                            onClick={() => onDeleteModule(module)}
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

            {!loading && !error && !selectedCourseSlug && (
                <EmptyState
                    icon={BookOpen}
                    title={t("modulesSelectTitle")}
                    description={t("modulesSelectDescription")}
                />
            )}
        </section>
    );
}

export default ModulesTable;
