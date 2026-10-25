import {useCallback, useEffect, useState} from "react";
import {Link, useNavigate, useParams} from "react-router-dom";
import {ArrowLeft, ArrowRight, ImageOff} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import Markdown from "@/components/Markdown/Markdown.jsx";
import {buildAnswerMap} from "@/services/exercises.js";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./course.module.css";

export function Lesson() {
    const {slug, moduleId, lessonId} = useParams();
    const navigate = useNavigate();
    const t = useTranslation("courses.course");
    const [lesson, setLesson] = useState(null);
    const [content, setContent] = useState("");
    const [completedExercises, setCompletedExercises] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [completing, setCompleting] = useState(false);
    const [completionState, setCompletionState] = useState(null);
    const [courseFinished, setCourseFinished] = useState(false);
    const [nextLessonError, setNextLessonError] = useState(false);

    const fetchLesson = useCallback(async () => {
        setLoading(true);
        setError(false);
        try {
            const [detail, body] = await Promise.all([
                api.get(API_ROUTES.COURSE_LESSON(slug, moduleId, lessonId)),
                api.get(API_ROUTES.COURSE_LESSON_CONTENT(slug, moduleId, lessonId)),
            ]);
            setLesson(detail.data);
            setContent(body.data.content ?? "");
            setCompletedExercises(buildAnswerMap(body.data.completed_exercises));
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [slug, moduleId, lessonId]);

    useEffect(() => { fetchLesson(); }, [fetchLesson]);

    const checkExercise = async (exerciseId, answer) => {
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

    const completeLesson = async () => {
        if (completing || completionState === "complete") return;
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

    return (
        <main className={styles.course}>
            <section className={styles.lessonPage}>
                <Link to={`${ROUTES.course}/${slug}`} className={styles.backLink}>
                    <ArrowLeft/><span>{t("backToCourse")}</span>
                </Link>
                {loading && <div className={styles.loading} role="status"><div className={styles.loadingContent}><span/><span/><span/></div></div>}
                {!loading && error && <div className={styles.state} role="alert">
                    <div className={styles.stateIcon}><ImageOff/></div><h1>{t("lessonErrorTitle")}</h1>
                    <p>{t("errorDescription")}</p><button type="button" className={styles.retryButton} onClick={fetchLesson}>{t("errorRetry")}</button>
                </div>}
                {!loading && !error && <>
                    <p className={styles.lessonModule}>{lesson?.course?.title} · {lesson?.module?.title}</p>
                    <h1 className={styles.lessonTitle}>{lesson?.lesson?.title}</h1>
                    {lesson?.lesson?.description && <p className={styles.description}>{lesson.lesson.description}</p>}
                    <Markdown content={content} answers={completedExercises} onExerciseCheck={checkExercise}
                              labels={{
                                  check: t("exerciseCheck"),
                                  checking: t("exerciseChecking"),
                                  correct: t("exerciseCorrect"),
                                  incorrect: t("exerciseIncorrect"),
                                  checkError: t("exerciseCheckError"),
                              }}/>
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
                </>}
            </section>
        </main>
    );
}
