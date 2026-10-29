import {useState} from "react";
import {useTranslation} from "@/hooks/useTranslation.js";
import MarkdownExpertSolution from "./MarkdownExpertSolution.jsx";
import MarkdownPlots from "./MarkdownPlots.jsx";
import styles from "./markdown.module.css";

// Доступ к эталону подтверждает сервер: проверка или запуск для самопроверки.
function MarkdownCodeExercise({block, onCheck, completed = false, expertSolutionAvailable = false, onExpertSolution}) {
    const t = useTranslation("courses.course");
    const [code, setCode] = useState("");
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState("");
    const [plots, setPlots] = useState([]);
    const [passed, setPassed] = useState(false);
    const [checkedAccess, setCheckedAccess] = useState(null);
    const {exercise_id: exerciseId, language, valid} = block.data ?? {};

    const run = async () => {
        if (!onCheck || busy || !code.trim()) return;
        setBusy(true);
        setResult("");
        setPlots([]);
        try {
            const response = await onCheck(exerciseId, JSON.stringify({type: "code", value: code}),
                {execute: true, language, code});
            setPlots(response.plots ?? []);
            setPassed(response.is_correct === true);
            setCheckedAccess(response.expert_solution_available === true);
            setResult([response.stdout, response.stderr,
                response.feedback,
                t("codeExerciseExit", {code: response.exit_code}),
                response.check_mode === "practice" ? t("codeExercisePractice")
                    : response.check_mode === "self_review" ? t("codeExerciseSelfReview")
                    : response.is_correct === true ? t("codeExerciseCorrect")
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
    return <><section className={styles.testBlock}>
        <div className={styles.testHeader}>{language.toUpperCase()} · {exerciseId}</div>
        {block.data?.practice && <p>{t("codeExercisePractice")}</p>}
        {language === "python" && <p>{t("codeExercisePlotHint")}</p>}
        <label className={styles.codeExerciseLabel}>
            {t("codeExerciseSolution")}
            <textarea className={styles.codeExerciseInput} value={code} maxLength={8000}
                      onChange={(event) => setCode(event.target.value)} rows={8}
                      spellCheck={false} disabled={busy}/>
        </label>
        <div className={styles.testActions}>
            <button type="button" className={styles.testCheckButton} disabled={!onCheck || busy || !code.trim()}
                    onClick={run}>{t(language === "sql" ? "codeExerciseRunSql" : "codeExerciseRun")}</button>
        </div>
        {result && <pre className={styles.codeExerciseOutput} role="status">{result}</pre>}
        <MarkdownPlots plots={plots}/>
    </section>
        {!block.data?.practice && (checkedAccess ?? (completed || passed || expertSolutionAvailable)) && onExpertSolution && (
            <MarkdownExpertSolution exerciseId={exerciseId} onLoad={onExpertSolution}/>
        )}
    </>;
}

export default MarkdownCodeExercise;
