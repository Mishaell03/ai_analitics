import {useCallback, useEffect, useState} from "react";
import {
    Inbox,
    RefreshCw,
    ShieldCheck,
    TriangleAlert,
    UserX,
    Users as UsersIcon,
} from "lucide-react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {useAuth} from "@/context/AuthContext.jsx";
import {getTranslation} from "@/locales/i18n.js";
import {formatNumber} from "@/services/format.js";
import UserAvatar from "@/components/UserAvatar/UserAvatar.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import UserModal from "@/pages/Admin/UserModal.jsx";
import styles from "./users.module.css";

const language = "ru";

const PER_PAGE = 10;
const SKELETON_ROWS = PER_PAGE;

export function Users() {
    const {user, loading: authLoading} = useAuth();

    const t = (key, params) => getTranslation(`admin.admin.${key}`, language, params);

    const [users, setUsers] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedUserId, setSelectedUserId] = useState(null);

    const fetchUsers = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_USERS, {
                params: {
                    page,
                    per_page: PER_PAGE,
                },
            });

            setUsers(data.users ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleNextPage = () => {
        setPage((current) => Math.min(totalPages, current + 1));
    };

    const handlePreviousPage = () => {
        setPage((current) => Math.max(1, current - 1));
    };

    const handleCloseModal = useCallback(() => {
        setSelectedUserId(null);
    }, []);

    // прав нет ни у гостя, ни у пользователя, ни по ответу бэкенда
    if (error === "forbidden" || (!authLoading && !user?.is_admin)) {
        return (
            <main className={styles.users}>
                <EmptyState
                    icon={ShieldCheck}
                    title={t("forbiddenTitle")}
                    description={t("forbiddenDescription")}
                />
            </main>
        );
    }

    if (error) {
        return (
            <main className={styles.users}>
                <EmptyState
                    icon={TriangleAlert}
                    title={t("usersPageErrorTitle")}
                    description={t("errorDescription")}
                    action={
                        <button
                            type="button"
                            className={styles.retryButton}
                            onClick={fetchUsers}
                        >
                            {t("usersPageErrorRetry")}
                        </button>
                    }
                />
            </main>
        );
    }

    const pending = authLoading || loading;

    const renderSkeletonRow = (index) => (
        <tr className={styles.row} key={index}>
            <td><span className={styles.skeletonCell} data-width="30%"/></td>

            <td>
                <div className={styles.skeletonUser}>
                    <span className={styles.skeletonAvatar}/>
                    <span className={styles.skeletonCell} data-width="60%"/>
                </div>
            </td>

            <td><span className={styles.skeletonCell} data-width="75%"/></td>
            <td><span className={styles.skeletonCell} data-width="55%"/></td>
            <td><span className={styles.skeletonCell} data-width="45%"/></td>
        </tr>
    );

    return (
        <dev className={styles.users}>

            {/* ---------- heading ---------- */}

            <section className={styles.heading}>
                <div className={styles.badge}>
                    <span className={styles.badgeDot}/>
                    {t("usersPageEyebrow")}
                </div>

                <div className={styles.headingRow}>
                    <div className={styles.headingContent}>
                        <h1>{t("usersPageTitle")}</h1>
                        <p>{t("usersPageSubtitle")}</p>
                    </div>

                    <button
                        type="button"
                        className={styles.refreshButton}
                        onClick={fetchUsers}
                        disabled={pending}
                    >
                        <RefreshCw/>
                        <span>
                            {pending ? t("refreshProcess") : t("refreshButton")}
                        </span>
                    </button>
                </div>
            </section>

            {/* ---------- table ---------- */}

            <section className={styles.panel}>
                {pending && (
                    <table className={styles.table} aria-busy="true">
                        <thead>
                        <tr>
                            <th>{t("usersColumnId")}</th>
                            <th>{t("usersColumnName")}</th>
                            <th>{t("usersColumnEmail")}</th>
                            <th>{t("usersColumnPhone")}</th>
                            <th data-align="right">{t("usersColumnStatus")}</th>
                        </tr>
                        </thead>

                        <tbody>
                        {Array.from({length: SKELETON_ROWS}, (_, index) => renderSkeletonRow(index))}
                        </tbody>
                    </table>
                )}

                {!pending && users.length === 0 && (
                    <EmptyState
                        icon={Inbox}
                        title={t("usersPageEmptyTitle")}
                        description={t("usersPageEmptyDescription")}
                    />
                )}

                {!pending && users.length > 0 && (
                    <div className={styles.tableWrap}>
                        <table className={styles.table}>
                            <thead>
                            <tr>
                                <th>{t("usersColumnId")}</th>
                                <th>{t("usersColumnName")}</th>
                                <th>{t("usersColumnEmail")}</th>
                                <th>{t("usersColumnPhone")}</th>
                                <th data-align="right">{t("usersColumnStatus")}</th>
                            </tr>
                            </thead>

                            <tbody>
                            {users.map((item) => (
                                <tr
                                    className={styles.row}
                                    key={item.user_id}
                                    onClick={() => setSelectedUserId(item.user_id)}
                                    tabIndex={0}
                                    role="button"
                                    aria-label={item.name || item.email}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter") {
                                            setSelectedUserId(item.user_id);
                                        }
                                    }}
                                >
                                    <td className={styles.cellId}>
                                        {formatNumber(item.user_id)}
                                    </td>

                                    <td>
                                        <div className={styles.user}>
                                            <UserAvatar
                                                url={item.img_url}
                                                name={item.name}
                                                email={item.email}
                                            />

                                            <span className={styles.userName}>
                                                {item.name || t("usersNameEmpty")}
                                            </span>
                                        </div>
                                    </td>

                                    <td className={styles.cellMuted}>{item.email}</td>

                                    <td className={styles.cellMuted}>
                                        {item.phone || t("usersPhoneEmpty")}
                                    </td>

                                    <td data-align="right">
                                        <div className={styles.status}>
                                            {item.is_blocked ? (
                                                <Badge tone="error" icon={UserX}>
                                                    {t("usersRoleBlocked")}
                                                </Badge>
                                            ) : item.is_admin ? (
                                                <Badge tone="accent" icon={ShieldCheck}>
                                                    {t("usersRoleAdmin")}
                                                </Badge>
                                            ) : (
                                                <Badge tone="muted" icon={UsersIcon}>
                                                    {t("usersRoleUser")}
                                                </Badge>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* ---------- pagination ---------- */}

            {!pending && users.length > 0 && totalPages > 1 && (
                <nav className={styles.pagination}>
                    <button
                        type="button"
                        className={styles.pageButton}
                        onClick={handlePreviousPage}
                        disabled={page <= 1}
                        aria-label={t("paginationPrev")}
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
                        aria-label={t("paginationNext")}
                    >
                        ›
                    </button>
                </nav>
            )}

            {selectedUserId !== null && (
                <UserModal
                    userId={selectedUserId}
                    onClose={handleCloseModal}
                />
            )}
        </dev>
    );
}
