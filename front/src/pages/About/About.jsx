import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./about.module.css";

import {
    ArrowRight,
    BookOpen,
    CheckCircle2,
    Code2,
    GraduationCap,
    Heart,
    Sparkles,
    Users,
} from "lucide-react";

import {Link, useNavigate} from "react-router-dom";

// TODO: заменить пути на реальные изображения
import aboutHeroImage from "@/assets/about/about.webp";
import aboutTeamImage from "@/assets/about/team.webp";
import aboutMissionImage from "@/assets/about/mission.webp";
import {ROUTES} from "@/router/AppRouter.jsx";

export function About() {
    const navigate = useNavigate();
    const t = useTranslation("about.about");

    const features = [
        {
            icon: BookOpen,
            title: t("featureEducationTitle"),
            description: t("featureEducationDescription"),
        },
        {
            icon: Code2,
            title: t("featurePracticeTitle"),
            description: t("featurePracticeDescription"),
        },
        {
            icon: Users,
            title: t("featureCommunityTitle"),
            description: t("featureCommunityDescription"),
        },
        {
            icon: Sparkles,
            title: t("featureDevelopmentTitle"),
            description: t("featureDevelopmentDescription"),
        },
    ];

    const values = [
        t("valuePractice"),
        t("valueAccessibility"),
        t("valueCommunity"),
        t("valueDevelopment"),
    ];

    return (
        <main className={styles.about}>
            {/* ---------- hero ---------- */}

            <section className={styles.hero}>
                <div className={styles.heroContent}>
                    <span className={styles.eyebrow}>
                        <Sparkles/>
                        {t("heroEyebrow")}
                    </span>

                    <h1>
                        {t("heroTitle")}
                    </h1>

                    <p>
                        {t("heroDescription")}
                    </p>

                    <div className={styles.heroActions}>
                        <Link
                            to="/courses"
                            className={styles.primaryButton}
                        >
                            <span>
                                {t("heroCoursesButton")}
                            </span>

                            <ArrowRight/>
                        </Link>

                        <a
                            href="#mission"
                            className={styles.secondaryButton}
                        >
                            {t("heroAboutButton")}
                        </a>
                    </div>
                </div>

                <div className={styles.heroImage}>
                    <img
                        src={aboutHeroImage}
                        alt={t("heroImageAlt")}
                    />

                    <div className={styles.heroImageOverlay}/>

                    <div className={styles.heroBadge}>
                        <GraduationCap/>

                        <div>
                            <strong>
                                {t("heroBadgeTitle")}
                            </strong>

                            <span>
                                {t("heroBadgeDescription")}
                            </span>
                        </div>
                    </div>
                </div>
            </section>

            {/* ---------- mission ---------- */}

            <section
                id="mission"
                className={styles.mission}
            >
                <div className={styles.sectionHeading}>
                    <span>
                        {t("missionEyebrow")}
                    </span>

                    <h2>
                        {t("missionTitle")}
                    </h2>
                </div>

                <div className={styles.missionGrid}>
                    <div className={styles.missionImage}>
                        <img
                            src={aboutMissionImage}
                            alt={t("missionImageAlt")}
                            loading="lazy"
                        />
                    </div>

                    <div className={styles.missionContent}>
                        <p className={styles.lead}>
                            {t("missionLead")}
                        </p>

                        <p>
                            {t("missionDescription")}
                        </p>

                        <div className={styles.values}>
                            {values.map((value) => (
                                <div
                                    className={styles.value}
                                    key={value}
                                >
                                    <CheckCircle2/>
                                    <span>{value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ---------- features ---------- */}

            <section className={styles.features}>
                <div className={styles.sectionHeading}>
                    <span>
                        {t("featuresEyebrow")}
                    </span>

                    <h2>
                        {t("featuresTitle")}
                    </h2>

                    <p>
                        {t("featuresDescription")}
                    </p>
                </div>

                <div className={styles.featureGrid}>
                    {features.map((feature) => {
                        const Icon = feature.icon;

                        return (
                            <article
                                className={styles.feature}
                                key={feature.title}
                            >
                                <div className={styles.featureIcon}>
                                    <Icon/>
                                </div>

                                <h3>
                                    {feature.title}
                                </h3>

                                <p>
                                    {feature.description}
                                </p>
                            </article>
                        );
                    })}
                </div>
            </section>

            {/* ---------- team ---------- */}

            <section className={styles.team}>
                <div className={styles.teamImage}>
                    <img
                        src={aboutTeamImage}
                        alt={t("teamImageAlt")}
                        loading="lazy"
                    />
                </div>

                <div className={styles.teamContent}>
                    <span className={styles.sectionEyebrow}>
                        {t("teamEyebrow")}
                    </span>

                    <h2>
                        {t("teamTitle")}
                    </h2>

                    <p>
                        {t("teamDescription")}
                    </p>

                    <div className={styles.teamStats}>
                        <div>
                            <strong>
                                {t("teamStat1Value")}
                            </strong>

                            <span>
                                {t("teamStat1Label")}
                            </span>
                        </div>

                        <div>
                            <strong>
                                {t("teamStat2Value")}
                            </strong>

                            <span>
                                {t("teamStat2Label")}
                            </span>
                        </div>

                        <div>
                            <strong>
                                {t("teamStat3Value")}
                            </strong>

                            <span>
                                {t("teamStat3Label")}
                            </span>
                        </div>
                    </div>
                </div>
            </section>

            {/* ---------- CTA ---------- */}

            <section className={styles.cta}>
                <div className={styles.ctaIcon}>
                    <Heart/>
                </div>

                <h2>
                    {t("ctaTitle")}
                </h2>

                <p>
                    {t("ctaDescription")}
                </p>

                <button
                    onClick={()=> navigate(ROUTES.courses)}
                    className={styles.primaryButton}
                >
                    <span>
                        {t("ctaButton")}
                    </span>

                    <ArrowRight/>
                </button>
            </section>
        </main>
    );
}