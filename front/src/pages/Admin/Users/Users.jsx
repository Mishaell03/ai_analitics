import {useCallback, useState} from "react";
import {
    Inbox,
    ShieldCheck,
    TriangleAlert,
    UserX,
    Users as UsersIcon,
} from "lucide-react";
import {formatNumber} from "@/services/format.js";
import UserAvatar from "@/components/UserAvatar/UserAvatar.jsx";
import Badge from "@/components/Badge/Badge.jsx";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import AdminPageHeader from "@/pages/Admin/components/AdminPageHeader.jsx";
import AdminPagination from "@/pages/Admin/components/AdminPagination.jsx";
import pageStyles from "@/pages/Admin/components/adminPage.module.css";
import {useAdminAccess} from "@/pages/Admin/hooks/useAdminAccess.js";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import UserModal from "./UserModal.jsx";
import {PER_PAGE, useUsers} from "./useUsers.js";
import styles from "./users.module.css";

const SKELETON_ROWS = PER_PAGE;

/**
 * Реестр пользователей: список, переход к карточке и блокировка.
 */
export function Users() {
    const t = useAdminTranslation();

    const {
        users,
        page,
        totalPages,
        loading,
        error,
        reload,
        goToPreviousPage,
        goToNextPage,
        updateUserBlocked,
    } = useUsers();

    const {authLoading, isForbidden} = useAdminAccess(error);

    const [selectedUserId, setSelectedUserId] = useState(null);

    const handleCloseModal = useCallback(() => {
        setSelectedUserId(null);
    }, []);

    // прав нет ни у гостя, ни у пользователя, ни по ответу бэкенда
    if (isForbidden) {
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
                            className={pageStyles.retryButton}
                            onClick={reload}
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
            <td><span className={pageStyles.skeletonCell} data-width="30%"/></td>

            <td>
                <div className={pageStyles.skeletonUser}>
                    <span className={pageStyles.skeletonAvatar}/>
                    <span className={pageStyles.skeletonCell} data-width="60%"/>
                </div>
            </td>

            <td><span className={pageStyles.skeletonCell} data-width="75%"/></td>
            <td><span className={pageStyles.skeletonCell} data-width="55%"/></td>
            <td><span className={pageStyles.skeletonCell} data-width="45%"/></td>
        </tr>
    );

    return (
        <div className={styles.users}>
            <AdminPageHeader
                eyebrow={t("usersPageEyebrow")}
                title={t("usersPageTitle")}
                subtitle={t("usersPageSubtitle")}
                onRefresh={reload}
                refreshing={pending}
                refreshLabel={t("refreshButton")}
                refreshingLabel={t("refreshProcess")}
            />

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

            {!pending && users.length > 0 && (
                <AdminPagination
                    page={page}
                    totalPages={totalPages}
                    onPrevious={goToPreviousPage}
                    onNext={goToNextPage}
                    label={t("paginationInfo", {
                        page: formatNumber(page),
                        total: formatNumber(totalPages),
                    })}
                    previousLabel={t("paginationPrev")}
                    nextLabel={t("paginationNext")}
                />
            )}

            {selectedUserId !== null && (
                <UserModal
                    key={selectedUserId}
                    userId={selectedUserId}
                    onClose={handleCloseModal}
                    onUserUpdated={updateUserBlocked}
                />
            )}
        </div>
    );
}
