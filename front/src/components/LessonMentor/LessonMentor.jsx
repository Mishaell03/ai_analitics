import {useEffect, useId, useRef, useState, useSyncExternalStore} from "react";
import {AlertCircle, ArrowUp, ChevronDown, CornerDownLeft, RotateCw, ShieldCheck, Sparkles, X} from "lucide-react";
import {api} from "@/api/axios.js";
import {useTranslation} from "@/hooks/useTranslation.js";
import {mergeMentorMessages} from "@/services/lessonMentor.js";
import MentorTurn from "./MentorTurn.jsx";
import MentorWelcome from "./MentorWelcome.jsx";
import styles from "./lessonMentor.module.css";

const mobileQuery = "(max-width: 1050px)";
const isMobile = () => window.matchMedia(mobileQuery).matches;
const subscribeMobile = callback => {
    const query = window.matchMedia(mobileQuery);
    query.addEventListener("change", callback);
    return () => query.removeEventListener("change", callback);
};

export default function LessonMentor({slug, moduleId, lessonId}) {
    const t = useTranslation("courses.course");
    const path = `/courses/${encodeURIComponent(slug)}/modules/${moduleId}/lessons/${lessonId}/ai/messages`;
    const [messages, setMessages] = useState([]);
    const [question, setQuestion] = useState("");
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [next, setNext] = useState(null);
    const [retry, setRetry] = useState(null);
    const mounted = useRef(true);
    const dialog = useRef(null);
    const scroller = useRef(null);
    const stickToBottom = useRef(true);
    const input = useRef(null);
    const id = useId();
    const narrow = useSyncExternalStore(subscribeMobile, isMobile, () => false);

    function merge(message) {
        setMessages(current => mergeMentorMessages(current, [message]));
    }

    async function load(after = 0) {
        setLoading(true);
        setError("");
        try {
            const {data} = await api.get(path, {params: {after_id: after, limit: 10}});
            if (!mounted.current) return;
            setMessages(current => mergeMentorMessages(current, data.messages));
            setNext(data.next_after_id);
        } catch {
            if (mounted.current) setError(t("mentorHistoryError"));
        } finally {
            if (mounted.current) setLoading(false);
        }
    }

    useEffect(() => {
        mounted.current = true;
        const controller = new AbortController();
        api.get(path, {params: {limit: 10}, signal: controller.signal}).then(({data}) => {
            setMessages(data.messages);
            setNext(data.next_after_id);
            setLoading(false);
        }).catch(() => {
            if (!controller.signal.aborted) {
                setError(t("mentorHistoryError"));
                setLoading(false);
            }
        });
        return () => { mounted.current = false; controller.abort(); };
    }, [path, t]);

    useEffect(() => {
        if (stickToBottom.current && scroller.current) {
            scroller.current.scrollTop = messages.length || sending ? scroller.current.scrollHeight : 0;
        }
    }, [messages, sending, narrow]);

    async function submit(data) {
        if (sending) return;
        stickToBottom.current = true;
        setRetry(data);
        setSending(true);
        setError("");
        try {
            const response = await api.post(path, data, {timeout: 60000});
            if (!mounted.current) return;
            merge(response.data);
            if (response.data.status === "pending") {
                setError(t("mentorPending"));
            } else {
                setRetry(null);
                setQuestion("");
            }
        } catch (failure) {
            if (!mounted.current) return;
            const status = failure.response?.status;
            setError(t(status === 429 ? "mentorQuota" : status === 409 ? "mentorBusy"
                : status === 503 ? "mentorConfigError" : "mentorRequestError"));
        } finally {
            if (mounted.current) setSending(false);
        }
    }

    const pending = messages.find(item => item.status === "pending");
    const outstanding = retry ?? (pending ? {
        request_id: pending.request_id, question: pending.question, user_context: pending.user_context,
    } : null);
    const showDraft = sending && retry && !messages.some(item => item.request_id === retry.request_id);
    const visibleMessages = showDraft ? [...messages, {...retry, status: "pending"}].slice(-10) : messages;

    function choosePrompt(text) {
        setQuestion(text);
        input.current?.focus();
    }

    function openChat() {
        dialog.current?.showModal();
        if (scroller.current) scroller.current.scrollTop = messages.length || sending ? scroller.current.scrollHeight : 0;
    }

    const chat = <>
        <header className={styles.header}>
            <div className={styles.headerMain}>
                <span className={styles.avatar}><Sparkles aria-hidden="true"/></span>
                <div className={styles.heading}>
                    <span className={styles.eyebrow}>{t("mentorEyebrow")}</span>
                    <h2 id={`${id}-title`}>{t("mentorTitle")}</h2>
                </div>
                {narrow && <button type="button" className={styles.closeButton} onClick={() => dialog.current?.close()}
                    aria-label={t("mentorClose")} title={t("mentorClose")}><X aria-hidden="true"/></button>}
            </div>
            <div className={styles.sessionBar}>
                <span><i aria-hidden="true"/>{t("mentorCurrentLesson")}</span>
                <span className={styles.historyBadge} title={t("mentorSession")}>{visibleMessages.length}<span>/ 10</span></span>
            </div>
        </header>
        <div className={styles.messages} ref={scroller} role="log" aria-label={t("mentorConversation")}
            aria-live="polite" aria-relevant="additions text" tabIndex={0} onScroll={event => {
                const node = event.currentTarget;
                stickToBottom.current = node.scrollHeight - node.scrollTop - node.clientHeight < 64;
            }}>
            {loading && !messages.length ? <div className={styles.historyLoading} role="status">
                <span className={styles.skeletonAvatar}/><div className={styles.skeletonLines}><span/><span/><span/></div>
                <span className={styles.srOnly}>{t("mentorLoading")}</span>
            </div> : <>
                {!messages.length && !showDraft && <MentorWelcome onPrompt={choosePrompt} disabled={sending || Boolean(outstanding)}/>}
                {visibleMessages.map(item => <MentorTurn key={item.request_id} item={item}/>)}
            </>}
        </div>
        <div className={styles.footer}>
            {next && <button type="button" className={styles.textButton} disabled={loading} onClick={() => load(next)}>{t("mentorMore")}</button>}
            {error && <div className={styles.error} role="alert"><AlertCircle aria-hidden="true"/><div>
                <p>{error}</p>
                {!outstanding && <button type="button" className={styles.textButton} disabled={loading} onClick={() => load()}>
                    <RotateCw aria-hidden="true"/>{t("mentorRefresh")}
                </button>}
            </div></div>}
            <form className={styles.composer} onSubmit={event => {
                event.preventDefault();
                if (!sending && !loading && question.trim() && !outstanding) {
                    submit({request_id: crypto.randomUUID(), question: question.trim(), user_context: ""});
                }
            }}>
                <div className={styles.composerHeading}>
                    <label htmlFor={`${id}-question`}>{t("mentorQuestion")}</label>
                    <span className={styles.counter} data-limit={question.length >= 1900}>{question.length}<span>/2000</span></span>
                </div>
                <textarea ref={input} id={`${id}-question`} maxLength={2000} value={question}
                    placeholder={t("mentorPlaceholder")} aria-describedby={`${id}-hint`}
                    disabled={sending || Boolean(outstanding)} onChange={event => setQuestion(event.target.value)} rows={3}
                    onKeyDown={event => {
                        if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && !event.nativeEvent.isComposing) {
                            event.preventDefault();
                            event.currentTarget.form?.requestSubmit();
                        }
                    }}/>
                <div className={styles.composerActions}>
                    <span className={styles.keyboardHint} id={`${id}-hint`}><CornerDownLeft aria-hidden="true"/>{t("mentorKeyboardHint")}</span>
                    {outstanding
                        ? <button className={styles.sendButton} type="button" disabled={sending} onClick={() => submit(outstanding)}>
                            <RotateCw className={sending ? styles.spin : undefined} aria-hidden="true"/>
                            <span>{t(sending ? "mentorSending" : "mentorCheck")}</span>
                        </button>
                        : <button className={styles.sendButton} type="submit" disabled={sending || loading || !question.trim()}
                            aria-label={t("mentorAsk")}><span>{t("mentorSend")}</span><ArrowUp aria-hidden="true"/></button>}
                </div>
            </form>
            <details className={styles.privacy}>
                <summary><ShieldCheck aria-hidden="true"/><span>{t("mentorPrivacy")}</span><ChevronDown aria-hidden="true"/></summary>
                <p>{t("mentorNotice")}</p>
            </details>
        </div>
    </>;

    return narrow ? <>
        <button type="button" className={styles.openChat} onClick={openChat} aria-haspopup="dialog" aria-controls={`${id}-dialog`}>
            <span className={styles.triggerIcon}><Sparkles aria-hidden="true"/></span>
            <span>{t("mentorTitle")}<small>{t("mentorTriggerHint")}</small></span>
        </button>
        <dialog ref={dialog} id={`${id}-dialog`} className={`${styles.mentor} ${styles.drawer}`} aria-labelledby={`${id}-title`}>
            {chat}
        </dialog>
    </> : <aside className={styles.mentor} aria-labelledby={`${id}-title`}>{chat}</aside>;
}
