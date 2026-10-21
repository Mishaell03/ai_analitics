import {BookOpen, Eye, FileText, Pencil, Power, Trash2, TriangleAlert} from "lucide-react";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";

const SKELETON_ROWS = 3;

/**
 * Таблица уроков выбранного модуля.
 *
 * Перетаскивание и действия передаются из панели уроков: таблица
 * отвечает только за отрисовку списка и состояний загрузки.
 */
function LessonsTable({
    lessons,
    loading,
    error,
    reordering,
    saving,
    dragIndex,
    dragOverIndex,
    getDragProps,
    onRetry,
    onEdit,
    onToggleStatus,
    onOpen,
    onDelete,
}) {
    const t = useAdminTranslation();

    if (loading) {
        return (
            <div className={pageStyles.tableWrap}>
                <table className={pageStyles.table} aria-busy="true">
                    <thead>
                    <tr>
                        <th>{t("adminLessonsColumnPosition")}</th>
                        <th>{t("adminLessonsColumnTitle")}</th>
                        <th>{t("adminLessonsColumnStatus")}</th>
                        <th>{t("adminLessonsColumnContent")}</th>
                        <th data-align="right">{t("adminLessonsColumnActions")}</th>
                    </tr>
                    </thead>
                    <tbody>
                    {Array.from({length: SKELETON_ROWS}, (_, index) => (
                        <tr className={pageStyles.row} key={index}>
                            <td><span className={pageStyles.skeletonCell} data-width="20%"/></td>
                            <td><span className={pageStyles.skeletonCell} data-width="60%"/></td>
                            <td><span className={pageStyles.skeletonCell} data-width="40%"/></td>
                            <td><span className={pageStyles.skeletonCell} data-width="30%"/></td>
                            <td><span className={pageStyles.skeletonCell} data-width="50%"/></td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
        );
    }

    if (error) {
        return (
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
        );
    }

    if (lessons.length === 0) {
        return (
            <EmptyState
                icon={BookOpen}
                title={t("adminLessonsEmptyTitle")}
                description={t("adminLessonsEmptyDescription")}
            />
        );
    }

    return (
        <div className={pageStyles.tableWrap}>
            {reordering && (
                <div className={pageStyles.reorderHint}>
                    Сохраняем новый порядок…
                </div>
            )}

            <table className={pageStyles.table}>
                <thead>
                <tr>
                    <th>{t("adminLessonsColumnPosition")}</th>
                    <th>{t("adminLessonsColumnTitle")}</th>
                    <th>{t("adminLessonsColumnStatus")}</th>
                    <th>{t("adminLessonsColumnContent")}</th>
                    <th data-align="right">{t("adminLessonsColumnActions")}</th>
                </tr>
                </thead>
                <tbody>
                {lessons.map((lesson, index) => (
                    <tr
                        className={
                            `${pageStyles.row}` +
                            (dragIndex === index ? ` ${pageStyles.rowDragging}` : "") +
                            (dragOverIndex === index ? ` ${pageStyles.rowDropTarget}` : "")
                        }
                        key={lesson.lesson_id}
                        {...getDragProps(index, reordering)}
                    >
                        <td data-label={t("columnPosition")}>
                            <div className={pageStyles.moduleCell}>
                                <span className={pageStyles.positionBadge}>
                                    {lesson.position}
                                </span>
                                <span className={pageStyles.dragHandle} aria-hidden="true">
                                    ⋮⋮
                                </span>
                            </div>
                        </td>

                        <td data-cell="title">
                            <div className={pageStyles.moduleCell}>
                                <div className={pageStyles.moduleMeta}>
                                    <strong>{lesson.title}</strong>
                                    {lesson.description && (
                                        <span>{lesson.description}</span>
                                    )}
                                </div>
                            </div>
                        </td>

                        <td data-label={t("columnStatus")}>
                            <Badge tone={lesson.is_published ? "focus" : "muted"}>
                                {lesson.is_published
                                    ? t("adminLessonsPublished")
                                    : t("adminLessonsDraft")}
                            </Badge>
                        </td>

                        <td data-label={t("columnContent")}>
                            <Badge tone={lesson.has_content ? "accent" : "muted"} icon={FileText}>
                                {lesson.has_content
                                    ? t("adminLessonsContentYes")
                                    : t("adminLessonsContentNo")}
                            </Badge>
                        </td>

                        <td data-align="right" data-cell="actions" data-label={t("columnActions")}>
                            <div className={pageStyles.actions}>
                                <button
                                    type="button"
                                    className={pageStyles.actionButton}
                                    onClick={() => onEdit(lesson)}
                                    title={t("adminLessonsEdit")}
                                >
                                    <Pencil/>
                                </button>

                                <button
                                    type="button"
                                    className={pageStyles.actionButton}
                                    onClick={() => onToggleStatus(lesson)}
                                    title={lesson.is_published
                                        ? t("adminLessonsUnpublish")
                                        : t("adminLessonsPublish")}
                                    disabled={saving}
                                >
                                    <Power/>
                                </button>

                                <button
                                    type="button"
                                    className={pageStyles.actionButton}
                                    onClick={() => onOpen(lesson)}
                                    title={t("adminLessonsOpen")}
                                >
                                    <Eye/>
                                </button>

                                <button
                                    type="button"
                                    className={pageStyles.actionButton}
                                    data-tone="danger"
                                    onClick={() => onDelete(lesson)}
                                    title={t("adminLessonsDelete")}
                                    disabled={saving}
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
    );
}

export default LessonsTable;
