import {useState} from "react";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./markdown.module.css";

// Эталоны намеренно не принимаются в props: ввод содержит только код ученика.
function MarkdownCodeExercise({block, onCheck}) {
    const t = useTranslation("courses.course");
    const [code, setCode] = useState("");
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState("");
    const {exercise_id: exerciseId, language, valid} = block.data ?? {};

    const run = async () => {
        if (!onCheck || busy || !code.trim()) return;
        setBusy(true);
        setResult("");
        try {
            const response = await onCheck(exerciseId, JSON.stringify({type: "code", value: code}),
                {execute: true, language, code});
            setResult([response.stdout, response.stderr,
                t("codeExerciseExit", {code: response.exit_code}),
                response.is_correct === true ? t("codeExerciseCorrect")
                    : response.is_correct === false ? t("codeExerciseIncorrect")
                        : t("codeExerciseNotGraded")].filter(Boolean).join("\n"));
        } catch (error) {
            const status = error?.response?.status;
            setResult(status === 503 ? t("codeExerciseUnavailable", {language: language.toUpperCase()})
                : status === 403 ? t("codeExerciseForbidden") : t("codeExerciseError"));
        } finally {
            setBusy(false);
        }
    };

    if (!valid) return <p role="alert">{t("codeExerciseInvalid")}</p>;
    return <section className={styles.testBlock}>
        <div className={styles.testHeader}>{language.toUpperCase()} · {exerciseId}</div>
        <label className={styles.codeExerciseLabel}>
            {t("codeExerciseSolution")}
            <textarea className={styles.codeExerciseInput} value={code} maxLength={8000}
                      onChange={(event) => setCode(event.target.value)} rows={8}
                      spellCheck={false} disabled={busy}/>
        </label>
        <div className={styles.testActions}>
            <button type="button" className={styles.testCheckButton} disabled={!onCheck || busy || !code.trim()}
                    onClick={run}>{t("codeExerciseRun")}</button>
        </div>
        {result && <pre className={styles.codeExerciseOutput} role="status">{result}</pre>}
    </section>;
}

export default MarkdownCodeExercise;
