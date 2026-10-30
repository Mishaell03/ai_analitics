import {Link} from "react-router-dom";
import {ArrowLeft, ArrowRight} from "lucide-react";
import {ROUTES} from "@/router/AppRouter.jsx";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./course.module.css";

/** Переходы выполняют только просмотр: здесь нет запросов завершения урока. */
export default function LessonNavigation({navigation, slug}) {
    const t = useTranslation("courses.course");
    const path = (lesson) => `${ROUTES.lesson}/${slug}/modules/${lesson.module_id}/lessons/${lesson.lesson_id}`;
    return (
        <nav className={styles.lessonNavigation} aria-label={t("lessonNavigationLabel")}>
            {navigation.loading && <span className={styles.lessonNavigationMessage} role="status">{t("lessonNavigationLoading")}</span>}
            {navigation.error && <span className={styles.lessonNavigationMessage} role="alert">{t("lessonNavigationError")}</span>}
            {navigation.previous ? (
                <Link to={path(navigation.previous)} className={styles.lessonNavButton}>
                    <ArrowLeft aria-hidden="true"/><span>{t("previousLesson")}</span>
                </Link>
            ) : <span/>}
            {navigation.next && (
                <Link to={path(navigation.next)} className={styles.lessonNavButton}>
                    <span>{t("nextLesson")}</span><ArrowRight aria-hidden="true"/>
                </Link>
            )}
        </nav>
    );
}
