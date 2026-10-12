import {NavLink} from "react-router-dom";
import {useState} from "react";
import {useAuth} from "@/context/AuthContext.jsx";
import {getTranslation} from "@/locales/i18n.js";
import {Menu, X} from "lucide-react";
import {ROUTES} from "@/router/AppRouter.jsx";

import Avatar from "@/components/Avatar/Avatar.jsx";
import styles from "./header.module.css";

const language = "ru";

function Header() {
    const [open, setOpen] = useState(false);
    const {user} = useAuth();
    const t = (key) => getTranslation(`layouts.header.${key}`, language);

    const navigation = [
        {
            title: t("home"),
            path: ROUTES.home,
        },
        {
            title: t("courses"),
            path: ROUTES.courses,
        },
        {
            title: t("teachers"),
            path: ROUTES.teachers,
        },
        {
            title: t("about_us"),
            path: ROUTES.about_us,
        },

        // доступно только администраторам
        ...(user?.is_admin
            ? [{title: t("admin"), path: ROUTES.admin}]
            : []),
    ];


    const linkClass = ({isActive}) =>
        `${styles.navLink} ${
            isActive ? styles.active : ""
        }`;


    const authBlock = (
        user ? (
            <NavLink
                to={ROUTES.profile}
                className={styles.profile}
                onClick={() => setOpen(false)}
            >

                <Avatar/>
            </NavLink>
        ) : (
            <>
                <NavLink
                    to={ROUTES.login}
                    className={({isActive}) =>
                        `${styles.login} ${
                            isActive ? styles.activeButton : ""
                        }`
                    }
                    onClick={() => setOpen(false)}
                >
                    {t("login")}
                </NavLink>


                <NavLink
                    to={ROUTES.registration}
                    className={({isActive}) =>
                        `${styles.registration} ${
                            isActive ? styles.activeButton : ""
                        }`
                    }
                    onClick={() => setOpen(false)}
                >
                    {t("registration")}
                </NavLink>
            </>
        )
    );


    return (
        <header className={styles.wrapper}>

            <div className={styles.header}>

                <div className={styles.logo}>
                    <NavLink to={ROUTES.home}>
                        <img
                            src="/icon.png"
                            alt={t("logo_alt")}
                        />

                        <h1>
                            Duck docs
                        </h1>
                    </NavLink>
                </div>


                <nav className={styles.desktop}>
                    {navigation.map((item) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={linkClass}
                        >
                            {item.title}
                        </NavLink>
                    ))}
                </nav>


                <div className={styles.info}>
                    {authBlock}
                </div>


                <button
                    type="button"
                    className={styles.burger}
                    onClick={() => setOpen((prev) => !prev)}
                >
                    {open ? <X/> : <Menu/>}
                </button>

            </div>


            <div
                className={`${styles.mobileMenu} ${
                    open ? styles.active : ""
                }`}
            >

                {navigation.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={linkClass}
                        onClick={() => setOpen(false)}
                    >
                        {item.title}
                    </NavLink>
                ))}


                <div className={styles.mobileAuth}>
                    {authBlock}
                </div>

            </div>

        </header>
    );
}


export default Header;