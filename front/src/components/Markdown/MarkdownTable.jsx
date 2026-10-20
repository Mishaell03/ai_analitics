import MarkdownInline from "@/components/Markdown/MarkdownInline.jsx";
import styles from "./markdown.module.css";

/**
 * ТАБЛИЦА
 *
 * Выравнивание колонок берётся из строки-разделителя Markdown.
 */
function MarkdownTable({header = [], rows = []}) {
    return (
        <div className={styles.tableWrap}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        {header.map((cell, index) => (
                            <th key={index} data-align={cell.align}>
                                <MarkdownInline nodes={cell.children}/>
                            </th>
                        ))}
                    </tr>
                </thead>

                <tbody>
                    {rows.map((row, rowIndex) => (
                        <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                                <td key={cellIndex} data-align={cell.align}>
                                    <MarkdownInline nodes={cell.children}/>
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default MarkdownTable;
