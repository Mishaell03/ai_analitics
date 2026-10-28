import {ArrowUpRight, BookOpen, Lightbulb, Sparkles} from "lucide-react";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./lessonMentor.module.css";

export default function MentorWelcome({onPrompt, disabled}) {
    const t = useTranslation("courses.course");
    return <div className={styles.welcome}>
        <div className={styles.welcomeArt} aria-hidden="true">
            <span className={styles.orbit}/>
            <span className={styles.welcomeBook}><BookOpen/></span>
            <span className={styles.orbitSpark}><Sparkles/></span>
            <span className={styles.orbitBulb}><Lightbulb/></span>
        </div>
        <span className={styles.welcomeEyebrow}>{t("mentorWelcomeEyebrow")}</span>
        <h3>{t("mentorWelcomeTitle")}</h3>
        <p>{t("mentorWelcomeDescription")}</p>
        <div className={styles.suggestions} aria-label={t("mentorSuggestions")}>
            {["mentorPromptExplain", "mentorPromptExample", "mentorPromptHint"].map(key =>
                <button type="button" key={key} disabled={disabled} onClick={() => onPrompt(t(key))}>
                    <span>{t(key)}</span><ArrowUpRight aria-hidden="true"/>
                </button>
            )}
        </div>
    </div>;
}
