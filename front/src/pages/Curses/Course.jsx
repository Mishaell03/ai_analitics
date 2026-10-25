import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./course.module.css";
import {ArrowLeft, ArrowRight, BookOpen, CheckCircle2, ChevronLeft, ChevronRight, ExternalLink, ImageOff, Play, RefreshCw} from "lucide-react";
import {Link, useNavigate, useParams} from "react-router-dom";
import {useCallback, useEffect, useState,} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import Description from "@/components/Markdown/Description.jsx";

const PAGE_SIZE = 20;

export function Course() {
    const t = useTranslation("courses.course");
    const navigate = useNavigate();

    const {slug} = useParams();
    const [course, setCourse] = useState(null);
    const [modules, setModules] = useState([]);
    const [expandedModule, setExpandedModule] = useState(null);
    const [moduleLessons, setModuleLessons] = useState({});
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [enrolling, setEnrolling] = useState(false);
    const [showUnenrollModal, setShowUnenrollModal] = useState(false);
    const [learning, setLearning] = useState(null);
    const [learningLoading, setLearningLoading] = useState(false);
    const [learningError, setLearningError] = useState(false);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const fetchCourse = useCallback(async () => {
        setError(false);

        if (!course) {
            setLoading(true);
        }

        try {
            const {data} = await api.get(
                `${API_ROUTES.COURSES}/${slug}`,
                {
                    params: {
                        page,
                        page_size: PAGE_SIZE,
                    },
                }
            );

            if (data.course) {
                setCourse(data.course);
            }

            setModules(data.modules ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [slug, page]);

    const fetchLearning = useCallback(async () => {
        if (!slug) return;
        setLearningLoading(true);
        setLearningError(false);
        try {
            const {data} = await api.get(API_ROUTES.COURSE_NEXT_LESSON(slug));
            setLearning(data);
        } catch {
            setLearningError(true);
        } finally {
            setLearningLoading(false);
        }
    }, [slug]);

    const fetchModuleLessons = useCallback(async (moduleId, requestedPage = 1) => {
        setModuleLessons((current) => ({
            ...current,
            [moduleId]: {...current[moduleId], loading: true, error: false},
        }));
        try {
            const {data} = await api.get(API_ROUTES.COURSE_MODULE_LESSONS(slug, moduleId), {
                params: {page: requestedPage, page_size: 100},
            });
            setModuleLessons((current) => ({
                ...current,
                [moduleId]: {
                    lessons: data.lessons ?? [],
                    page: data.current_page ?? requestedPage,
                    totalPages: data.total_pages ?? 1,
                    loading: false,
                    error: false,
                },
            }));
        } catch {
            setModuleLessons((current) => ({
                ...current,
                [moduleId]: {...current[moduleId], loading: false, error: true},
            }));
        }
    }, [slug]);

    const toggleModule = (moduleId) => {
        if (!course?.is_enrolled) return;
        if (expandedModule === moduleId) {
            setExpandedModule(null);
            return;
        }
        setExpandedModule(moduleId);
        if (!moduleLessons[moduleId]) fetchModuleLessons(moduleId);
    };

    const handleEnroll = async () => {
        if (!slug || enrolling) return;

        setEnrolling(true);

        try {
            await api.post(
                API_ROUTES.ENROLL_COURSE_BY_ID(slug)
            );

            setCourse((current) =>
                current
                    ? {
                        ...current,
                        is_enrolled: true,
                    }
                    : current
            );
        } catch {
            setError(true);
        } finally {
            setEnrolling(false);
        }
    };

    const handleUnenroll = async () => {
        if (!slug || enrolling) return;

        setEnrolling(true);

        try {
            await api.delete(
                API_ROUTES.UNENROLL_COURSE_BY_ID(slug)
            );

            setCourse((current) =>
                current
                    ? {
                        ...current,
                        is_enrolled: false,
                    }
                    : current
            );
            setExpandedModule(null);
            setModuleLessons({});

            setShowUnenrollModal(false);
        } catch {
            setError(true);
        } finally {
            setEnrolling(false);
        }
    };

    const handleOpenUnenrollModal = () => {
        if (enrolling) return;

        setShowUnenrollModal(true);
    };

    useEffect(() => {
        fetchCourse();
    }, [fetchCourse]);

    useEffect(() => {
        if (course?.is_enrolled) fetchLearning();
        else setLearning(null);
    }, [course?.is_enrolled, fetchLearning]);

    const openNextLesson = () => {
        if (!learning?.next_lesson || !slug) return;
        const {module_id: moduleId, lesson_id: lessonId} = learning.next_lesson;
        navigate(`${ROUTES.lesson}/${slug}/modules/${moduleId}/lessons/${lessonId}`);
    };

    const handlePreviousPage = () => {
        setPage((current) =>
            Math.max(1, current - 1)
        );
    };

    const handleNextPage = () => {
        setPage((current) =>
            Math.min(totalPages, current + 1)
        );
    };

    if (loading && !course) {
        return (
            <main className={styles.course}>
                <div className={styles.loading}>
                    <div className={styles.loadingImage}/>

                    <div className={styles.loadingContent}>
                        <span/>
                        <span/>
                        <span/>
                        <span/>
                    </div>
                </div>
            </main>
        );
    }

    if (error && !course) {
        return (
            <main className={styles.course}>
                <div className={styles.state}>
                    <div className={styles.stateIcon}>
                        <ImageOff/>
                    </div>

                    <h1>{t("errorTitle")}</h1>
                    <p>{t("errorDescription")}</p>

                    <button type="button" className={styles.retryButton}
                            onClick={fetchCourse}>{t("errorRetry")}</button>
                </div>
            </main>
        );
    }

    return (
        <main className={styles.course}>
            <section className={styles.hero}>
                <Link to="/courses" className={styles.backLink}>
                    <ArrowLeft/>

                    <span>{t("backToCourses")}</span>
                </Link>

                <div className={styles.heroGrid}>
                    <div className={styles.heroImage}>
                        {course?.main_image_url ? (
                            <>
                                <img src={course.main_image_url} alt={course.title}/>
                                <div className={styles.heroImageOverlay}/>
                            </>
                        ) : (
                            <ImageOff/>
                        )}
                    </div>

                    <div className={styles.heroContent}>
                        <div className={styles.badge}>
                            <BookOpen/>
                            <span>{t("courseLabel")}</span>
                        </div>

                        <h1>
                            {course?.title}
                        </h1>

                        {course?.description && (
                            <Description content={course.description} className={styles.description}/>
                        )}

                        {course?.is_enrolled && (
                            <div className={styles.courseProgressStatus} data-complete={course.is_course_completed}>
                                <CheckCircle2 aria-hidden="true"/>
                                <span>
                                    <strong>{course.is_course_completed ? t("courseCompleted") : t("courseInProgress")}</strong>
                                    <small>{t("courseProgress")}: {course.lessons_completed}/{course.lessons_total}</small>
                                </span>
                            </div>
                        )}

                        <div className={styles.courseActions}>
                            {!course?.is_enrolled ? (
                                <button type="button" className={styles.enrollButton} onClick={handleEnroll}
                                        disabled={enrolling}>
                                    <BookOpen/>
                                    <span>{enrolling ? t("enrolling") : t("enrollOnCourse")}</span>
                                </button>
                            ) : (
                                <>
                                    <button type="button" className={styles.enrollButton}
                                            onClick={openNextLesson}
                                            disabled={learningLoading || learningError || !learning?.next_lesson}>
                                        <Play/>
                                        <span>{learningLoading ? t("learningLoading") : learningError ? t("learningRetry") : learning?.is_course_completed ? t("courseCompleted") : learning?.next_lesson ? t("enrollingContinue") : t("noLessons")}</span>
                                        <ArrowRight/>
                                    </button>

                                    <button type="button" className={styles.unsubscribeButton}
                                            onClick={handleOpenUnenrollModal}
                                            disabled={enrolling}>{t("unenrolling")}</button>
                                </>
                            )}
                        </div>
                        {learningLoading && <p role="status" className={styles.learningProgress}>{t("learningLoading")}</p>}
                        {learningError && <button type="button" className={styles.learningRetry} onClick={fetchLearning}><RefreshCw/> {t("learningRetry")}</button>}
                        {!learningLoading && !learningError && learning && (
                            <div className={styles.learningProgress} aria-live="polite">
                                <span>{learning.is_course_completed ? t("courseCompleted") : learning.next_lesson ? `${t("progress")}: ${learning.lessons_completed} / ${learning.lessons_total}` : t("noLessons")}</span>
                                {learning.next_lesson && <span>{learning.next_lesson.module_title} · {learning.next_lesson.title}</span>}
                            </div>
                        )}
                    </div>
                </div>
            </section>

            <section className={styles.modulesSection}>
                <div className={styles.sectionHeading}>
                    <div>
                        <span>{t("modulesEyebrow")}</span>
                        <h2>{t("modulesTitle")}</h2>
                    </div>

                    {totalPages > 1 && (
                        <p>
                            {t("pageInfo")} {page}{" "}
                            {t("pageOf")} {totalPages}
                        </p>
                    )}
                </div>

                {loading && (
                    <div className={styles.modulesLoading}>
                        <div className={styles.moduleSkeleton}/>
                        <div className={styles.moduleSkeleton}/>
                        <div className={styles.moduleSkeleton}/>
                    </div>
                )}

                {!loading && error && (
                    <div className={styles.empty}>
                        <div className={styles.emptyIcon}>
                            <ImageOff/>
                        </div>

                        <h3>{t("errorLessonsTitle")}</h3>

                        <p>{t("errorDescription")}</p>

                        <button type="button" className={styles.retryButton}
                                onClick={fetchCourse}>{t("errorRetry")}</button>
                    </div>
                )}

                {!loading &&
                    !error &&
                    modules.length === 0 && (
                        <div className={styles.empty}>
                            <div className={styles.emptyIcon}><BookOpen/></div>
                            <h3>{t("emptyModulesTitle")}</h3>
                            <p>{t("emptyModulesDescription")}</p>
                        </div>
                    )}

                {!loading &&
                    !error &&
                    modules.length > 0 && (
                        <div className={styles.modules}>
                            {modules.map(
                                (module, index) => (
                                    <article className={styles.module} data-complete={course?.is_enrolled && module.is_completed}
                                             key={module.module_id}>
                                        <div className={styles.moduleNumber}>
                                            {String((page - 1) * PAGE_SIZE + index + 1).padStart(2, "0")}
                                        </div>
                                        <div className={styles.moduleContent}>
                                            <div className={styles.moduleTop}>
                                                <div>
                                                    <span className={styles.moduleLabel}>{t("moduleLabel")}</span>
                                                    {course?.is_enrolled && (
                                                        <span className={styles.completionStatus}
                                                              data-complete={module.is_completed}>
                                                            {module.is_completed
                                                                ? `${t("moduleCompleted")} · ${module.lessons_completed}/${module.lessons_total}`
                                                                : `${t("moduleInProgress")} · ${module.lessons_completed}/${module.lessons_total}`}
                                                        </span>
                                                    )}
                                                    {course?.is_enrolled ? (
                                                        <button type="button" className={styles.moduleToggle}
                                                                aria-expanded={expandedModule === module.module_id}
                                                                onClick={() => toggleModule(module.module_id)}>
                                                            <h3>{module.title}</h3>
                                                            <ChevronRight aria-hidden="true"/>
                                                        </button>
                                                    ) : <h3>{module.title}</h3>}
                                                </div>

                                                {module.content_url && (
                                                    <a href={module.content_url} target="_blank" rel="noreferrer"
                                                       className={styles.moduleButton} aria-label={t("openModule")}>
                                                        <ArrowRight/>
                                                    </a>
                                                )}
                                            </div>

                                            {module.description && <Description content={module.description} className={styles.moduleDescription}/>}

                                            {module.content_url && (
                                                <a href={module.content_url} target="_blank" rel="noreferrer"
                                                   className={styles.moduleLink}>
                                                    <span>{t("openModule")}</span>
                                                    <ExternalLink/>
                                                </a>
                                            )}

                                            {course?.is_enrolled && expandedModule === module.module_id && (() => {
                                                const moduleState = moduleLessons[module.module_id];
                                                if (!moduleState || moduleState.loading) {
                                                    return <div className={styles.lessonListLoading} role="status">
                                                        <span/><span/><span/>
                                                    </div>;
                                                }
                                                if (moduleState.error) {
                                                    return <div className={styles.moduleLessonsError} role="alert">
                                                        <span>{t("errorDescription")}</span>
                                                        <button type="button" onClick={() => fetchModuleLessons(module.module_id, moduleState.page ?? 1)}>
                                                            {t("errorRetry")}
                                                        </button>
                                                    </div>;
                                                }
                                                if (!moduleState.lessons.length) {
                                                    return <p className={styles.moduleLessonsEmpty}>{t("emptyLessonsTitle")}</p>;
                                                }
                                                return <div className={styles.moduleLessons}>
                                                    {moduleState.lessons.map((lesson, lessonIndex) => (
                                                        <Link className={styles.lessonLink} data-complete={lesson.is_completed}
                                                              to={`${ROUTES.lesson}/${slug}/modules/${module.module_id}/lessons/${lesson.lesson_id}`}
                                                              key={lesson.lesson_id}>
                                                            <span className={styles.lessonIndex}>
                                                                {String((moduleState.page - 1) * 100 + lessonIndex + 1).padStart(2, "0")}
                                                            </span>
                                                            <span className={styles.lessonText}>
                                                                 <strong>{lesson.title}</strong>
                                                                  {lesson.description && <Description content={lesson.description} className={styles.lessonDescription}/>}
                                                                 <small className={styles.lessonCompletionStatus}
                                                                        data-complete={lesson.is_completed}>
                                                                     {lesson.is_completed ? t("lessonCompleted") : t("lessonNotCompleted")}
                                                                 </small>
                                                             </span>
                                                            <ArrowRight aria-hidden="true"/>
                                                        </Link>
                                                    ))}
                                                    {moduleState.totalPages > 1 && <div className={styles.lessonPagination}>
                                                        <button type="button" disabled={moduleState.page <= 1}
                                                                onClick={() => fetchModuleLessons(module.module_id, moduleState.page - 1)}>
                                                            <ChevronLeft aria-hidden="true"/>{t("paginationPrevious")}
                                                        </button>
                                                        <span>{moduleState.page} / {moduleState.totalPages}</span>
                                                        <button type="button" disabled={moduleState.page >= moduleState.totalPages}
                                                                onClick={() => fetchModuleLessons(module.module_id, moduleState.page + 1)}>
                                                            {t("paginationNext")}<ChevronRight aria-hidden="true"/>
                                                        </button>
                                                    </div>}
                                                </div>;
                                            })()}
                                        </div>
                                    </article>
                                )
                            )}
                        </div>
                    )}

                {!loading &&
                    !error &&
                    totalPages > 1 && (
                        <nav className={styles.pagination} aria-label={t("paginationLabel")}>
                            <button type="button" className={styles.pageButton} disabled={page <= 1}
                                    onClick={handlePreviousPage} aria-label={t("paginationPrevious")}>
                                <ChevronLeft/>
                            </button>
                            <div className={styles.pageInfo}>
                                <strong>{page}</strong>
                                <span>/</span>
                                <span>{totalPages}</span>
                            </div>
                            <button type="button" className={styles.pageButton} disabled={page >= totalPages}
                                    onClick={handleNextPage} aria-label={t("paginationNext")}>
                                <ChevronRight/>
                            </button>
                        </nav>
                    )}
            </section>

            {showUnenrollModal && (
                <div
                    className={styles.modalOverlay}
                    onClick={() => {
                        if (!enrolling) {
                            setShowUnenrollModal(false);
                        }
                    }}
                >
                    <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
                        <div className={styles.modalIcon}>
                            <BookOpen/>
                        </div>
                        <h2>{t("unenrollTitle")}</h2>
                        <p>{t("unenrollDescription")}</p>

                        <div className={styles.modalActions}>
                            <button type="button" className={styles.modalCancel}
                                    onClick={() => setShowUnenrollModal(false)}
                                    disabled={enrolling}>{t("unenrollCancel")}</button>

                            <button type="button" className={styles.modalConfirm} onClick={handleUnenroll} disabled={enrolling}>
                                {enrolling
                                    ? t("unenrollingProcess")
                                    : t("unenrollConfirm")}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
