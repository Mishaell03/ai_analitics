import {Link, NavLink} from "react-router-dom";
import {ArrowLeft, Flag} from "lucide-react";
import {useAuth} from "@/context/AuthContext.jsx";
import {getTranslation} from "@/locales/i18n.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import Avatar from "@/components/Avatar/Avatar.jsx";
import {ADMIN_NAV} from "@/pages/Admin/adminNav.js";
import styles from "./adminSidebar.module.css";

const language = "ru";

/**
 * Боковая панель админки.
 *
 * На широких экранах — вертикальный список, прилипает при скролле.
 * На узких превращается в горизонтальную ленту ссылок,
 * поэтому не нужно открывать её по кнопке.
 */
function AdminSidebar() {
    const {user} = useAuth();

    const t = (key) => getTranslation(`admin.admin.${key}`, language);

    const renderItem = (item) => {
        const {icon: Icon} = item;

        if (item.soon) {
            return (
                <span className={styles.item} data-soon="true" key={item.title}>
                    <Icon/>

                    <span className={styles.itemText}>{t(item.title)}</span>

                    <span className={styles.soon}>{t("sidebarSoon")}</span>
                </span>
            );
        }

        return (
            <NavLink
                to={item.path}
                end
                className={({isActive}) =>
                    `${styles.item} ${isActive ? styles.active : ""}`
                }
                key={item.title}
            >
                <Icon/>

                <span className={styles.itemText}>{t(item.title)}</span>
            </NavLink>
        );
    };

    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>
                <span className={styles.brandIcon}>
                    <Flag/>
                </span>

                <div className={styles.brandText}>
                    <strong>{t("badge")}</strong>
                    <span>{user?.email}</span>
                </div>
            </div>

            <nav className={styles.nav}>
                {ADMIN_NAV.map((group) => (
                    <div className={styles.group} key={group.title}>
                        <span className={styles.groupTitle}>
                            {t(group.title)}
                        </span>

                        <div className={styles.groupItems}>
                            {group.items.map(renderItem)}
                        </div>
                    </div>
                ))}
            </nav>

            <div className={styles.footer}>
                <div className={styles.user}>
                    <Avatar/>

                    <div className={styles.userText}>
                        <strong>{user?.name || t("usersNameEmpty")}</strong>
                        <span>{t("sidebarRole")}</span>
                    </div>
                </div>

                <Link to={ROUTES.home} className={styles.back}>
                    <ArrowLeft/>
                    <span>{t("sidebarBack")}</span>
                </Link>
            </div>
        </aside>
    );
}

export default AdminSidebar;
