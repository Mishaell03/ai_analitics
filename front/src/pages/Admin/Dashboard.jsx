import {useCallback, useEffect, useMemo, useState} from "react";
import {Link} from "react-router-dom";
import {
    Activity,
    BookOpen,
    Flame,
    GraduationCap,
    Inbox,
    RefreshCw,
    ShieldCheck,
    TriangleAlert,
    UserCheck,
    Users,
} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import {useAuth} from "@/context/AuthContext.jsx";
import {getTranslation} from "@/locales/i18n.js";
import {formatDateTime, formatNumber} from "@/services/format.js";
import StatCard from "@/components/StatCard/StatCard.jsx";
import BarChart from "@/components/BarChart/BarChart.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import styles from "./dashboard.module.css";

const language = "ru";

// сколько последних пользователей показываем и сколько курсов берём в топ
const LATEST_USERS = 10;
const TOP_COURSES = 3;

const STAT_CARDS = [
    {key: "total_users", title: "statsUsers", icon: Users, tone: "accent"},
    {key: "total_courses", title: "statsCourses", icon: BookOpen, tone: "primary"},
    {key: "total_lessons", title: "statsLessons", icon: GraduationCap, tone: "focus"},
    {key: "total_enrollments", title: "statsEnrollments", icon: UserCheck, tone: "accent"},
    {key: "total_active_sessions", title: "statsActiveSessions", icon: Activity, tone: "primary"},
];

// пустой ответ, чтобы разметка не зависела от наличия ключей
const EMPTY_DASHBOARD = {
    total_users: 0,
    total_courses: 0,
    total_lessons: 0,
    total_enrollments: 0,
    total_active_sessions: 0,
    latest_users: [],
    top_courses: [],
};

// первая буква имени для аватара, иначе — первая буква почты
function getInitial(user) {
    return (user.name || user.email || "?").trim().charAt(0).toUpperCase();
}

export function Dashboard() {
    const {user, loading: authLoading} = useAuth();

    const t = (key) => getTranslation(`admin.admin.${key}`, language);

    const [dashboard, setDashboard] = useState(EMPTY_DASHBOARD);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchDashboard = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_DASHBOARD, {
                params: {
                    users: LATEST_USERS,
                    top_courses: TOP_COURSES,
                },
            });

            setDashboard({...EMPTY_DASHBOARD, ...data});
        } catch (requestError) {
            // 403 — сессия есть, но прав администратора нет
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchDashboard();
    }, [fetchDashboard]);

    const topCourses = useMemo(
        () => dashboard.top_courses.map((course) => ({
            key: course.course_id,
            title: course.title,
            value: course.enrollments_count,
        })),
        [dashboard.top_courses]
    );

    const forbiddenState = (
        <main className={styles.dashboard}>
            <div className={styles.state}>
                <EmptyState
                    icon={ShieldCheck}
                    title={t("forbiddenTitle")}
                    description={t("forbiddenDescription")}
                    action={
                        <Link to={ROUTES.profile} className={styles.linkButton}>
                            {t("forbiddenButton")}
                        </Link>
                    }
                />
            </div>
        </main>
    );

    // прав нет ни у гостя, ни у пользователя, ни по ответу бэкенда
    if (error === "forbidden" || (!authLoading && !user?.is_admin)) {
        return forbiddenState;
    }

    if (error) {
        return (
            <main className={styles.dashboard}>
                <div className={styles.state}>
                    <EmptyState
                        icon={TriangleAlert}
                        title={t("errorTitle")}
                        description={t("errorDescription")}
                        action={
                            <button
                                type="button"
                                className={styles.linkButton}
                                onClick={fetchDashboard}
                            >
                                {t("errorRetry")}
                            </button>
                        }
                    />
                </div>
            </main>
        );
    }

    // пока проверяется сессия, показываем скелетоны вместо пустых метрик
    const pending = authLoading || loading;

    const latestUsers = dashboard.latest_users;

    return (
        <main className={styles.dashboard}>

            {/* ---------- heading ---------- */}

            <section className={styles.heading}>
                <div className={styles.badge}>
                    <span className={styles.badgeDot}/>
                    {t("badge")}
                </div>

                <div className={styles.headingRow}>
                    <div className={styles.headingContent}>
                        <h1>{t("title")}</h1>
                        <p>{t("subtitle")}</p>
                    </div>

                    <button
                        type="button"
                        className={styles.refreshButton}
                        onClick={fetchDashboard}
                        disabled={pending}
                    >
                        <RefreshCw/>
                        <span>
                            {pending ? t("refreshProcess") : t("refreshButton")}
                        </span>
                    </button>
                </div>
            </section>

            {/* ---------- stats ---------- */}

            <section className={styles.stats} aria-label={t("statsEyebrow")}>
                {STAT_CARDS.map(({key, title, icon, tone}) => (
                    <StatCard
                        key={key}
                        icon={icon}
                        tone={tone}
                        label={t(title)}
                        value={formatNumber(dashboard[key])}
                        loading={pending}
                    />
                ))}
            </section>

            <div className={styles.columns}>

                {/* ---------- top courses ---------- */}

                <section className={styles.panel}>
                    <div className={styles.panelHeading}>
                        <div>
                            <span>{t("topCoursesEyebrow")}</span>
                            <h2>{t("topCoursesTitle")}</h2>
                        </div>

                        <span className={styles.panelIcon}>
                            <Flame/>
                        </span>
                    </div>

                    {pending && (
                        <BarChart
                            data={[]}
                            label={t("topCoursesTitle")}
                            unit={t("topCoursesCount")}
                            loading
                            skeletonRows={TOP_COURSES}
                        />
                    )}

                    {!pending && topCourses.length === 0 && (
                        <EmptyState
                            icon={Inbox}
                            title={t("topCoursesEmptyTitle")}
                            description={t("topCoursesEmptyDescription")}
                        />
                    )}

                    {!pending && topCourses.length > 0 && (
                        <BarChart
                            data={topCourses}
                            label={t("topCoursesTitle")}
                            unit={t("topCoursesCount")}
                        />
                    )}
                </section>

                {/* ---------- latest users ---------- */}

                <aside className={styles.panel}>
                    <div className={styles.panelHeading}>
                        <div>
                            <span>{t("usersEyebrow")}</span>
                            <h2>{t("usersTitle")}</h2>
                        </div>

                        {!pending && (
                            <span className={styles.counter}>
                                {formatNumber(latestUsers.length)}
                            </span>
                        )}
                    </div>

                    {pending && (
                        <ul className={styles.users}>
                            {Array.from(
                                {length: LATEST_USERS},
                                (_, index) => (
                                    <li className={styles.user} data-skeleton="true" key={index}>
                                        <span className={styles.userAvatar}/>
                                        <div className={styles.userBody}>
                                            <span/>
                                            <span/>
                                        </div>
                                    </li>
                                )
                            )}
                        </ul>
                    )}

                    {!pending && latestUsers.length === 0 && (
                        <EmptyState
                            icon={Users}
                            title={t("usersEmptyTitle")}
                            description={t("usersEmptyDescription")}
                        />
                    )}

                    {!pending && latestUsers.length > 0 && (
                        <ul className={styles.users}>
                            {latestUsers.map((latestUser) => (
                                <li className={styles.user} key={latestUser.user_id}>
                                    <span className={styles.userAvatar}>
                                        {getInitial(latestUser)}
                                    </span>

                                    <div className={styles.userBody}>
                                        <div className={styles.userTop}>
                                            <span className={styles.userName}>
                                                {latestUser.name || t("usersNameEmpty")}
                                            </span>

                                            <span className={styles.userId}>
                                                #{latestUser.user_id}
                                            </span>
                                        </div>

                                        <span className={styles.userEmail}>
                                            {latestUser.email}
                                        </span>

                                        <span className={styles.userDate}>
                                            {formatDateTime(
                                                latestUser.created_at,
                                                t("usersDateEmpty")
                                            )}
                                        </span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </aside>
            </div>
        </main>
    );
}
