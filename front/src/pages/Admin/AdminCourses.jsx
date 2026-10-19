import {useCallback, useEffect, useMemo, useState} from "react";
import {
    BookOpen,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    Pencil,
    Plus,
    Power,
    RefreshCw,
    ShieldCheck,
    Trash2,
    TriangleAlert,
    X,
} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {useAuth} from "@/context/AuthContext.jsx";
import {getTranslation} from "@/locales/i18n.js";
import {formatNumber} from "@/services/format.js";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import styles from "./adminCourses.module.css";
import modalStyles from "./userModal.module.css";

const language = "ru";
const PER_PAGE = 10;

function AdminCourses() {
    const {user, loading: authLoading} = useAuth();
    const t = (key, params) => getTranslation(`admin.admin.${key}`, language, params);

    const [courses, setCourses] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [selectedCourseSlug, setSelectedCourseSlug] = useState("");
    const [modules, setModules] = useState([]);
    const [modulesLoading, setModulesLoading] = useState(false);
    const [modulesError, setModulesError] = useState(null);

    const [message, setMessage] = useState(null);

    const [courseModal, setCourseModal] = useState(null);
    const [moduleModal, setModuleModal] = useState(null);
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [reordering, setReordering] = useState(false);

    const [saving, setSaving] = useState(false);

    const showMessage = (type, text) => {
        setMessage({type, text});
        window.setTimeout(() => setMessage(null), 4000);
    };

    const fetchCourses = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_COURSES, {
                params: {page, page_size: PER_PAGE},
            });

            const list = data.courses ?? [];
            setCourses(list);
            setTotalPages(data.total_pages ?? 1);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [page]);

    const fetchModules = useCallback(async (courseSlug) => {
        if (!courseSlug) {
            setModules([]);
            return;
        }

        setModulesError(null);
        setModulesLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_COURSE_MODULES(courseSlug), {
                params: {page: 1, page_size: 100},
            });

            setModules(data.modules ?? []);
        } catch (requestError) {
            setModulesError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setModulesLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchCourses();
    }, [fetchCourses]);

    useEffect(() => {
        if (!selectedCourseSlug) {
            setModules([]);
            return;
        }

        fetchModules(selectedCourseSlug);
    }, [selectedCourseSlug, fetchModules]);

    const handleNextPage = () => {
        setPage((current) => Math.min(totalPages, current + 1));
    };

    const handlePreviousPage = () => {
        setPage((current) => Math.max(1, current - 1));
    };

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

    const closeCourseModal = () => setCourseModal(null);

    const submitCourse = async (event) => {
        event.preventDefault();
        if (!courseModal) return;

        const {mode, originalSlug, course} = courseModal;

        setSaving(true);

        const title = course.title.trim();
        const slug = course.slug.trim();
        const description = course.description.trim();

        if (!title || title.length > 255) {
            showMessage("error", "Название курса обязательно и не длиннее 255 символов");
            setSaving(false);
            return;
        }

        if (slug && (slug.length > 255 || !/^[a-z0-9-]+$/.test(slug))) {
            showMessage("error", "Slug: только латиница, цифры и дефис, до 255 символов");
            setSaving(false);
            return;
        }

        if (description.length > 2000) {
            showMessage("error", "Описание не длиннее 2000 символов");
            setSaving(false);
            return;
        }

        try {
            const payload = {
                title,
                slug: slug || null,
                description: description || null,
                is_active: course.is_active,
            };

            if (mode === "create") {
                await api.post(API_ROUTES.ADMIN_COURSES, payload);
                showMessage("success", "Курс создан");
            } else {
                await api.patch(API_ROUTES.ADMIN_COURSE_BY_ID(originalSlug), payload);
                showMessage("success", "Курс обновлён");
            }

            closeCourseModal();
            await fetchCourses();
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось сохранить курс";

            showMessage("error", messageText);
        } finally {
            setSaving(false);
        }
    };

    const toggleCourseStatus = async (course) => {
        setSaving(true);

        try {
            if (course.is_active) {
                await api.post(API_ROUTES.ADMIN_COURSE_DEACTIVATE(course.slug));
                showMessage("success", "Курс деактивирован");
            } else {
                await api.post(API_ROUTES.ADMIN_COURSE_ACTIVATE(course.slug));
                showMessage("success", "Курс активирован");
            }

            await fetchCourses();
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось изменить статус курса";

            showMessage("error", messageText);
        } finally {
            setSaving(false);
        }
    };

    const confirmDeleteCourse = (course) => {
        setDeleteTarget({type: "course", target: course});
    };

    const confirmDeleteModule = (module) => {
        setDeleteTarget({type: "module", target: module});
    };

    const closeDelete = () => setDeleteTarget(null);

    const performDelete = async () => {
        if (!deleteTarget) return;

        setSaving(true);

        try {
            if (deleteTarget.type === "course") {
                await api.delete(API_ROUTES.ADMIN_COURSE_BY_ID(deleteTarget.target.slug));
                showMessage("success", "Курс удалён");

                if (selectedCourseSlug === deleteTarget.target.slug) {
                    setSelectedCourseSlug("");
                }
            } else {
                await api.delete(API_ROUTES.ADMIN_MODULE_BY_ID(deleteTarget.target.id || deleteTarget.target.module_id));
                showMessage("success", "Модуль удалён");
            }

            closeDelete();
            await fetchCourses();

            if (deleteTarget.type === "module") {
                await fetchModules(selectedCourseSlug);
            }
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось удалить";

            showMessage("error", messageText);
        } finally {
            setSaving(false);
        }
    };

    const openCreateModule = () => {
        if (!selectedCourseSlug) return;

        setModuleModal({
            mode: "create",
            module: {title: "", description: "", is_active: false},
        });
    };

    const openEditModule = (module) => {
        setModuleModal({
            mode: "edit",
            originalId: module.id || module.module_id,
            module: {
                title: module.title || "",
                description: module.description || "",
                is_active: !!module.is_active,
            },
        });
    };

    const closeModuleModal = () => setModuleModal(null);

    const submitModule = async (event) => {
        event.preventDefault();
        if (!moduleModal) return;

        const {mode, originalId, module} = moduleModal;

        setSaving(true);

        const title = module.title.trim();
        const description = module.description.trim();

        if (!title || title.length > 255) {
            showMessage("error", "Название модуля обязательно и не длиннее 255 символов");
            setSaving(false);
            return;
        }

        if (description.length > 2000) {
            showMessage("error", "Описание не длиннее 2000 символов");
            setSaving(false);
            return;
        }

        try {
            const payload = {
                title,
                description: description || null,
                is_active: module.is_active,
            };

            if (mode === "create") {
                await api.post(API_ROUTES.ADMIN_COURSE_MODULES(selectedCourseSlug), payload);
                showMessage("success", "Модуль создан");
            } else {
                await api.patch(API_ROUTES.ADMIN_MODULE_BY_ID(originalId), payload);
                showMessage("success", "Модуль обновлён");
            }

            closeModuleModal();
            await fetchModules(selectedCourseSlug);
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось сохранить модуль";

            showMessage("error", messageText);
        } finally {
            setSaving(false);
        }
    };

    // перетаскивание модулей: меняем локальный порядок и сохраняем одним запросом
    const [dragIndex, setDragIndex] = useState(null);
    const [dragOverIndex, setDragOverIndex] = useState(null);

    const handleDragStart = (index) => () => {
        setDragIndex(index);
    };

    const handleDragOver = (index) => (event) => {
        event.preventDefault();
        if (dragIndex === null || dragIndex === index) return;
        setDragOverIndex(index);
    };

    const handleDrop = async (index) => {
        if (dragIndex === null || dragIndex === index) {
            setDragIndex(null);
            setDragOverIndex(null);
            return;
        }

        const reordered = [...modules];
        const [moved] = reordered.splice(dragIndex, 1);
        reordered.splice(index, 0, moved);

        setModules(reordered);
        setDragIndex(null);
        setDragOverIndex(null);

        setReordering(true);

        try {
            await api.put(API_ROUTES.ADMIN_COURSE_MODULES_REORDER(selectedCourseSlug), {
                module_ids: reordered.map((module) => module.id || module.module_id),
            });

            await fetchModules(selectedCourseSlug);
            showMessage("success", "Порядок модулей обновлён");
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось изменить порядок модулей";

            showMessage("error", messageText);

            await fetchModules(selectedCourseSlug);
        } finally {
            setReordering(false);
        }
    };

    const handleDragEnd = () => {
        setDragIndex(null);
        setDragOverIndex(null);
    };

    const toggleModuleStatus = async (module) => {
        const moduleId = module.id || module.module_id;

        setSaving(true);

        try {
            if (module.is_active) {
                await api.post(API_ROUTES.ADMIN_MODULE_DEACTIVATE(moduleId));
                showMessage("success", "Модуль деактивирован");
            } else {
                await api.post(API_ROUTES.ADMIN_MODULE_ACTIVATE(moduleId));
                showMessage("success", "Модуль активирован");
            }

            await fetchModules(selectedCourseSlug);
        } catch (requestError) {
            const messageText =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                "Не удалось изменить статус модуля";

            showMessage("error", messageText);
        } finally {
            setSaving(false);
        }
    };

    const forbiddenState = (
        <main className={styles.users}>
            <EmptyState
                icon={ShieldCheck}
                title={t("forbiddenTitle")}
                description={t("forbiddenDescription")}
            />
        </main>
    );

    const selectedCourse = useMemo(
        () => courses.find((course) => course.slug === selectedCourseSlug) || null,
        [courses, selectedCourseSlug]
    );

    if (error === "forbidden" || (!authLoading && !user?.is_admin)) {
        return forbiddenState;
    }

    if (error) {
        return (
            <main className={styles.users}>
                <EmptyState
                    icon={TriangleAlert}
                    title={t("errorTitle")}
                    description={t("errorDescription")}
                    action={
                        <button type="button" className={styles.retryButton} onClick={fetchCourses}>
                            {t("errorRetry")}
                        </button>
                    }
                />
            </main>
        );
    }

    const pending = authLoading || loading;

    return (
        <div className={styles.users}>

            {/* ---------- heading ---------- */}

            <section className={styles.heading}>
                <div className={styles.badge}>
                    <span className={styles.badgeDot}/>
                    Курсы и модули
                </div>

                <div className={styles.headingRow}>
                    <div className={styles.headingContent}>
                        <h1>Управление курсами</h1>
                        <p>Создание, редактирование, удаление и статусы курсов и модулей</p>
                    </div>

                    <button
                        type="button"
                        className={styles.refreshButton}
                        onClick={fetchCourses}
                        disabled={pending}
                    >
                        <RefreshCw/>
                        <span>{pending ? t("refreshProcess") : t("refreshButton")}</span>
                    </button>
                </div>
            </section>

            {/* ---------- toast ---------- */}

            {message && (
                <div className={styles.toast} data-tone={message.type}>
                    {message.type === "success" ? <CheckCircle2/> : <TriangleAlert/>}
                    <span>{message.text}</span>
                </div>
            )}

            {/* ---------- courses ---------- */}

            <section className={styles.panel}>
                <div className={styles.panelHeader}>
                    <div>
                        <h2>Курсы</h2>
                        <p>Выберите курс, чтобы управлять его модулями</p>
                    </div>

                    <button type="button" className={styles.primaryButton} onClick={openCreateCourse}>
                        <Plus/>
                        <span>Создать курс</span>
                    </button>
                </div>

                {pending && (
                    <div className={styles.tableWrap}>
                        <table className={styles.table} aria-busy="true">
                            <thead>
                            <tr>
                                <th>Название</th>
                                <th>Slug</th>
                                <th>Статус</th>
                                <th data-align="right">Действия</th>
                            </tr>
                            </thead>
                            <tbody>
                            {Array.from({length: PER_PAGE}, (_, index) => (
                                <tr className={styles.row} key={index}>
                                    <td><span className={styles.skeletonCell} data-width="60%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="40%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="30%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="50%"/></td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {!pending && courses.length === 0 && (
                    <EmptyState
                        icon={BookOpen}
                        title="Курсы не найдены"
                        description="Создайте первый курс"
                    />
                )}

                {!pending && courses.length > 0 && (
                    <div className={styles.tableWrap}>
                        <table className={styles.table}>
                            <thead>
                            <tr>
                                <th>Название</th>
                                <th>Slug</th>
                                <th>Статус</th>
                                <th data-align="right">Действия</th>
                            </tr>
                            </thead>
                            <tbody>
                            {courses.map((course) => (
                                <tr
                                    className={styles.row}
                                    key={course.slug}
                                    onClick={() => setSelectedCourseSlug(course.slug)}
                                    tabIndex={0}
                                    role="button"
                                    aria-label={course.title}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter") {
                                            setSelectedCourseSlug(course.slug);
                                        }
                                    }}
                                >
                                    <td>
                                        <div className={styles.courseCell}>
                                            <span className={styles.courseIcon}>
                                                <BookOpen/>
                                            </span>

                                            <div className={styles.courseMeta}>
                                                <strong>{course.title}</strong>
                                                {course.description && (
                                                    <span>{course.description}</span>
                                                )}
                                            </div>
                                        </div>
                                    </td>

                                    <td className={styles.cellMuted}>{course.slug}</td>

                                    <td>
                                        <Badge tone={course.is_active ? "focus" : "muted"}>
                                            {course.is_active ? "Активен" : "Неактивен"}
                                        </Badge>
                                    </td>

                                    <td data-align="right">
                                        <div className={styles.actions}>
                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                onClick={(event) => {
                                                    event.stopPropagation();
                                                    openEditCourse(course);
                                                }}
                                                title="Редактировать"
                                            >
                                                <Pencil/>
                                            </button>

                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                onClick={(event) => {
                                                    event.stopPropagation();
                                                    toggleCourseStatus(course);
                                                }}
                                                title={course.is_active ? "Деактивировать" : "Активировать"}
                                                disabled={saving}
                                            >
                                                <Power/>
                                            </button>

                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                data-tone="danger"
                                                onClick={(event) => {
                                                    event.stopPropagation();
                                                    confirmDeleteCourse(course);
                                                }}
                                                title="Удалить"
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

                {!pending && totalPages > 1 && (
                    <nav className={styles.pagination}>
                        <button
                            type="button"
                            className={styles.pageButton}
                            onClick={handlePreviousPage}
                            disabled={page <= 1}
                            aria-label="Назад"
                        >
                            ‹
                        </button>

                        <div className={styles.pageInfo}>
                            {t("paginationInfo", {
                                page: formatNumber(page),
                                total: formatNumber(totalPages),
                            })}
                        </div>

                        <button
                            type="button"
                            className={styles.pageButton}
                            onClick={handleNextPage}
                            disabled={page >= totalPages}
                            aria-label="Вперёд"
                        >
                            ›
                        </button>
                    </nav>
                )}
            </section>

            {/* ---------- modules ---------- */}

            <section className={styles.panel}>
                <div className={styles.panelHeader}>
                    <div>
                        <h2>Модули</h2>
                        <p>
                            {selectedCourse
                                ? ` `
                                : "Выберите курс из списка выше"}
                        </p>
                    </div>

                    <div className={styles.moduleToolbar}>
                        <select
                            className={styles.select}
                            value={selectedCourseSlug}
                            onChange={(event) => setSelectedCourseSlug(event.target.value)}
                        >
                            <option value="">Выберите курс</option>
                            {courses.map((course) => (
                                <option key={course.slug} value={course.slug}>
                                    {course.title}
                                </option>
                            ))}
                        </select>

                        <button
                            type="button"
                            className={styles.primaryButton}
                            onClick={openCreateModule}
                            disabled={!selectedCourseSlug}
                        >
                            <Plus/>
                            <span>Создать модуль</span>
                        </button>
                    </div>
                </div>

                {modulesLoading && (
                    <div className={styles.tableWrap}>
                        <table className={styles.table} aria-busy="true">
                            <thead>
                            <tr>
                                <th>Название</th>
                                <th>Позиция</th>
                                <th>Статус</th>
                                <th data-align="right">Действия</th>
                            </tr>
                            </thead>
                            <tbody>
                            {Array.from({length: 5}, (_, index) => (
                                <tr className={styles.row} key={index}>
                                    <td><span className={styles.skeletonCell} data-width="60%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="20%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="30%"/></td>
                                    <td><span className={styles.skeletonCell} data-width="50%"/></td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {!modulesLoading && modulesError && (
                    <EmptyState
                        icon={TriangleAlert}
                        title={t("errorTitle")}
                        description={t("errorDescription")}
                        action={
                            <button
                                type="button"
                                className={styles.retryButton}
                                onClick={() => fetchModules(selectedCourseSlug)}
                            >
                                {t("errorRetry")}
                            </button>
                        }
                    />
                )}

                {!modulesLoading && !modulesError && selectedCourseSlug && modules.length === 0 && (
                    <EmptyState
                        icon={BookOpen}
                        title="Модули не найдены"
                        description="Создайте первый модуль для выбранного курса"
                    />
                )}

                {!modulesLoading && !modulesError && selectedCourseSlug && modules.length > 0 && (
                    <div className={styles.tableWrap}>
                        {reordering && (
                            <div className={styles.reorderHint}>
                                Сохраняем новый порядок…
                            </div>
                        )}

                        <table className={styles.table}>
                            <thead>
                            <tr>
                                <th>Название</th>
                                <th>Позиция</th>
                                <th>Статус</th>
                                <th data-align="right">Действия</th>
                            </tr>
                            </thead>
                            <tbody>
                            {modules.map((module, index) => (
                                <tr
                                    className={
                                        `${styles.row}` +
                                        (dragIndex === index ? ` ${styles.rowDragging}` : "") +
                                        (dragOverIndex === index ? ` ${styles.rowDropTarget}` : "")
                                    }
                                    key={module.id || module.module_id}
                                    draggable={!reordering}
                                    onDragStart={handleDragStart(index)}
                                    onDragOver={handleDragOver(index)}
                                    onDrop={() => handleDrop(index)}
                                    onDragEnd={handleDragEnd}
                                >
                                    <td>
                                        <div className={styles.moduleCell}>
                                            <span className={styles.dragHandle} aria-hidden="true">
                                                ⋮⋮
                                            </span>

                                            <div className={styles.moduleMeta}>
                                                <strong>{module.title}</strong>
                                                {module.description && (
                                                    <span>{module.description}</span>
                                                )}
                                            </div>
                                        </div>
                                    </td>

                                    <td>
                                        <span className={styles.positionBadge}>
                                            {index + 1}
                                        </span>
                                    </td>

                                    <td>
                                        <Badge tone={module.is_active ? "focus" : "muted"}>
                                            {module.is_active ? "Активен" : "Неактивен"}
                                        </Badge>
                                    </td>

                                    <td data-align="right">
                                        <div className={styles.actions}>
                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                onClick={() => openEditModule(module)}
                                                title="Редактировать"
                                            >
                                                <Pencil/>
                                            </button>

                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                onClick={() => toggleModuleStatus(module)}
                                                title={module.is_active ? "Деактивировать" : "Активировать"}
                                                disabled={saving}
                                            >
                                                <Power/>
                                            </button>

                                            <button
                                                type="button"
                                                className={styles.actionButton}
                                                data-tone="danger"
                                                onClick={() => confirmDeleteModule(module)}
                                                title="Удалить"
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

                {!selectedCourseSlug && (
                    <EmptyState
                        icon={BookOpen}
                        title="Выберите курс"
                        description="Сначала выберите курс из списка выше"
                    />
                )}
            </section>

            {/* ---------- course modal ---------- */}

            {courseModal && (
                <div className={modalStyles.overlay} onClick={closeCourseModal} role="presentation">
                    <div className={modalStyles.modal} onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" style={{maxWidth: 640}}>
                        <button type="button" className={modalStyles.close} onClick={closeCourseModal} aria-label="Закрыть">
                            <X/>
                        </button>

                        <h2 className={styles.modalTitle}>
                            {courseModal.mode === "create" ? "Создать курс" : "Редактировать курс"}
                        </h2>

                        <form onSubmit={submitCourse} className={styles.form}>
                            <label className={styles.field}>
                                <span>Название (до 255 символов)</span>
                                <input
                                    required
                                    maxLength={255}
                                    value={courseModal.course.title}
                                    onChange={(event) =>
                                        setCourseModal((current) => ({
                                            ...current,
                                            course: {...current.course, title: event.target.value},
                                        }))
                                    }
                                />
                            </label>

                            <label className={styles.field}>
                                <span>Slug (до 255 символов, необязательно)</span>
                                <input
                                    maxLength={255}
                                    value={courseModal.course.slug}
                                    onChange={(event) =>
                                        setCourseModal((current) => ({
                                            ...current,
                                            course: {...current.course, slug: event.target.value},
                                        }))
                                    }
                                />
                            </label>

                            <label className={styles.field}>
                                <span>Описание (до 2000 символов)</span>
                                <textarea
                                    maxLength={2000}
                                    value={courseModal.course.description}
                                    onChange={(event) =>
                                        setCourseModal((current) => ({
                                            ...current,
                                            course: {...current.course, description: event.target.value},
                                        }))
                                    }
                                    rows={4}
                                />
                            </label>

                            <label className={styles.checkboxField}>
                                <input
                                    type="checkbox"
                                    checked={courseModal.course.is_active}
                                    onChange={(event) =>
                                        setCourseModal((current) => ({
                                            ...current,
                                            course: {...current.course, is_active: event.target.checked},
                                        }))
                                    }
                                />
                                <span>Активен</span>
                            </label>

                            <div className={styles.formActions}>
                                <button
                                    type="button"
                                    className={styles.cancelButton}
                                    onClick={closeCourseModal}
                                    disabled={saving}
                                >
                                    Отмена
                                </button>

                                <button type="submit" className={styles.saveButton} disabled={saving}>
                                    {saving ? "Сохранение..." : "Сохранить"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ---------- module modal ---------- */}

            {moduleModal && (
                <div className={modalStyles.overlay} onClick={closeModuleModal} role="presentation">
                    <div className={modalStyles.modal} onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" style={{maxWidth: 640}}>
                        <button type="button" className={modalStyles.close} onClick={closeModuleModal} aria-label="Закрыть">
                            <X/>
                        </button>

                        <h2 className={styles.modalTitle}>
                            {moduleModal.mode === "create" ? "Создать модуль" : "Редактировать модуль"}
                        </h2>

                        <form onSubmit={submitModule} className={styles.form}>
                            <label className={styles.field}>
                                <span>Название (до 255 символов)</span>
                                <input
                                    required
                                    maxLength={255}
                                    value={moduleModal.module.title}
                                    onChange={(event) =>
                                        setModuleModal((current) => ({
                                            ...current,
                                            module: {...current.module, title: event.target.value},
                                        }))
                                    }
                                />
                            </label>

                            <label className={styles.field}>
                                <span>Описание (до 2000 символов)</span>
                                <textarea
                                    maxLength={2000}
                                    value={moduleModal.module.description}
                                    onChange={(event) =>
                                        setModuleModal((current) => ({
                                            ...current,
                                            module: {...current.module, description: event.target.value},
                                        }))
                                    }
                                    rows={4}
                                />
                            </label>

                            <label className={styles.checkboxField}>
                                <input
                                    type="checkbox"
                                    checked={moduleModal.module.is_active}
                                    onChange={(event) =>
                                        setModuleModal((current) => ({
                                            ...current,
                                            module: {...current.module, is_active: event.target.checked},
                                        }))
                                    }
                                />
                                <span>Активен</span>
                            </label>

                            <div className={styles.formActions}>
                                <button
                                    type="button"
                                    className={styles.cancelButton}
                                    onClick={closeModuleModal}
                                    disabled={saving}
                                >
                                    Отмена
                                </button>

                                <button type="submit" className={styles.saveButton} disabled={saving}>
                                    {saving ? "Сохранение..." : "Сохранить"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ---------- delete confirm ---------- */}

            {deleteTarget && (
                <div className={modalStyles.confirmOverlay} onClick={closeDelete} role="presentation">
                    <div className={modalStyles.confirm} onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
                        <span className={modalStyles.confirmIcon}>
                            <TriangleAlert/>
                        </span>

                        <h3>Удалить {deleteTarget.type === "course" ? "курс" : "модуль"}?</h3>
                        <p>{deleteTarget.target.title}</p>

                        <div className={modalStyles.confirmActions}>
                            <button
                                type="button"
                                className={modalStyles.confirmCancel}
                                onClick={closeDelete}
                                disabled={saving}
                            >
                                Отмена
                            </button>

                            <button
                                type="button"
                                className={modalStyles.confirmDanger}
                                onClick={performDelete}
                                disabled={saving}
                            >
                                {saving ? "Удаление..." : "Удалить"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminCourses;
export {AdminCourses as CoursesAdmin};