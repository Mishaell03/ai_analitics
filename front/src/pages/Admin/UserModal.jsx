import {useCallback, useEffect, useState} from "react";
import {
    BookOpen,
    Clock,
    Fingerprint,
    Globe,
    KeyRound,
    Link2,
    Monitor,
    ShieldCheck,
    TriangleAlert,
    X,
} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {getTranslation} from "@/locales/i18n.js";
import {formatDateTime, formatNumber} from "@/services/format.js";
import UserAvatar from "@/components/UserAvatar/UserAvatar.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import styles from "./userModal.module.css";

const language = "ru";

/**
 * Модальное окно с подробной карточкой пользователя.
 *
 * Данные тянет сам по userId: странице-родителю не нужно
 * держать лишнее состояние, достаточно знать id открытого пользователя.
 */
function UserModal({userId, onClose}) {
    const t = (key, params) => getTranslation(`admin.admin.${key}`, language, params);

    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const fetchDetail = useCallback(async () => {
        setError(false);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_USER_DETAIL(userId));

            setDetail(data);
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        fetchDetail();
    }, [fetchDetail]);

    // закрытие по Escape и блокировка прокрутки фона
    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === "Escape") {
                onClose();
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "hidden";

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "";
        };
    }, [onClose]);

    const renderSkeleton = () => (
        <div className={styles.skeletonBody}>
            <div className={styles.skeletonHead}>
                <span className={styles.skeletonAvatar}/>
                <div className={styles.skeletonLines}>
                    <span/>
                    <span/>
                </div>
            </div>

            {Array.from({length: 3}, (_, index) => (
                <div className={styles.skeletonBlock} key={index}>
                    <span/>
                    <span/>
                    <span/>
                </div>
            ))}
        </div>
    );

    const renderError = () => (
        <div className={styles.modalState}>
            <span className={styles.stateIcon}>
                <TriangleAlert/>
            </span>

            <h3>{t("userModalErrorTitle")}</h3>
            <p>{t("userModalErrorDescription")}</p>

            <button type="button" className={styles.retryButton} onClick={fetchDetail}>
                {t("userModalErrorRetry")}
            </button>
        </div>
    );

    const renderDetail = () => {
        const user = detail.user;
        const learning = detail.learning;

        const hasCourses = detail.courses.length > 0;
        const hasAttempts = detail.recent_attempts.length > 0;
        const hasAuth = detail.auth_methods.length > 0;
        const hasConsents = detail.consents.length > 0;
        const hasSessions = detail.sessions.length > 0;

        return (
            <div className={styles.body}>

                {/* ---------- header ---------- */}

                <header className={styles.head}>
                    <UserAvatar
                        url={user.img_url}
                        name={user.name}
                        email={user.email}
                        size={56}
                    />

                    <div className={styles.headContent}>
                        <h2>{user.name || t("usersNameEmpty")}</h2>
                        <p>{user.email}</p>

                        <div className={styles.headTags}>
                            <Badge tone="muted" icon={Fingerprint}>
                                #{user.user_id}
                            </Badge>

                            {user.is_admin && (
                                <Badge tone="accent" icon={ShieldCheck}>
                                    {t("usersRoleAdmin")}
                                </Badge>
                            )}

                            {user.is_blocked && (
                                <Badge tone="error">
                                    {t("usersRoleBlocked")}
                                </Badge>
                            )}

                            <Badge tone="muted" icon={Clock}>
                                {t("userModalRegistered")}: {formatDateTime(user.created_at)}
                            </Badge>
                        </div>
                    </div>
                </header>

                {/* ---------- counters ---------- */}

                <div className={styles.counters}>
                    <div className={styles.counter}>
                        <Monitor/>
                        <strong>{formatNumber(detail.total_sessions)}</strong>
                        <span>{t("userModalSessionsTotal")}</span>
                    </div>

                    <div className={styles.counter} data-tone="focus">
                        <Link2/>
                        <strong>{formatNumber(detail.active_sessions)}</strong>
                        <span>{t("userModalSessionsActive")}</span>
                    </div>

                    <div className={styles.counter}>
                        <BookOpen/>
                        <strong>{formatNumber(learning.enrollments)}</strong>
                        <span>{t("userModalEnrollments")}</span>
                    </div>

                    <div className={styles.counter}>
                        <Fingerprint/>
                        <strong>
                            {formatNumber(learning.lessons_solved)}
                            <em>/{formatNumber(learning.lessons_with_attempts)}</em>
                        </strong>
                        <span>{t("userModalSolved")}</span>
                    </div>

                    <div className={styles.counter} data-tone="primary">
                        <Clock/>
                        <strong>{formatNumber(learning.attempts_total)}</strong>
                        <span>{t("userModalAttempts")}</span>
                    </div>
                </div>

                {/* ---------- auth methods ---------- */}

                <section className={styles.section}>
                    <h3>
                        <KeyRound/>
                        {t("userModalAuthTitle")}
                    </h3>

                    {!hasAuth && <p className={styles.empty}>{t("userModalAuthEmpty")}</p>}

                    {hasAuth && (
                        <div className={styles.chips}>
                            {detail.auth_methods.map((method) => (
                                <Badge key={method.provider} tone="accent">
                                    {method.provider_name || method.provider}
                                    <em>{formatDateTime(method.created_at)}</em>
                                </Badge>
                            ))}
                        </div>
                    )}
                </section>

                {/* ---------- consents ---------- */}

                <section className={styles.section}>
                    <h3>
                        <ShieldCheck/>
                        {t("userModalConsentsTitle")}
                    </h3>

                    {!hasConsents && <p className={styles.empty}>{t("userModalConsentsEmpty")}</p>}

                    {hasConsents && (
                        <div className={styles.rows}>
                            {detail.consents.map((consent, index) => (
                                <div className={styles.row} key={`${consent.consent_code}-${index}`}>
                                    <strong>{consent.consent_code}</strong>

                                    <Badge tone={consent.is_accepted ? "focus" : "error"}>
                                        {consent.is_accepted
                                            ? t("userModalConsentAccepted")
                                            : t("userModalConsentNotAccepted")}
                                    </Badge>

                                    <span className={styles.rowMeta}>
                                        {t("userModalConsentVersion", {
                                            version: consent.policy_version ?? "—",
                                        })}
                                        {" · "}
                                        {formatDateTime(consent.accepted_at)}
                                        {" · "}
                                        {consent.ip ?? "—"}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* ---------- sessions ---------- */}

                <section className={styles.section}>
                    <h3>
                        <Monitor/>
                        {t("userModalSessionsTitle")}
                    </h3>

                    {!hasSessions && <p className={styles.empty}>{t("userModalSessionsEmpty")}</p>}

                    {hasSessions && (
                        <div className={styles.rows}>
                            {detail.sessions.map((session) => (
                                <div className={styles.row} key={session.session_id}>
                                    <div className={styles.rowTop}>
                                        <strong>{session.platform ?? "—"}</strong>

                                        <div className={styles.rowTags}>
                                            <Badge tone={session.is_active ? "focus" : "muted"}>
                                                {session.is_active
                                                    ? t("userModalSessionsActive")
                                                    : formatDateTime(session.expires_at)}
                                            </Badge>

                                            {session.is_proxy !== null && (
                                                <Badge tone={session.is_proxy ? "error" : "muted"}>
                                                    {session.is_proxy
                                                        ? t("userModalProxy")
                                                        : t("userModalDirect")}
                                                </Badge>
                                            )}
                                        </div>
                                    </div>

                                    <span className={styles.rowMeta}>
                                        <Globe/>
                                        {session.ip ?? "—"}
                                        {session.country_code
                                            ? ` · ${session.country_code}`
                                            : ""}
                                        {" · "}
                                        {session.device_name ?? session.device_id}
                                        {" · "}
                                        {formatDateTime(session.created_at)}
                                        {session.last_seen_at
                                            ? ` · ${t("userModalLastSeen")}: ${formatDateTime(session.last_seen_at)}`
                                            : ""}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* ---------- courses ---------- */}

                <section className={styles.section}>
                    <h3>
                        <BookOpen/>
                        {t("userModalCoursesTitle")}
                    </h3>

                    {!hasCourses && <p className={styles.empty}>{t("userModalCoursesEmpty")}</p>}

                    {hasCourses && (
                        <div className={styles.rows}>
                            {detail.courses.map((course) => {
                                const percent = course.lessons_total
                                    ? Math.round(
                                        (course.lessons_solved / course.lessons_total) * 100
                                    )
                                    : 0;

                                return (
                                    <div className={styles.row} key={course.course_id}>
                                        <div className={styles.rowTop}>
                                            <strong>{course.title}</strong>

                                            {!course.is_published && (
                                                <Badge tone="primary">
                                                    {t("userModalCourseUnpublished")}
                                                </Badge>
                                            )}
                                        </div>

                                        <div className={styles.progress}>
                                            <span style={{width: `${percent}%`}}/>

                                            <em>
                                                {t("userModalCourseProgress", {
                                                    solved: formatNumber(course.lessons_solved),
                                                    total: formatNumber(course.lessons_total),
                                                })}
                                            </em>
                                        </div>

                                        <span className={styles.rowMeta}>
                                            {t("userModalCourseAttempts", {
                                                count: formatNumber(course.attempts_total),
                                            })}
                                            {" · "}
                                            {t("userModalCourseEnrolled", {
                                                date: formatDateTime(course.enrolled_at),
                                            })}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </section>

                {/* ---------- recent attempts ---------- */}

                <section className={styles.section}>
                    <h3>
                        <Fingerprint/>
                        {t("userModalAttemptsTitle")}
                    </h3>

                    {!hasAttempts && <p className={styles.empty}>{t("userModalAttemptsEmpty")}</p>}

                    {hasAttempts && (
                        <div className={styles.tableWrap}>
                            <table className={styles.table}>
                                <thead>
                                <tr>
                                    <th>{t("userModalAttemptLesson")}</th>
                                    <th data-align="right">{t("userModalAttemptCorrectness")}</th>
                                    <th data-align="right">{t("userModalAttemptSpeed")}</th>
                                    <th data-align="right">{t("userModalAttemptDate")}</th>
                                </tr>
                                </thead>

                                <tbody>
                                {detail.recent_attempts.map((attempt) => (
                                    <tr key={attempt.attempt_id}>
                                        <td>{attempt.lesson_title}</td>

                                        <td data-align="right">
                                            <Badge
                                                tone={
                                                    attempt.correctness >= 3
                                                        ? "focus"
                                                        : attempt.correctness >= 2
                                                            ? "accent"
                                                            : "error"
                                                }
                                            >
                                                {attempt.correctness}/3
                                            </Badge>
                                        </td>

                                        <td data-align="right">{attempt.speed}/2</td>

                                        <td data-align="right">
                                            {formatDateTime(attempt.created_at)}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            </div>
        );
    };

    return (
        <div
            className={styles.overlay}
            onClick={onClose}
            role="presentation"
        >
            <div
                className={styles.modal}
                onClick={(event) => event.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-label={t("userModalTitle")}
            >
                <button
                    type="button"
                    className={styles.close}
                    onClick={onClose}
                    aria-label={t("userModalClose")}
                >
                    <X/>
                </button>

                {loading && renderSkeleton()}
                {!loading && error && renderError()}
                {!loading && !error && detail && renderDetail()}
            </div>
        </div>
    );
}

export default UserModal;
