import {useCallback, useEffect, useState} from "react";
import {
    BookOpen,
    BookOpenCheck,
    ChevronDown,
    ChevronUp,
    Clock,
    Fingerprint,
    Globe,
    KeyRound,
    Monitor,
    ShieldCheck,
    TriangleAlert,
    UserCheck,
    UserX,
} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {useAuth} from "@/context/AuthContext.jsx";
import {formatDateTime, formatNumber} from "@/services/format.js";
import UserAvatar from "@/components/UserAvatar/UserAvatar.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import styles from "./userModal.module.css";

// сколько сессий показываем до раскрытия списка
const SESSIONS_PREVIEW = 5;

/**
 * Модальное окно с подробной карточкой пользователя.
 *
 * Данные тянет сам по userId: странице-родителю не нужно
 * держать лишнее состояние, достаточно знать id открытого пользователя.
 */
function UserModal({userId, onClose, onUserUpdated}) {
    const t = useAdminTranslation();

    const {user: authUser} = useAuth();

    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    // длинный список сессий сначала показываем укороченным
    const [showAllSessions, setShowAllSessions] = useState(false);

    // блокировка / разблокировка
    const [blocking, setBlocking] = useState(false);
    const [blockConfirm, setBlockConfirm] = useState(false);
    const [blockError, setBlockError] = useState("");

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

    const handleOpenBlockConfirm = () => {
        setBlockError("");
        setBlockConfirm(true);
    };

    const handleCancelBlock = () => {
        setBlockConfirm(false);
    };

    const handleToggleBlock = async () => {
        if (blocking || !detail) return;

        const nextBlocked = !detail.user.is_blocked;
        const url = API_ROUTES.ADMIN_USER_BLOCK(userId);

        setBlocking(true);
        setBlockConfirm(false);
        setBlockError("");

        try {
            const {data} = nextBlocked
                ? await api.post(url)
                : await api.delete(url);

            // после блокировки активные сессии отозваны — карточку надо взять заново
            await fetchDetail();

            onUserUpdated(userId, data.is_blocked);
        } catch (requestError) {
            const message =
                requestError.response?.data?.detail?.message ||
                t("userModalBlockError");

            setBlockError(message);
        } finally {
            setBlocking(false);
        }
    };

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

        // себя блокировать нельзя: админ потерял бы доступ к админке.
        // В ответе /me нет user_id, поэтому сравниваем по почте
        const isSelf = Boolean(authUser?.email) && authUser.email === user.email;

        const hasCourses = detail.courses.length > 0;
        const hasAttempts = detail.recent_attempts.length > 0;
        const hasAuth = detail.auth_methods.length > 0;
        const hasConsents = detail.consents.length > 0;
        const hasSessions = detail.sessions.length > 0;

        // показываем короткий список, полный — по кнопке
        const hiddenSessionsCount = Math.max(
            detail.sessions.length - SESSIONS_PREVIEW,
            0
        );

        const hasHiddenSessions = hiddenSessionsCount > 0;

        const visibleSessions = hasHiddenSessions && !showAllSessions
            ? detail.sessions.slice(0, SESSIONS_PREVIEW)
            : detail.sessions;

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

                            {isSelf && (
                                <Badge tone="accent" icon={UserCheck}>
                                    {t("userModalSelf")}
                                </Badge>
                            )}

                            <Badge tone="muted" icon={Clock}>
                                {t("userModalRegistered")}: {formatDateTime(user.created_at)}
                            </Badge>
                        </div>

                        {blockError && (
                            <p className={styles.blockError}>
                                <TriangleAlert/>
                                {blockError}
                            </p>
                        )}
                    </div>

                    {!isSelf && (
                        <button
                            type="button"
                            className={
                                user.is_blocked
                                    ? styles.unblockButton
                                    : styles.blockButton
                            }
                            onClick={handleOpenBlockConfirm}
                            disabled={blocking}
                        >
                            {user.is_blocked ? <UserCheck/> : <UserX/>}

                            <span>
                                {blocking
                                    ? user.is_blocked
                                        ? t("userModalUnblocking")
                                        : t("userModalBlocking")
                                    : user.is_blocked
                                        ? t("userModalUnblock")
                                        : t("userModalBlock")}
                            </span>
                        </button>
                    )}
                </header>

                {/* ---------- counters ---------- */}

                <div className={styles.counters}>
                    <div className={styles.counter} data-tone="focus">
                        <Monitor/>
                        <strong>
                            {formatNumber(detail.active_sessions)}
                            <em>/{formatNumber(detail.total_sessions)}</em>
                        </strong>
                        <span>{t("userModalSessionsRatio")}</span>
                    </div>

                    <div className={styles.counter}>
                        <BookOpen/>
                        <strong>{formatNumber(learning.enrollments)}</strong>
                        <span>{t("userModalEnrollments")}</span>
                    </div>

                    <div className={styles.counter}>
                        <BookOpenCheck/>
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
                        <>
                            <div className={styles.rows}>
                                {visibleSessions.map((session) => (
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

                            {hasHiddenSessions && (
                                <button
                                    type="button"
                                    className={styles.toggleButton}
                                    onClick={() => setShowAllSessions((current) => !current)}
                                >
                                    {showAllSessions ? (
                                        <>
                                            <ChevronUp/>
                                            {t("userModalSessionsHide")}
                                        </>
                                    ) : (
                                        <>
                                            <ChevronDown/>
                                            {t("userModalSessionsShowAll", {
                                                count: formatNumber(hiddenSessionsCount),
                                            })}
                                        </>
                                    )}
                                </button>
                            )}
                        </>
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
        <AdminModal
            onClose={onClose}
            ariaLabel={t("userModalTitle")}
            closeLabel={t("userModalClose")}
            closeOnEscape={!blockConfirm}
        >
            {loading && renderSkeleton()}
            {!loading && error && renderError()}
            {!loading && !error && detail && renderDetail()}

            {/* ---------- block confirm ---------- */}

            {blockConfirm && detail && (
                <ConfirmModal
                    icon={detail.user.is_blocked ? UserCheck : TriangleAlert}
                    tone={detail.user.is_blocked ? "ok" : "danger"}
                    title={detail.user.is_blocked
                        ? t("userModalUnblock")
                        : t("userModalBlockConfirmTitle")}
                    description={detail.user.is_blocked
                        ? ""
                        : t("userModalBlockConfirmDescription")}
                    confirmText={detail.user.is_blocked
                        ? t("userModalUnblock")
                        : t("userModalBlockConfirmOk")}
                    cancelText={t("userModalBlockConfirmCancel")}
                    busy={blocking}
                    onConfirm={handleToggleBlock}
                    onClose={handleCancelBlock}
                />
            )}
        </AdminModal>
    );
}

export default UserModal;
