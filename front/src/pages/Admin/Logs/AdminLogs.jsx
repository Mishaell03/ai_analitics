import {useEffect, useRef, useState} from "react";
import {ShieldCheck, Terminal, LoaderCircle} from "lucide-react";
import EmptyState from "@/components/EmptyState/EmptyState.jsx";
import AdminPageHeader from "@/pages/Admin/components/AdminPageHeader.jsx";
import {useAdminTranslation} from "@/pages/Admin/hooks/useAdminTranslation.js";
import {useAdminAccess} from "@/pages/Admin/hooks/useAdminAccess.js";
import {formatNumber} from "@/services/format.js";
import {useAdminLogs} from "./useAdminLogs.js";
import LogFilters from "./LogFilters.jsx";
import styles from "./logs.module.css";

const AI_STATUSES = {
    pending: "logsPending", completed: "logsCompleted", refused: "logsRefused", failed: "logsFailed",
};

function LogEntry({item, isAI, t}) {
    const tone = isAI
        ? (item.status === "failed" ? "error" : item.status === "refused" ? "warning" : item.status === "pending" ? "info" : "success")
        : (item.status_code >= 500 ? "error" : item.status_code >= 400 ? "warning" : "success");

    return (
        <article className={styles.entry} data-tone={tone}>
            <div className={styles.entryLine}>
                <time className={styles.timestamp} dateTime={item.created_at}>
                    {new Date(item.created_at).toISOString().replace("T", " ").replace("Z", "")}
                </time>
                <span className={styles.level}>
                    {isAI ? t(AI_STATUSES[item.status]) : item.status_code ?? "—"}
                </span>
                <span className={styles.eventCode}>{isAI ? item.model : item.code || "—"}</span>
                {!isAI && <span className={styles.request}>{item.request_method} {item.request_path}</span>}
            </div>
            <div className={styles.metadata}>
                <span>{t(isAI ? "logsAI" : item.source === "event" ? "logsEvent" : "logsBackend")}</span>
                <span>{item.name || item.email || t("logsAnonymous")}{item.name && item.email ? ` <${item.email}>` : ""}</span>
                {item.user_id != null && <span>user_id={item.user_id}</span>}
                {isAI ? <>
                    <span>lesson_id={item.lesson_id}</span>
                    <span>conversation_id={item.conversation_id}</span>
                    <span>question_id={item.question_id}</span>
                </> : item.session_id != null && <span>session_id={item.session_id}</span>}
            </div>
            {isAI && <div className={styles.messages}>
                <div className={styles.message}><span className={styles.prompt}>{t("logsQuestionLabel")}</span><p>{item.question}</p></div>
                <div className={styles.message}><span className={styles.response}>{t("logsAnswer")}</span><p>{item.answer || t("logsNoAnswer")}</p></div>
                {item.error_code && <p className={styles.errorCode}>{item.error_code}</p>}
            </div>}
        </article>
    );
}

function LogsPanel({tab, t}) {
    const isAI = tab === "ai";
    const logs = useAdminLogs(tab);
    const {error, hasMore, loadMore} = logs;
    const {authLoading, isForbidden} = useAdminAccess(logs.error);
    const viewport = useRef(null);
    const sentinel = useRef(null);
    const pending = authLoading || logs.loading;

    useEffect(() => {
        if (pending || error || !hasMore || !viewport.current || !sentinel.current) return;
        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) loadMore();
        }, {root: viewport.current, rootMargin: "240px"});
        observer.observe(sentinel.current);
        return () => observer.disconnect();
    }, [pending, error, hasMore, loadMore]);

    const resetScroll = () => viewport.current?.scrollTo({top: 0});

    if (isForbidden) return <EmptyState icon={ShieldCheck} title={t("forbiddenTitle")} description={t("forbiddenDescription")}/>;

    return (
        <>
            <AdminPageHeader title={t("logsTitle")} subtitle={t("logsConsoleSubtitle")} onRefresh={() => {
                resetScroll();
                logs.reload();
            }} refreshing={pending} refreshLabel={t("refreshButton")} refreshingLabel={t("refreshProcess")}/>
            <LogFilters isAI={isAI} onApply={(filters) => {
                resetScroll();
                logs.applyFilters(filters);
            }} t={t}/>
            <section className={styles.console} aria-label={t(isAI ? "logsAI" : "logsSystem")}>
                <header className={styles.consoleHeader}>
                    <div className={styles.consoleTitle}><Terminal size={16} aria-hidden="true"/>
                        <span>{t(isAI ? "logsAI" : "logsSystem")}</span><span className={styles.utc}>UTC</span>
                    </div>
                    <span className={styles.counter}>{t("logsLoaded", {
                        loaded: formatNumber(logs.items.length), total: formatNumber(logs.total),
                    })}</span>
                </header>
                <div className={styles.viewport} ref={viewport} tabIndex={0}
                     role="region" aria-label={t("logsConsoleScroll")} aria-busy={pending}>
                    {logs.items.map((item) => <LogEntry key={isAI ? item.question_id : `${item.source}-${item.id}`}
                                                      item={item} isAI={isAI} t={t}/>)}
                    <div ref={sentinel} className={styles.consoleFooter}>
                        {logs.error ? <div role="alert" className={styles.consoleError}>
                            <span>{t("logsError")}</span>
                            <button type="button" onClick={logs.retry}>{t("usersPageErrorRetry")}</button>
                        </div> : pending ? <span role="status" className={styles.loading}>
                            <LoaderCircle size={15} aria-hidden="true"/>{t("logsLoading")}
                        </span> : logs.items.length === 0 ? <span>{t("logsEmpty")} · {t("logsEmptyDescription")}</span>
                            : <span>{t(logs.hasMore ? "logsScrollMore" : "logsEnd")}</span>}
                    </div>
                </div>
            </section>
        </>
    );
}

export default function AdminLogs() {
    const t = useAdminTranslation();
    const [tab, setTab] = useState("system");
    return (
        <div className={styles.logs}>
            <nav className={styles.tabs} aria-label={t("logsTitle")}>
                {["system", "ai"].map((value) => (
                    <button key={value} type="button" aria-pressed={tab === value} onClick={() => setTab(value)}>
                        {t(value === "ai" ? "logsAI" : "logsSystem")}
                    </button>
                ))}
            </nav>
            <LogsPanel key={tab} tab={tab} t={t}/>
        </div>
    );
}
