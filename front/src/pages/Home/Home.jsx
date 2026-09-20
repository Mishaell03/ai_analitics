import orangeSpiral from "@/assets/artefacts/orange_spiral_3d.png";
import violetSpiral from "@/assets/artefacts/violet_spiral_3d.png";
import {getTranslation} from "@/locales/i18n.js";
import styles from "./home.module.css";
import {
    ArrowRight,
    Award,
    Briefcase,
    GraduationCap,
    Layers,
    ShoppingBag,
    Tags,
    Users,
} from "lucide-react";
import {Link} from "react-router-dom";
import duck from "@/assets/home/smart_duck.png";
import bg from "@/assets/home/bg.webp";

const language = "ru";

export function Home() {
    const t = (key) => getTranslation(`home.home.${key}`, language);

    const stats = [
        {
            icon: GraduationCap,
            value: "0 лет",
            label: t("stats.experience"),
        },
        {
            icon: Users,
            value: "< 500 000 учеников",
            label: t("stats.students"),
        },
        {
            icon: Award,
            value: "< 30 курсов",
            label: t("stats.courses"),
        },
    ];

    const programs = [
        {
            icon: Layers,
            title: t("programs.analytics.title"),
            description: t("programs.analytics.description"),
        },
        {
            icon: Tags,
            title: t("programs.ai.title"),
            description: t("programs.ai.description"),
        },
        {
            icon: ShoppingBag,
            title: t("programs.teachers.title"),
            description: t("programs.teachers.description"),
        },
        {
            icon: Briefcase,
            title: t("programs.career.title"),
            description: t("programs.career.description"),
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
                        DUCK DOCS
                        <span className={styles.heroSub}>
                            {t("hero.subtitle")}
                        </span>
                    </h1>

                    <p className={styles.heroDescription}>
                        {t("hero.description")}
                    </p>

                    <div className={styles.heroActions}>
                        <button className={styles.primaryButton}>
                            {t("hero.primaryAction")}
                        </button>

                        <Link
                            to="/curator"
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
                    <img src={duck} alt={t("hero.mentorAlt")} />

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

            <section className={styles.programs}>
                <h2>
                    {t("programs.title")}{" "}
                    <span>{t("programs.highlight")}</span>
                </h2>

                <div className={styles.programList}>
                    <img
                        src={orangeSpiral}
                        className={styles.artefact}
                        data-pos="6"
                        alt=""
                    />
                    {programs.map(
                        ({icon: Icon, title, description}) => (
                            <div
                                className={styles.programCard}
                                key={title}
                            >
                                <div className={styles.programIcon}>
                                    <Icon/>
                                </div>

                                <div className={styles.programBody}>
                                    <h3>{title}</h3>
                                    <p>{description}</p>
                                </div>

                                <button className={styles.programButton}>
                                    {t("programs.action")}
                                    <ArrowRight/>
                                </button>
                            </div>
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