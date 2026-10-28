import styles from "./lessonMentor.module.css";

// Deliberately limited formatting: no HTML, links, media, custom blocks or actions.
function inline(text) {
    return text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g).map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
        if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
        return part;
    });
}

export default function MentorText({text}) {
    return <div className={styles.answerText}>
        {text.split(/(```[\s\S]*?```)/g).filter(Boolean).map((part, index) => {
            const code = /^```([^\n`]*)\n([\s\S]*?)```$/.exec(part);
            if (code) return <div className={styles.codeBlock} key={index}>
                {code[1].trim() && <span className={styles.codeLanguage}>{code[1].trim()}</span>}
                <pre><code>{code[2].replace(/\n$/, "")}</code></pre>
            </div>;
            return <p key={index}>{inline(part)}</p>;
        })}
    </div>;
}
