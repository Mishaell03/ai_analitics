import {getTranslation} from "@/locales/i18n.js";
import styles from "./teachers.module.css";

import {
    ArrowRight,
    CheckCircle2,
    GraduationCap,
    Plus,
    Sparkles,
    UserPlus,
} from "lucide-react";

import {Link, useNavigate} from "react-router-dom";

import teamPhoto from "@/assets/teacher/hero_teacher.webp";
import teacher1Photo from "@/assets/teacher/teacher1.webp";
import teacher2Photo from "@/assets/teacher/teacher2.webp";
import teacher3Photo from "@/assets/teacher/teacher3.webp";
import teacher4Photo from "@/assets/teacher/teacher4.webp";
import teacher5Photo from "@/assets/teacher/teacher5.webp";
import teacher6Photo from "@/assets/teacher/teacher6.webp";
import {ROUTES} from "@/router/AppRouter.jsx";

const language = "ru";

export function Teachers() {
    const navigate = useNavigate();
    const t = (key) => getTranslation(`teachers.teachers.${key}`, language);

    const aiPoints = [
        t("pairAiPoint1"),
        t("pairAiPoint2"),
        t("pairAiPoint3"),
        t("pairAiPoint4"),
    ];

    const humanPoints = [
        t("pairHumanPoint1"),
        t("pairHumanPoint2"),
        t("pairHumanPoint3"),
        t("pairHumanPoint4"),
    ];

    const teachers = [
        {
            name: t("teacher1Name"),
            role: t("teacher1Role"),
            description: t("teacher1Description"),
            tags: [t("teacher1Tag1"), t("teacher1Tag2"), t("teacher1Tag3")],
            photo: teacher1Photo,
        },
        {
            name: t("teacher2Name"),
            role: t("teacher2Role"),
            description: t("teacher2Description"),
            tags: [t("teacher2Tag1"), t("teacher2Tag2"), t("teacher2Tag3")],
            photo: teacher2Photo,
        },
        {
            name: t("teacher3Name"),
            role: t("teacher3Role"),
            description: t("teacher3Description"),
            tags: [t("teacher3Tag1"), t("teacher3Tag2"), t("teacher3Tag3")],
            photo: teacher3Photo,
        },
        {
            name: t("teacher4Name"),
            role: t("teacher4Role"),
            description: t("teacher4Description"),
            tags: [t("teacher4Tag1"), t("teacher4Tag2"), t("teacher4Tag3")],
            photo: teacher4Photo,
        },
        {
            name: t("teacher5Name"),
            role: t("teacher5Role"),
            description: t("teacher5Description"),
            tags: [t("teacher5Tag1"), t("teacher5Tag2"), t("teacher5Tag3")],
            photo: teacher5Photo,
        },
        {
            name: t("teacher6Name"),
            role: t("teacher6Role"),
            description: t("teacher6Description"),
            tags: [t("teacher6Tag1"), t("teacher6Tag2"), t("teacher6Tag3")],
            photo: teacher6Photo,
        },
    ];

    const growPoints = [
        t("growPoint1"),
        t("growPoint2"),
        t("growPoint3"),
        t("growPoint4"),
    ];

    const growStats = [
        {
            value: t("growStat1Value"),
            label: t("growStat1Label"),
        },
        {
            value: t("growStat2Value"),
            label: t("growStat2Label"),
        },
        {
            value: t("growStat3Value"),
            label: t("growStat3Label"),
        },
    ];

    return (
        <main className={styles.teachers}>
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
                            to={ROUTES.courses}
                            className={styles.primaryButton}
                        >
                            <span>
                                {t("heroCoursesButton")}
                            </span>

                            <ArrowRight/>
                        </Link>

                        <a
                            href="#team"
                            className={styles.secondaryButton}
                        >
                            {t("heroTeamButton")}
                        </a>
                    </div>
                </div>

                <div className={styles.heroImage}>
                    <img
                        src={teamPhoto}
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

            {/* ---------- AI + teachers ---------- */}

            <section className={styles.pair}>
                <div className={styles.sectionHeading}>
                    <span>
                        {t("pairEyebrow")}
                    </span>

                    <h2>
                        {t("pairTitle")}
                    </h2>

                    <p>
                        {t("pairDescription")}
                    </p>
                </div>

                <div className={styles.pairGrid}>
                    <article className={styles.pairCard}>
                        <div className={styles.pairHead}>
                            <div className={styles.pairIcon}>
                                <Sparkles/>
                            </div>

                            <div>
                                <h3>
                                    {t("pairAiTitle")}
                                </h3>

                                <span className={styles.pairTagline}>
                                    {t("pairAiTagline")}
                                </span>
                            </div>
                        </div>



                        <ul className={styles.pairList}>
                            {aiPoints.map((point) => (
                                <li key={point}>
                                    <CheckCircle2/>
                                    <span>{point}</span>
                                </li>
                            ))}
                        </ul>
                    </article>

                    <div className={styles.pairPlus}>
                        <Plus/>
                    </div>

                    <article className={styles.pairCard}>
                        <div className={styles.pairHead}>
                            <div className={styles.pairIcon}>
                                <GraduationCap/>
                            </div>

                            <div>
                                <h3>
                                    {t("pairHumanTitle")}
                                </h3>

                                <span className={styles.pairTagline}>
                                    {t("pairHumanTagline")}
                                </span>
                            </div>
                        </div>

                        <ul className={styles.pairList}>
                            {humanPoints.map((point) => (
                                <li key={point}>
                                    <CheckCircle2/>
                                    <span>{point}</span>
                                </li>
                            ))}
                        </ul>
                    </article>
                </div>
            </section>

            {/* ---------- team ---------- */}

            <section
                id="team"
                className={styles.team}
            >
                <div className={styles.sectionHeading}>
                    <span>
                        {t("teamEyebrow")}
                    </span>

                    <h2>
                        {t("teamTitle")}
                    </h2>

                    <p>
                        {t("teamDescription")}
                    </p>
                </div>

                <div className={styles.teacherGrid}>
                    {teachers.map((teacher) => (
                        <article
                            className={styles.teacherCard}
                            key={teacher.name}
                        >
                            <div className={styles.teacherPhoto}>
                                <img
                                    src={teacher.photo}
                                    alt={teacher.name}
                                    loading="lazy"
                                />

                                <div className={styles.teacherRole}>
                                    {teacher.role}
                                </div>
                            </div>

                            <div className={styles.teacherBody}>
                                <h3>
                                    {teacher.name}
                                </h3>

                                <p>
                                    {teacher.description}
                                </p>

                                <div className={styles.teacherTags}>
                                    {teacher.tags.map((tag) => (
                                        <span key={tag}>
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            {/* ---------- grow ---------- */}

            <section className={styles.grow}>
                <div className={styles.growContent}>
                    <span className={styles.sectionEyebrow}>
                        {t("growEyebrow")}
                    </span>

                    <h2>
                        {t("growTitle")}
                    </h2>

                    <p>
                        {t("growDescription")}
                    </p>

                    <div className={styles.growPoints}>
                        {growPoints.map((point) => (
                            <div
                                className={styles.growPoint}
                                key={point}
                            >
                                <CheckCircle2/>
                                <span>{point}</span>
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={() => navigate(ROUTES.registration)}
                        className={styles.primaryButton}
                    >
                        <UserPlus/>
                        <span>
                            {t("growButton")}
                        </span>
                    </button>
                </div>

                <div className={styles.growStats}>
                    {growStats.map((stat) => (
                        <div
                            className={styles.growStat}
                            key={stat.label}
                        >
                            <strong>
                                {stat.value}
                            </strong>

                            <span>
                                {stat.label}
                            </span>
                        </div>
                    ))}
                </div>
            </section>

            {/* ---------- CTA ---------- */}

            <section className={styles.cta}>
                <div className={styles.ctaIcon}>
                    <Sparkles/>
                </div>

                <h2>
                    {t("ctaTitle")}
                </h2>

                <p>
                    {t("ctaDescription")}
                </p>

                <button
                    onClick={() => navigate(ROUTES.courses)}
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