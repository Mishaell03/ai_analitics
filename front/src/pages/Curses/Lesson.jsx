import {useCallback, useEffect, useRef, useState} from "react";
import {Link, useNavigate, useParams} from "react-router-dom";
import {ArrowLeft, ArrowRight, ImageOff} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {listCourseLessonMedia, refreshCourseLessonMediaUrl} from "@/api/media.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import Markdown from "@/components/Markdown/Markdown.jsx";
import Description from "@/components/Markdown/Description.jsx";
import LessonMentor from "@/components/LessonMentor/LessonMentor.jsx";
import {buildAnswerMap} from "@/services/exercises.js";
import {loadLessonMediaMap} from "@/services/media.js";
import {canCompleteLesson, isLessonBrowsingAllowed} from "@/services/lessonCompletion.js";
import LessonNavigation from "./LessonNavigation.jsx";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./course.module.css";

const MODULE_PAGE_SIZE = 100;

async function loadLessonNavigation(slug, moduleId, lessonId) {
    const courseResponse = await api.get(API_ROUTES.COURSE_BY_ID(slug), {
        params: {page: 1, page_size: MODULE_PAGE_SIZE},
    });
    const modules = [...(courseResponse.data.modules ?? [])];
    const coursePages = courseResponse.data.total_pages ?? 1;

    if (coursePages > 1) {
        const remainingPages = await Promise.all(
            Array.from({length: coursePages - 1}, (_, index) =>
                api.get(API_ROUTES.COURSE_BY_ID(slug), {
                    params: {page: index + 2, page_size: MODULE_PAGE_SIZE},
                })
            )
        );
        remainingPages.forEach(({data}) => modules.push(...(data.modules ?? [])));
    }

    const getModulePage = (id, page = 1) => api.get(
        API_ROUTES.COURSE_MODULE_LESSONS(slug, id),
        {params: {page, page_size: MODULE_PAGE_SIZE}}
    );

    const currentPage = await getModulePage(moduleId);
    let currentLessons = currentPage.data.lessons ?? [];
    const lessonPages = currentPage.data.total_pages ?? 1;
    if (lessonPages > 1) {
        const rest = await Promise.all(
            Array.from({length: lessonPages - 1}, (_, index) => getModulePage(moduleId, index + 2))
        );
        rest.forEach(({data}) => currentLessons.push(...(data.lessons ?? [])));
    }

    const currentIndex = currentLessons.findIndex((item) => String(item.lesson_id) === String(lessonId));
    const currentModuleIndex = modules.findIndex((item) => String(item.module_id) === String(moduleId));
    let previous = currentIndex > 0
        ? {...currentLessons[currentIndex - 1], module_id: Number(moduleId)}
        : null;
    let next = currentIndex >= 0 && currentLessons[currentIndex + 1]
        ? {...currentLessons[currentIndex + 1], module_id: Number(moduleId)}
        : null;

    const findEdgeLesson = async (startIndex, step, edge) => {
        for (let index = startIndex; index >= 0 && index < modules.length; index += step) {
            const {data} = await getModulePage(modules[index].module_id);
            const lessons = data.lessons ?? [];
            if (lessons.length) {
                if (edge === "first") return {...lessons[0], module_id: modules[index].module_id};
                const lastPage = data.total_pages ?? 1;
                if (lastPage === 1) return {...lessons[lessons.length - 1], module_id: modules[index].module_id};
                const {data: lastData} = await getModulePage(modules[index].module_id, lastPage);
                const lastLessons = lastData.lessons ?? [];
                return lastLessons.length
                    ? {...lastLessons[lastLessons.length - 1], module_id: modules[index].module_id}
                    : null;
            }
        }
        return null;
    };

    if (currentIndex === 0 && currentModuleIndex > 0) {
        previous = await findEdgeLesson(currentModuleIndex - 1, -1, "last");
    }
    if ((currentIndex === currentLessons.length - 1 || currentIndex < 0)
        && currentModuleIndex >= 0 && currentModuleIndex < modules.length - 1) {
        next = await findEdgeLesson(currentModuleIndex + 1, 1, "first");
    }

    return {previous, next};
}

export function Lesson() {
    const {slug, moduleId, lessonId} = useParams();
    const navigate = useNavigate();
    const t = useTranslation("courses.course");
    const [lesson, setLesson] = useState(null);
    const [content, setContent] = useState("");
    const [media, setMedia] = useState({});
    const mediaRetries = useRef(new Set());
    const [completedExercises, setCompletedExercises] = useState({});
    const [expertReviewExercises, setExpertReviewExercises] = useState([]);
    const [exerciseBlocks, setExerciseBlocks] = useState([]);
    const [allowBrowsing, setAllowBrowsing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [completing, setCompleting] = useState(false);
    const [completionState, setCompletionState] = useState(null);
    const [courseFinished, setCourseFinished] = useState(false);
    const [nextLessonError, setNextLessonError] = useState(false);
    const [courseProgress, setCourseProgress] = useState(null);
    const [lessonNavigation, setLessonNavigation] = useState({previous: null, next: null, loading: false});

    const fetchLesson = useCallback(async () => {
        setLoading(true);
        setError(false);
        setCourseProgress(null);
        setLessonNavigation({previous: null, next: null, loading: true});
        setCompletionState(null);
        setCourseFinished(false);
        setMedia({});
        mediaRetries.current = new Set();
        try {
            const [detail, body, lessonMedia] = await Promise.all([
                api.get(API_ROUTES.COURSE_LESSON(slug, moduleId, lessonId)),
                api.get(API_ROUTES.COURSE_LESSON_CONTENT(slug, moduleId, lessonId)),
                loadLessonMediaMap((page) => listCourseLessonMedia(slug, moduleId, lessonId, {page})),
            ]);
            setLesson(detail.data);
            setContent(body.data.content ?? "");
            setMedia(lessonMedia);
            setCompletedExercises(buildAnswerMap(body.data.completed_exercises));
            setExpertReviewExercises(body.data.expert_review_exercises ?? []);
            setExerciseBlocks(body.data.custom_blocks ?? []);
            const browsing = isLessonBrowsingAllowed(
                import.meta.env.VITE_LESSON_ALLOW_BROWSING, body.data.allow_lesson_browsing
            );
            setAllowBrowsing(browsing);
            let progress = null;
            try {
                const response = await api.get(API_ROUTES.COURSE_NEXT_LESSON(slug));
                progress = response.data;
                setCourseProgress(progress);
            } catch {
                setCourseProgress(null);
            }

            const isPreviouslyCompleted = Boolean(
                detail.data.lesson.is_completed
            );

            if (browsing || (isPreviouslyCompleted && !progress?.is_course_completed)) {
                setLessonNavigation({previous: null, next: null, loading: true});
                try {
                    const navigation = await loadLessonNavigation(slug, moduleId, lessonId);
                    setLessonNavigation({...navigation, loading: false});
                } catch {
                    setLessonNavigation({previous: null, next: null, loading: false, error: true});
                }
            } else {
                setLessonNavigation({previous: null, next: null, loading: false});
            }
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [slug, moduleId, lessonId]);

    useEffect(() => { fetchLesson(); }, [fetchLesson]);

    const handleMediaError = async (mediaKey) => {
        const retries = mediaRetries.current;
        // Повреждённый или отсутствующий файл не должен вызывать бесконечные запросы.
        if (retries.has(mediaKey)) return;
        retries.add(mediaKey);
        try {
            const data = await refreshCourseLessonMediaUrl(slug, moduleId, lessonId, mediaKey);
            if (mediaRetries.current !== retries) return;
            setMedia((current) => ({
                ...current,
                [mediaKey]: {...current[mediaKey], url: data.url},
            }));
        } catch {
            // Повторная загрузка урока позволит запросить файл заново.
        }
    };

    const checkExercise = async (exerciseId, answer, execution) => {
        if (execution?.execute) {
            const {data} = await api.post(API_ROUTES.SANDBOX_EXECUTE, {
                course_slug: slug, module_id: Number(moduleId), lesson_id: Number(lessonId),
                exercise_id: exerciseId, language: execution.language, code: execution.code,
            });
            if (data.is_correct === true) {
                setCompletedExercises((current) => ({
                    ...current, ...buildAnswerMap({[exerciseId]: answer}),
                }));
            }
            if (data.check_mode === "self_review" && data.expert_solution_available === true) {
                setExpertReviewExercises((current) => [...new Set([...current, exerciseId])]);
            }
            return data;
        }
        const {data: isCorrect} = await api.post(
            API_ROUTES.COURSE_EXERCISE_CHECK(slug, moduleId, lessonId, exerciseId),
            {answer}
        );
        if (isCorrect) {
            setCompletedExercises((current) => ({
                ...current,
                ...buildAnswerMap({[exerciseId]: answer}),
            }));
        }
        return isCorrect;
    };

    const loadExpertSolution = useCallback(async (exerciseId) => {
        const {data} = await api.get(API_ROUTES.COURSE_EXPERT_SOLUTION(slug, moduleId, lessonId, exerciseId));
        return data;
    }, [slug, moduleId, lessonId]);

    const completeLesson = async () => {
        if (completing || completionState === "complete") return;
        if (!canCompleteLesson(exerciseBlocks, completedExercises, expertReviewExercises)) {
            setCompletionState("incomplete");
            return;
        }
        setCompleting(true);
        setCompletionState(null);
        setNextLessonError(false);
        try {
            const {data: completed} = await api.post(
                API_ROUTES.COURSE_LESSON_COMPLETE(slug, moduleId, lessonId)
            );
            if (!completed) {
                setCompletionState("incomplete");
                return;
            }

            setCompletionState("complete");
            try {
                const {data: progress} = await api.get(API_ROUTES.COURSE_NEXT_LESSON(slug));
                const nextLesson = progress.next_lesson;
                if (nextLesson) {
                    navigate(`${ROUTES.lesson}/${slug}/modules/${nextLesson.module_id}/lessons/${nextLesson.lesson_id}`);
                } else {
                    setCourseFinished(true);
                }
            } catch {
                setNextLessonError(true);
            }
        } catch {
            setCompletionState("error");
        } finally {
            setCompleting(false);
        }
    };

    const nextIncompleteLesson = courseProgress?.next_lesson;
    const isPreviouslyCompleted = Boolean(lesson?.lesson?.is_completed);

    const lessonPath = (item) =>
        `${ROUTES.lesson}/${slug}/modules/${item.module_id}/lessons/${item.lesson_id}`;

    return (
        <main className={`${styles.course} ${styles.lessonCourse}`}>
            <div className={styles.lessonLayout}>
            <section className={styles.lessonPage}>
                <header className={styles.lessonHeader}>
                    <Link to={`${ROUTES.course}/${slug}`} className={styles.backLink}>
                        <ArrowLeft aria-hidden="true"/><span>{t("backToCourse")}</span>
                    </Link>
                    {!loading && !error && lesson?.course?.title && (
                        <p className={styles.lessonCourseName}>{lesson.course.title}</p>
                    )}
                </header>
                {loading && <div className={styles.loading} role="status"><div className={styles.loadingContent}><span/><span/><span/></div></div>}
                {!loading && error && <div className={styles.state} role="alert">
                    <div className={styles.stateIcon}><ImageOff/></div><h1>{t("lessonErrorTitle")}</h1>
                    <p>{t("errorDescription")}</p><button type="button" className={styles.retryButton} onClick={fetchLesson}>{t("errorRetry")}</button>
                </div>}
                {!loading && !error && <>
                    {lesson?.module?.title && <p className={styles.lessonModule}>{lesson.module.title}</p>}
                    <h1 className={styles.lessonTitle}>{lesson?.lesson?.title}</h1>
                    <span className={styles.lessonCompletionStatus}
                          data-complete={Boolean(lesson?.lesson?.is_completed)}>
                        {lesson?.lesson?.is_completed ? t("lessonCompleted") : t("lessonNotCompleted")}
                    </span>
                    {lesson?.lesson?.description && <Description content={lesson.lesson.description} className={styles.description}/>}
                    <Markdown key={`${slug}/${moduleId}/${lessonId}`}
                              content={content} media={media} onMediaError={handleMediaError}
                              answers={completedExercises} onExerciseCheck={checkExercise}
                              onExpertSolution={loadExpertSolution}
                              expertReviewExercises={expertReviewExercises}
                              labels={{
                                  check: t("exerciseCheck"),
                                  checking: t("exerciseChecking"),
                                  correct: t("exerciseCorrect"),
                                  incorrect: t("exerciseIncorrect"),
                                  checkError: t("exerciseCheckError"),
                              }}/>
                    {isPreviouslyCompleted ? (
                        <div className={styles.lessonCompletion} data-complete="true">
                            <div className={styles.completionCopy}>
                                <span className={styles.completionEyebrow}>{t("lessonCompleted")}</span>
                                <h2>{courseProgress?.is_course_completed ? t("courseLearningComplete") : t("reviewedLessonTitle")}</h2>
                                <p>{courseProgress?.is_course_completed ? t("courseLearningCompleteDescription") : t("reviewedLessonDescription")}</p>
                            </div>
                            {courseProgress && !courseProgress.is_course_completed && nextIncompleteLesson && (
                                <Link className={styles.completeButton} to={lessonPath(nextIncompleteLesson)}>
                                    <span>{t("returnToAssignments")}</span><ArrowRight aria-hidden="true"/>
                                </Link>
                            )}
                        </div>
                    ) : (
                        <div className={styles.lessonCompletion} data-complete={completionState === "complete"}>
                            <div className={styles.completionCopy}>
                                <span className={styles.completionEyebrow}>{t("lessonFinishEyebrow")}</span>
                                <h2>{courseFinished ? t("courseLearningComplete") : t("lessonFinishTitle")}</h2>
                                <p>{courseFinished ? t("courseLearningCompleteDescription") : t("lessonFinishDescription")}</p>
                            </div>
                            {!courseFinished && completionState !== "complete" && (
                                <button type="button" className={styles.completeButton}
                                        onClick={completeLesson} disabled={completing}>
                                    <span>{completing ? t("lessonCompleting") : t("completeLesson")}</span>
                                    {!completing && <ArrowRight aria-hidden="true"/>}
                                </button>
                            )}
                            {courseFinished && <Link className={styles.completeButton} to={`${ROUTES.course}/${slug}`}>
                                <span>{t("backToCourse")}</span><ArrowLeft aria-hidden="true"/>
                            </Link>}
                            {completionState === "incomplete" && <p className={styles.completionError} role="alert">{t("lessonIncomplete")}</p>}
                            {completionState === "error" && <p className={styles.completionError} role="alert">{t("lessonCompleteError")}</p>}
                            {nextLessonError && <p className={styles.completionHint} role="status">{t("nextLessonError")}</p>}
                        </div>
                    )}
                    {(allowBrowsing || (isPreviouslyCompleted && !courseProgress?.is_course_completed)) && (
                        <LessonNavigation navigation={lessonNavigation} slug={slug}/>
                    )}
                </>}
            </section>
            {!loading && !error && <div className={styles.lessonSidebar}>
                <LessonMentor key={`${slug}/${moduleId}/${lessonId}`} slug={slug} moduleId={moduleId} lessonId={lessonId}/>
            </div>}
            </div>
        </main>
    );
}
