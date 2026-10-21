import {useCallback, useMemo, useState} from "react";
import {ShieldCheck, TriangleAlert} from "lucide-react";
import {getApiErrorMessage} from "@/services/apiError.js";
import {uploadCourseImage} from "@/api/media.js";
import {getLocalizedErrorMessage} from "@/hooks/useFileUpload.js";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import AdminPageHeader from "@/pages/Admin/components/AdminPageHeader.jsx";
import AdminToast from "@/pages/Admin/components/AdminToast.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminAccess} from "@/pages/Admin/hooks/useAdminAccess.js";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {useDragReorder} from "@/pages/Admin/hooks/useDragReorder.js";
import {useToast} from "@/pages/Admin/hooks/useToast.js";
import LessonsPanel from "@/pages/Admin/Lessons/LessonsPanel.jsx";
import CourseCoverModal from "./CourseCoverModal.jsx";
import CourseFormModal from "./CourseFormModal.jsx";
import CoursesTable from "./CoursesTable.jsx";
import ModuleFormModal from "./ModuleFormModal.jsx";
import ModulesTable from "./ModulesTable.jsx";
import {useCourseModules} from "./useCourseModules.js";
import {useCourses} from "./useCourses.js";
import {getModuleId} from "@/pages/Admin/utils/getModuleId.js";

/**
 * Управление курсами и модулями.
 *
 * Страница хранит только выбранный курс/модуль и состояние модальных
 * окон. Загрузка и изменение данных — в useCourses и useCourseModules,
 * отрисовка списков — в таблицах, уроки — в LessonsPanel.
 */
function AdminCourses() {
    const t = useAdminTranslation();

    const {message, showMessage} = useToast();

    const {
        courses,
        page,
        totalPages,
        loading: coursesLoading,
        error,
        saving: coursesSaving,
        reload: reloadCourses,
        goToPreviousPage,
        goToNextPage,
        createCourse,
        updateCourse,
        deleteCourse,
        toggleCourseStatus,
    } = useCourses();

    const [selectedCourseSlug, setSelectedCourseSlug] = useState("");
    const [selectedModuleId, setSelectedModuleId] = useState(null);

    const {
        modules,
        loading: modulesLoading,
        error: modulesError,
        reordering,
        saving: modulesSaving,
        reload: reloadModules,
        createModule,
        updateModule,
        deleteModule,
        toggleModuleStatus,
        reorderModules,
    } = useCourseModules(selectedCourseSlug);

    const [courseModal, setCourseModal] = useState(null);
    const [moduleModal, setModuleModal] = useState(null);
    const [deleteTarget, setDeleteTarget] = useState(null);

    // курс, у которого открыта обложка
    const [coverCourse, setCoverCourse] = useState(null);

    const {authLoading, isForbidden} = useAdminAccess(error);

    // при смене курса выбранный модуль сбрасывается:
    // уроки другого курса показывать нельзя
    const selectCourse = useCallback((courseSlug) => {
        setSelectedCourseSlug(courseSlug);
        setSelectedModuleId(null);
    }, []);

    const selectModule = useCallback((module) => {
        setSelectedModuleId(getModuleId(module));
    }, []);

    // выбранный модуль берём из загруженного списка: после смены
    // курса или удаления модуля выделение сбрасывается само
    const selectedModule = useMemo(
        () => modules.find((module) => getModuleId(module) === selectedModuleId) || null,
        [modules, selectedModuleId]
    );

    /* ---------- курсы ---------- */

    const openCreateCourse = () => {
        setCourseModal({
            mode: "create",
            course: {title: "", slug: "", description: "", is_active: false},
        });
    };

    const openEditCourse = (course) => {
        setCourseModal({
            mode: "edit",
            originalSlug: course.slug,
            course: {
                title: course.title || "",
                slug: course.slug || "",
                description: course.description || "",
                is_active: !!course.is_active,
            },
        });
    };

    const submitCourse = async (payload, coverFile) => {
        if (!courseModal) {
            return;
        }

        const isCreate = courseModal.mode === "create";

        let saved;

        try {
            saved = isCreate
                ? await createCourse(payload)
                : await updateCourse(courseModal.originalSlug, payload);
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("courseSaveError")));
            return;
        }

        // Обложка уходит отдельным запросом уже после сохранения курса:
        // у нового курса до этого нет slug, по которому её примет сервер.
        // У изменённого курса берём slug из ответа — он мог поменяться.
        if (coverFile) {
            const coverSlug = saved?.slug || payload.slug || courseModal.originalSlug;

            try {
                await uploadCourseImage(coverSlug, coverFile);

                // в списке появится ссылка на сохранённую обложку
                await reloadCourses();
            } catch (requestError) {
                showMessage(
                    "error",
                    getLocalizedErrorMessage(requestError, t, t("coverUploadError"))
                );

                // курс уже сохранён — окно закрываем, обложку можно
                // загрузить повторно через отдельное окно обложки
                setCourseModal(null);

                return;
            }
        }

        showMessage("success", isCreate ? t("courseCreated") : t("courseUpdated"));

        setCourseModal(null);
    };

    const handleToggleCourseStatus = async (course) => {
        try {
            await toggleCourseStatus(course);

            showMessage(
                "success",
                course.is_active ? t("courseDeactivated") : t("courseActivated")
            );
        } catch (requestError) {
            showMessage(
                "error",
                getApiErrorMessage(requestError, t("courseStatusError"))
            );
        }
    };

    /* ---------- модули ---------- */

    const openCreateModule = () => {
        if (!selectedCourseSlug) {
            return;
        }

        setModuleModal({
            mode: "create",
            module: {title: "", description: "", is_active: false},
        });
    };

    const openEditModule = (module) => {
        setModuleModal({
            mode: "edit",
            originalId: getModuleId(module),
            module: {
                title: module.title || "",
                description: module.description || "",
                is_active: !!module.is_active,
            },
        });
    };

    const submitModule = async (payload) => {
        if (!moduleModal) {
            return;
        }

        try {
            if (moduleModal.mode === "create") {
                await createModule(payload);
                showMessage("success", t("moduleCreated"));
            } else {
                await updateModule(moduleModal.originalId, payload);
                showMessage("success", t("moduleUpdated"));
            }

            setModuleModal(null);
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("moduleSaveError")));
        }
    };

    const handleToggleModuleStatus = async (module) => {
        try {
            await toggleModuleStatus(module);

            showMessage(
                "success",
                module.is_active ? t("moduleDeactivated") : t("moduleActivated")
            );
        } catch (requestError) {
            showMessage(
                "error",
                getApiErrorMessage(requestError, t("moduleStatusError"))
            );
        }
    };

    const handleModuleDrop = useCallback(async (fromIndex, toIndex) => {
        const reordered = [...modules];
        const [moved] = reordered.splice(fromIndex, 1);

        reordered.splice(toIndex, 0, moved);

        try {
            await reorderModules(reordered);

            showMessage("success", t("modulesReordered"));
        } catch (requestError) {
            showMessage(
                "error",
                getApiErrorMessage(requestError, t("modulesReorderError"))
            );
        }
    }, [modules, reorderModules, showMessage, t]);

    const {dragIndex, dragOverIndex, getDragProps} = useDragReorder(handleModuleDrop);

    /* ---------- удаление ---------- */

    const closeDelete = () => setDeleteTarget(null);

    const performDelete = async () => {
        if (!deleteTarget) {
            return;
        }

        try {
            if (deleteTarget.type === "course") {
                const deletedSlug = deleteTarget.target.slug;

                await deleteCourse(deleteTarget.target);

                showMessage("success", t("courseDeleted"));

                if (selectedCourseSlug === deletedSlug) {
                    selectCourse("");
                }
            } else {
                await deleteModule(deleteTarget.target);

                showMessage("success", t("moduleDeleted"));

                // счётчики модулей и уроков в списке курсов тоже изменились
                await reloadCourses();
            }

            setDeleteTarget(null);
        } catch (requestError) {
            showMessage("error", getApiErrorMessage(requestError, t("deleteError")));
        }
    };

    const forbiddenState = (
        <main className={pageStyles.page}>
            <EmptyState
                icon={ShieldCheck}
                title={t("forbiddenTitle")}
                description={t("forbiddenDescription")}
            />
        </main>
    );

    if (isForbidden) {
        return forbiddenState;
    }

    if (error) {
        return (
            <main className={pageStyles.page}>
                <EmptyState
                    icon={TriangleAlert}
                    title={t("errorTitle")}
                    description={t("errorDescription")}
                    action={
                        <button
                            type="button"
                            className={pageStyles.retryButton}
                            onClick={reloadCourses}
                        >
                            {t("errorRetry")}
                        </button>
                    }
                />
            </main>
        );
    }

    const pending = authLoading || coursesLoading;

    return (
        <div className={pageStyles.page}>
            <AdminPageHeader
                eyebrow={t("coursesEyebrow")}
                title={t("coursesTitle")}
                subtitle={t("coursesSubtitle")}
                onRefresh={reloadCourses}
                refreshing={pending}
                refreshLabel={t("refreshButton")}
                refreshingLabel={t("refreshProcess")}
            />

            <AdminToast message={message}/>

            <CoursesTable
                courses={courses}
                page={page}
                totalPages={totalPages}
                loading={pending}
                saving={coursesSaving}
                onSelectCourse={selectCourse}
                onCreateCourse={openCreateCourse}
                onOpenCover={setCoverCourse}
                onEditCourse={openEditCourse}
                onToggleStatus={handleToggleCourseStatus}
                onDeleteCourse={(course) => setDeleteTarget({type: "course", target: course})}
                onPreviousPage={goToPreviousPage}
                onNextPage={goToNextPage}
            />

            <ModulesTable
                courses={courses}
                selectedCourseSlug={selectedCourseSlug}
                selectedModuleId={selectedModuleId}
                modules={modules}
                loading={modulesLoading}
                error={modulesError}
                reordering={reordering}
                saving={modulesSaving}
                dragIndex={dragIndex}
                dragOverIndex={dragOverIndex}
                getDragProps={getDragProps}
                onSelectCourse={selectCourse}
                onCreateModule={openCreateModule}
                onRetry={reloadModules}
                onSelectModule={selectModule}
                onEditModule={openEditModule}
                onToggleStatus={handleToggleModuleStatus}
                onDeleteModule={(module) => setDeleteTarget({type: "module", target: module})}
            />

            <LessonsPanel
                key={`${selectedCourseSlug}:${selectedModuleId}`}
                courseSlug={selectedCourseSlug}
                module={selectedModule}
            />

            {/* ---------- course modal ---------- */}

            {courseModal && (
                <CourseFormModal
                    key={`${courseModal.mode}:${courseModal.originalSlug ?? ""}`}
                    mode={courseModal.mode}
                    course={courseModal.course}
                    saving={coursesSaving}
                    onClose={() => setCourseModal(null)}
                    onSubmit={submitCourse}
                    onError={(text) => showMessage("error", text)}
                />
            )}

            {/* ---------- module modal ---------- */}

            {moduleModal && (
                <ModuleFormModal
                    key={`${moduleModal.mode}:${moduleModal.originalId ?? ""}`}
                    mode={moduleModal.mode}
                    module={moduleModal.module}
                    saving={modulesSaving}
                    onClose={() => setModuleModal(null)}
                    onSubmit={submitModule}
                    onError={(text) => showMessage("error", text)}
                />
            )}

            {/* ---------- delete confirm ---------- */}

            {deleteTarget && (
                <ConfirmModal
                    title={deleteTarget.type === "course"
                        ? t("confirmDeleteCourseTitle")
                        : t("confirmDeleteModuleTitle")}
                    description={deleteTarget.target.title}
                    confirmText={t("confirmDeleteButton")}
                    busyText={t("confirmDeleteProcess")}
                    cancelText={t("confirmCancelButton")}
                    busy={coursesSaving || modulesSaving}
                    onConfirm={performDelete}
                    onClose={closeDelete}
                />
            )}

            {/* ---------- cover ---------- */}

            {coverCourse && (
                <CourseCoverModal
                    key={coverCourse.slug}
                    course={coverCourse}
                    onClose={() => setCoverCourse(null)}
                    onSaved={async () => {
                        setCoverCourse(null);

                        await reloadCourses();
                    }}
                />
            )}
        </div>
    );
}

export default AdminCourses;
