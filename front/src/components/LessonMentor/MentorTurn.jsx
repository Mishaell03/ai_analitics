import {useEffect, useState} from "react";
import {AlertCircle, Check, Copy, Sparkles} from "lucide-react";
import {useTranslation} from "@/hooks/useTranslation.js";
import MentorText from "./MentorText.jsx";
import styles from "./lessonMentor.module.css";

export default function MentorTurn({item}) {
    const t = useTranslation("courses.course");
    const [copyState, setCopyState] = useState(null);

    useEffect(() => {
        if (!copyState) return;
        const timer = setTimeout(() => setCopyState(null), 2500);
        return () => clearTimeout(timer);
    }, [copyState]);

    async function copyAnswer() {
        try {
            await navigator.clipboard.writeText(item.answer);
            setCopyState("copied");
        } catch {
            setCopyState("failed");
        }
    }

    return <article className={styles.turn}>
        <div className={styles.studentMessage}>
            <span className={styles.studentLabel}>{t("mentorStudent")}</span>
            <p className={styles.studentBubble}>{item.question}</p>
        </div>
        <div className={styles.assistantMessage}>
            <div className={styles.messageHeading}>
                <span className={styles.miniAvatar}><Sparkles aria-hidden="true"/></span>
                <span>{t("mentorName")}</span>
                {item.status === "completed" && item.answer && <button type="button" className={styles.copyButton}
                    onClick={copyAnswer} title={t(copyState === "copied" ? "mentorCopied" : "mentorCopy")}
                    aria-label={t(copyState === "copied" ? "mentorCopied" : "mentorCopy")}>
                    {copyState === "copied" ? <Check aria-hidden="true"/> : <Copy aria-hidden="true"/>}
                </button>}
            </div>
            <div className={styles.assistantBubble} data-status={item.status}>
                {item.status === "pending" ? <div className={styles.typing} role="status">
                    <span className={styles.typingDots} aria-hidden="true"><i/><i/><i/></span>
                    <span>{t("mentorThinking")}</span>
                </div> : <>
                    {item.status === "failed" && <AlertCircle className={styles.failureIcon} aria-hidden="true"/>}
                    <MentorText text={item.answer ?? t("mentorWaiting")}/>
                </>}
            </div>
            {item.status === "failed" && <p className={styles.messageNote}>{t("mentorFailed")}</p>}
            {copyState && <span className={styles.copyFeedback} role="status">
                {t(copyState === "copied" ? "mentorCopied" : "mentorCopyFailed")}
            </span>}
        </div>
    </article>;
}
