import {useCallback, useState} from "react";
import {BookOpen, Plus} from "lucide-react";
import {getApiErrorMessage} from "@/services/apiError.js";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import AdminToast from "@/pages/Admin/components/AdminToast.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {useDragReorder} from "@/pages/Admin/hooks/useDragReorder.js";
import {useToast} from "@/pages/Admin/hooks/useToast.js";
import LessonContentModal from "./LessonContentModal.jsx";
import LessonEditor from "./LessonEditor.jsx";
import LessonsTable from "./LessonsTable.jsx";
import {getModuleId} from "@/pages/Admin/utils/getModuleId.js";
import {useModuleLessons} from "./useModuleLessons.js";

/**
 * Уроки выбранного модуля.
 *
 * Панель сама решает, какие уроки показать: странице-родителю
 * достаточно передать курс и модуль. При смене модуля список
 * запрашивается заново, а открытый урок закрывается.
 */
function LessonsPanel({courseSlug, module}) {
    const t = useAdminTranslation();

    const moduleId = getModuleId(module);

    const {
        lessons,
        loading,
        error,
        reordering,
        saving,
        reload,
        reorderLessons,
        toggleLessonStatus,
        deleteLesson,
    } = useModuleLessons(courseSlug, moduleId);

    const {message, showMessage} = useToast();

    const [selectedLesson, setSelectedLesson] = useState(null);

    // редактор урока: null — закрыт, lesson — правка существующего,
    // {mode: "create"} — создание нового
    const [editor, setEditor] = useState(null);

    // урок, который собираются удалить
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleting, setDeleting] = useState(false);

    // урок сохранён: обновляем список и показываем результат
    const handleSaved = useCallback(async () => {
        const wasCreated = editor?.mode === "create";

        setEditor(null);

        await reload();

        showMessage(
            "success",
            wasCreated ? t("adminLessonsCreated") : t("adminLessonsSaved")
        );
    }, [editor, reload, showMessage, t]);

    const handleDrop = useCallback(async (fromIndex, toIndex) => {
        const reordered = [...lessons];
        const [moved] = reordered.splice(fromIndex, 1);

        reordered.splice(toIndex, 0, moved);

        try {
            await reorderLessons(reordered);

            showMessage("success", t("adminLessonsReordered"));
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("adminLessonsReorderError")));
        }
    }, [lessons, reorderLessons, showMessage, t]);

    const {dragIndex, dragOverIndex, getDragProps} = useDragReorder(handleDrop);

    // публикация урока: состояние меняется тем же PATCH, что и в редакторе
    const handleToggleStatus = async (lesson) => {
        try {
            await toggleLessonStatus(lesson);

            showMessage(
                "success",
                lesson.is_published
                    ? t("adminLessonsUnpublished")
                    : t("adminLessonsPublishedToast")
            );
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("adminLessonsStatusError")));
        }
    };

    const performDelete = async () => {
        if (!deleteTarget) {
            return;
        }

        setDeleting(true);

        try {
            await deleteLesson(deleteTarget);

            setDeleteTarget(null);

            showMessage("success", t("adminLessonsDeleted"));
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("adminLessonsDeleteError")));
        } finally {
            setDeleting(false);
        }
    };

    return (
        <section className={pageStyles.panel}>
            <div className={pageStyles.panelHeader}>
                <div>
                    <h2>{t("adminLessonsTitle")}</h2>
                    <p>
                        {module
                            ? module.title
                            : t("adminLessonsHint")}
                    </p>
                </div>

                <button
                    type="button"
                    className={pageStyles.primaryButton}
                    onClick={() => setEditor({mode: "create"})}
                    disabled={!module}
                >
                    <Plus/>
                    <span>{t("adminLessonsCreate")}</span>
                </button>
            </div>

            <AdminToast message={message}/>

            {!module && (
                <EmptyState
                    icon={BookOpen}
                    title={t("adminLessonsSelectModuleTitle")}
                    description={t("adminLessonsSelectModuleDescription")}
                />
            )}

            {module && (
                <LessonsTable
                    lessons={lessons}
                    loading={loading}
                    error={error}
                    reordering={reordering}
                    saving={saving}
                    dragIndex={dragIndex}
                    dragOverIndex={dragOverIndex}
                    getDragProps={getDragProps}
                    onRetry={reload}
                    onEdit={(lesson) => setEditor({mode: "edit", lesson})}
                    onToggleStatus={handleToggleStatus}
                    onOpen={setSelectedLesson}
                    onDelete={setDeleteTarget}
                />
            )}

            {selectedLesson && (
                <LessonContentModal
                    key={selectedLesson.lesson_id}
                    courseSlug={courseSlug}
                    moduleId={moduleId}
                    lesson={selectedLesson}
                    onClose={() => setSelectedLesson(null)}
                    onEdit={() => {
                        setSelectedLesson(null);
                        setEditor({mode: "edit", lesson: selectedLesson});
                    }}
                />
            )}

            {editor && (
                <LessonEditor
                    key={editor.mode === "create" ? "create" : editor.lesson.lesson_id}
                    courseSlug={courseSlug}
                    moduleId={moduleId}
                    lesson={editor.mode === "create" ? null : editor.lesson}
                    onClose={() => setEditor(null)}
                    onSaved={handleSaved}
                />
            )}

            {deleteTarget && (
                <ConfirmModal
                    title={t("confirmDeleteLessonTitle")}
                    description={deleteTarget.title}
                    confirmText={t("confirmDeleteButton")}
                    busyText={t("confirmDeleteProcess")}
                    cancelText={t("confirmCancelButton")}
                    busy={deleting}
                    onConfirm={performDelete}
                    onClose={() => setDeleteTarget(null)}
                />
            )}
        </section>
    );
}

export default LessonsPanel;
