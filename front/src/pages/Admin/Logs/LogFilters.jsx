import {useState} from "react";
import {EMPTY_FILTERS} from "./useAdminLogs.js";
import styles from "./logs.module.css";

export default function LogFilters({isAI, onApply, t}) {
    const [draft, setDraft] = useState({...EMPTY_FILTERS});
    const [dateError, setDateError] = useState(false);
    const update = (key, value) => setDraft((current) => ({...current, [key]: value}));

    const input = (key, label, type = "text", props = {}) => (
        <label className={styles.field}>
            <span>{t(label)}</span>
            <input type={type} value={draft[key]} onChange={(event) => update(key, event.target.value)} {...props}/>
        </label>
    );
    const select = (key, label, options) => (
        <label className={styles.field}>
            <span>{t(label)}</span>
            <select value={draft[key]} onChange={(event) => update(key, event.target.value)}>
                <option value="">{t("logsAll")}</option>
                {options.map(([value, title]) => <option key={value} value={value}>{t(title)}</option>)}
            </select>
        </label>
    );

    return (
        <details className={styles.filterPanel}>
            <summary>{t("logsFilters")}</summary>
        <form className={styles.filters} onSubmit={(event) => {
            event.preventDefault();
            const invalid = Boolean(draft.date_from && draft.date_to && draft.date_from > draft.date_to);
            setDateError(invalid);
            if (invalid) return;
            const next = {...draft};
            if (isAI) {
                for (const key of ["session_id", "status_code", "code", "source"]) delete next[key];
            }
            onApply(next);
        }}>
            {input("user", "logsUser", "text", {maxLength: 255})}
            {input("user_id", "logsUserId", "number", {min: 1, step: 1})}
            {!isAI && input("session_id", "logsSession", "number", {min: 1, step: 1})}
            {select("status", "logsStatus", isAI ? [
                ["pending", "logsPending"], ["completed", "logsCompleted"],
                ["refused", "logsRefused"], ["failed", "logsFailed"],
            ] : [
                ["success", "logsSuccess"], ["redirect", "logsRedirect"],
                ["client_error", "logsClientError"], ["server_error", "logsServerError"],
            ])}
            {!isAI && input("status_code", "logsHttpCode", "number", {min: 100, max: 599, step: 1})}
            {!isAI && input("code", "logsCode", "text", {maxLength: 255, placeholder: "SUCCESS_GET_ADMIN_USERS"})}
            {!isAI && select("source", "logsSource", [["event", "logsEvent"], ["backend", "logsBackend"]])}
            {input("date_from", "logsDateFrom", "date")}
            {input("date_to", "logsDateTo", "date")}
            <div className={styles.actions}>
                <button type="submit">{t("logsApply")}</button>
                <button type="button" onClick={() => {
                    setDraft({...EMPTY_FILTERS});
                    setDateError(false);
                    onApply({...EMPTY_FILTERS});
                }}>{t("logsReset")}</button>
            </div>
            {dateError && <p role="alert" className={styles.error}>{t("logsDateInvalid")}</p>}
        </form>
        </details>
    );
}
