import {useMemo} from "react";
import {Link} from "react-router-dom";
import {
    Activity,
    BookOpen,
    Flame,
    GraduationCap,
    Inbox,
    ShieldCheck,
    TriangleAlert,
    UserCheck,
    Users,
} from "lucide-react";
import {ROUTES} from "@/router/AppRouter.jsx";
import {formatDateTime, formatNumber} from "@/services/format.js";
import StatCard from "@/components/StatCard/StatCard.jsx";
import BarChart from "@/components/BarChart/BarChart.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import UserAvatar from "@/components/UserAvatar/UserAvatar.jsx";
import AdminPageHeader from "@/pages/Admin/components/AdminPageHeader.jsx";
import {useAdminAccess} from "@/pages/Admin/hooks/useAdminAccess.js";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {LATEST_USERS, TOP_COURSES, useDashboard} from "./useDashboard.js";
import styles from "./dashboard.module.css";

const STAT_CARDS = [
    {key: "total_users", title: "statsUsers", icon: Users, tone: "accent"},
    {key: "total_courses", title: "statsCourses", icon: BookOpen, tone: "primary"},
    {key: "total_lessons", title: "statsLessons", icon: GraduationCap, tone: "focus"},
    {key: "total_enrollments", title: "statsEnrollments", icon: UserCheck, tone: "accent"},
    {key: "total_active_sessions", title: "statsActiveSessions", icon: Activity, tone: "primary"},
];

/**
 * Дашборд админки: метрики, популярные курсы и последние регистрации.
 */
export function Dashboard() {
    const t = useAdminTranslation();

    const {dashboard, loading, error, reload} = useDashboard();
    const {authLoading, isForbidden} = useAdminAccess(error);

    const topCourses = useMemo(
        () => dashboard.top_courses.map((course) => ({
            key: course.course_id,
            title: course.title,
            value: course.enrollments_count,
        })),
        [dashboard.top_courses]
    );

    if (isForbidden) {
        return (
            <div className={styles.dashboard}>
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
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.dashboard}>
                <div className={styles.state}>
                    <EmptyState
                        icon={TriangleAlert}
                        title={t("errorTitle")}
                        description={t("errorDescription")}
                        action={
                            <button
                                type="button"
                                className={styles.linkButton}
                                onClick={reload}
                            >
                                {t("errorRetry")}
                            </button>
                        }
                    />
                </div>
            </div>
        );
    }

    // пока проверяется сессия, показываем скелетоны вместо пустых метрик
    const pending = authLoading || loading;

    const latestUsers = dashboard.latest_users;

    return (
        <div className={styles.dashboard}>
            <AdminPageHeader
                eyebrow={t("badge")}
                title={t("title")}
                subtitle={t("subtitle")}
                onRefresh={reload}
                refreshing={pending}
                refreshLabel={t("refreshButton")}
                refreshingLabel={t("refreshProcess")}
                titleClassName={styles.title}
            />

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
                                        <span className={styles.userSkeletonAvatar}/>
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
                                    <UserAvatar
                                        url={latestUser.img_url}
                                        name={latestUser.name}
                                        email={latestUser.email}
                                    />

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
        </div>
    );
}
