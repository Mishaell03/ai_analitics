import orangeSpiral from "@/assets/artefacts/orange_spiral_3d.png";
import violetSpiral from "@/assets/artefacts/violet_spiral_3d.png";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./home.module.css";
import {ArrowRight, Award, BookOpen, GraduationCap, Layers, Sparkles, Users} from "lucide-react";
import {Link} from "react-router-dom";
import duck from "@/assets/home/smart_duck.png";
import bg from "@/assets/home/bg.webp";
import {ROUTES} from "@/router/AppRouter.jsx";

const BEGINNER_COURSE_PATH = `${ROUTES.course}/ai-development-beginner`;
const DEMO_COURSE_PATH = `${ROUTES.course}/platform-demo`;

export function Home() {
    const t = useTranslation("home.home");

    const stats = [
        {
            icon: GraduationCap,
            value: t("stats.experienceValue"),
            label: t("stats.experience"),
        },
        {
            icon: Users,
            value: t("stats.studentsValue"),
            label: t("stats.students"),
        },
        {
            icon: Award,
            value: t("stats.coursesValue"),
            label: t("stats.courses"),
        },
    ];

    const programs = [
        {
            id: "welcome",
            icon: BookOpen,
            title: t("programs.welcome.title"),
            description: t("programs.welcome.description"),
            label: t("programs.welcome.label"),
            action: t("programs.welcome.action"),
            link: DEMO_COURSE_PATH,
            featured: true,
        },
        {
            id: "analytics",
            icon: Layers,
            title: t("programs.analytics.title"),
            description: t("programs.analytics.description"),
            label: t("programs.analytics.label"),
            action: t("programs.analytics.action"),
            link: BEGINNER_COURSE_PATH,
        },
        {
            id: "ai",
            icon: Sparkles,
            title: t("programs.ai.title"),
            description: t("programs.ai.description"),
            label: t("programs.ai.label"),
            action: t("programs.ai.action"),
            link: ROUTES.about_us,
        },
        {
            id: "teachers",
            icon: Users,
            title: t("programs.teachers.title"),
            description: t("programs.teachers.description"),
            label: t("programs.teachers.label"),
            action: t("programs.teachers.action"),
            link: ROUTES.teachers,
        },
    ];

    return (
        <div className={styles.home}>
            <img
                src={orangeSpiral}
                className={styles.artefact}
                data-pos="1"
                alt=""
            />
            <img
                src={violetSpiral}
                className={styles.artefact}
                data-pos="2"
                alt=""
            />
            <img
                src={orangeSpiral}
                className={styles.artefact}
                data-pos="3"
                alt=""
            />
            <img
                src={violetSpiral}
                className={styles.artefact}
                data-pos="4"
                alt=""
            />

            <section className={styles.hero}>
                <div className={styles.heroText}>
                    <div className={styles.badge}>
                        {t("hero.badge")}
                    </div>

                    <h1>
                        DataLab
                        <span className={styles.heroSub}>
                            {t("hero.subtitle")}
                        </span>
                    </h1>

                    <p className={styles.heroDescription}>
                        {t("hero.description")}
                    </p>

                    <div className={styles.heroActions}>
                        <Link to={DEMO_COURSE_PATH} className={styles.primaryButton}>
                            {t("hero.primaryAction")}
                        </Link>

                        <Link
                            to={ROUTES.teachers}
                            className={styles.secondaryLink}
                        >
                            {t("hero.secondaryAction")}
                        </Link>
                    </div>
                </div>

                <div
                    className={styles.heroCard}
                    style={{
                        "--card-image": `url(${bg})`,
                    }}
                >
                    <img src={duck} alt={t("hero.mentorAlt")}/>

                    <div className={styles.heroCardBadge}>
                        <p>{t("hero.mentorLabel")}</p>
                        <span>{t("hero.mentorName")}</span>
                    </div>
                </div>
            </section>

            <section className={styles.stats}>
                {stats.map(({icon: Icon, value, label}) => (
                    <div className={styles.statCard} key={value}>
                        <div className={styles.statIcon}>
                            <Icon/>
                        </div>

                        <div>
                            <p className={styles.statValue}>
                                {value}
                            </p>

                            <p className={styles.statLabel}>
                                {label}
                            </p>
                        </div>
                    </div>
                ))}
            </section>

            <section className={styles.curatorBox}>
                <div className={styles.curatorAvatar}>
                    <Users/>
                </div>

                <div>
                    <p className={styles.curatorName}>
                        <span>{t("teachers.label")}{" "}</span>
                    </p>

                    <p className={styles.curatorText}>
                        {t("teachers.description")}
                    </p>
                </div>
                <img
                    src={violetSpiral}
                    className={styles.artefact}
                    data-pos="5"
                    alt=""
                />
            </section>

            <section className={styles.programs} aria-labelledby="home-programs-title">
                <h2 id="home-programs-title">
                    {t("programs.title")}{" "}
                    <span>{t("programs.highlight")}</span>
                </h2>
                <p className={styles.programsDescription}>{t("programs.description")}</p>

                <div className={styles.programList}>
                    <img
                        src={orangeSpiral}
                        className={styles.artefact}
                        data-pos="6"
                        alt=""
                    />
                    {programs.map(
                        ({id, icon: Icon, title, description, label, action, link, featured}) => (
                            <Link
                                to={link}
                                className={styles.programCard}
                                data-featured={featured || undefined}
                                aria-labelledby={`program-${id}`}
                                key={id}
                            >
                                <div className={styles.programCardHeader}>
                                    <span className={styles.programIcon}>
                                        <Icon aria-hidden="true"/>
                                    </span>
                                    <span className={styles.programLabel}>{label}</span>
                                </div>

                                <div className={styles.programBody}>
                                    <h3 id={`program-${id}`}>{title}</h3>
                                    <p>{description}</p>
                                </div>

                                <span className={styles.programButton}>
                                    {action}
                                    <ArrowRight aria-hidden="true"/>
                                </span>
                            </Link>
                        )
                    )}
                </div>
                <img
                    src={violetSpiral}
                    className={styles.artefact}
                    data-pos="7"
                    alt=""
                />
            </section>
        </div>
    );
}
