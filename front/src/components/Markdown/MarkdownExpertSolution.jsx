import {useEffect, useId, useMemo, useState} from "react";
import {useTranslation} from "@/hooks/useTranslation.js";
import {markdownService} from "@/services/markdown/MarkdownService.js";
import MarkdownCode from "./MarkdownCode.jsx";
import styles from "./markdown.module.css";

export function ExpertSolutionView({solution}) {
    const t = useTranslation("courses.course");
    const titleId = useId();
    const tokens = useMemo(() => markdownService.highlight(solution.code, solution.language), [solution]);
    return (
        <section className={styles.expertSolution} aria-labelledby={titleId}>
            <h3 className={styles.expertSolutionTitle} id={titleId}>{t("expertSolutionTitle")}</h3>
            <MarkdownCode language={solution.language} code={solution.code} tokens={tokens}/>
        </section>
    );
}

export default function MarkdownExpertSolution({exerciseId, onLoad}) {
    const t = useTranslation("courses.course");
    const [state, setState] = useState({loading: true, solution: null});
    const [retry, setRetry] = useState(0);

    useEffect(() => {
        let active = true;
        const load = async () => {
            try {
                const solution = await onLoad(exerciseId);
                if (active) setState({loading: false, solution});
            } catch {
                if (active) setState({loading: false, solution: null});
            }
        };
        load();
        return () => { active = false; };
    }, [exerciseId, onLoad, retry]);

    if (state.solution) return <ExpertSolutionView solution={state.solution}/>;
    return (
        <section className={styles.expertSolution} aria-busy={state.loading}>
            <h3 className={styles.expertSolutionTitle}>{t("expertSolutionTitle")}</h3>
            {state.loading ? <p role="status">{t("expertSolutionLoading")}</p> : <>
                <p role="alert">{t("expertSolutionError")}</p>
                <button type="button" className={styles.testCheckButton} onClick={() => {
                    setState({loading: true, solution: null});
                    setRetry((value) => value + 1);
                }}>{t("errorRetry")}</button>
            </>}
        </section>
    );
}
