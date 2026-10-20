import styles from "./markdown.module.css";

/**
 * БЛОК КОДА
 *
 * Токены подсветки приходят из сервиса: компонент только раздаёт
 * им классы, текст кода остаётся текстом.
 */
function MarkdownCode({language, code, tokens = []}) {
    return (
        <div className={styles.codeBlock}>
            {language && (
                <span className={styles.codeLanguage}>
                    {language}
                </span>
            )}

            <pre className={styles.code}>
                <code>
                    {tokens.map((token, index) => (
                        <span
                            className={styles[`token${capitalize(token.type)}`]}
                            key={index}
                        >
                            {token.value}
                        </span>
                    ))}

                    {!tokens.length && code}
                </code>
            </pre>
        </div>
    );
}

function capitalize(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
}

export default MarkdownCode;
