/**
 * ПОДСВЕТКА СИНТАКСИСА В БЛОКАХ КОДА
 *
 * Своя реализация без внешних зависимостей: уроки читаются из
 * хранилища, а тянуть в фронт большой редактор ради подсветки
 * не нужно.
 *
 * Результат — список токенов {type, value}. Разметку собирает
 * React-компонент, поэтому подсветка остаётся обычным текстом.
 */

const JS_KEYWORDS = [
    "as", "async", "await", "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "export", "extends", "finally",
    "for", "from", "function", "get", "if", "import", "in", "instanceof", "let",
    "new", "of", "return", "set", "static", "super", "switch", "this", "throw",
    "try", "typeof", "var", "void", "while", "with", "yield",
];

const TS_KEYWORDS = [
    ...JS_KEYWORDS,
    "abstract", "any", "boolean", "declare", "enum", "implements", "interface",
    "never", "number", "private", "protected", "public", "readonly", "string",
    "type", "unknown", "namespace", "keyof",
];

const PYTHON_KEYWORDS = [
    "and", "as", "assert", "async", "await", "break", "class", "continue", "def",
    "del", "elif", "else", "except", "finally", "for", "from", "global", "if",
    "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
    "return", "try", "while", "with", "yield",
];

const BASH_KEYWORDS = [
    "case", "do", "done", "elif", "else", "esac", "export", "fi", "for", "function",
    "if", "in", "local", "return", "then", "until", "while",
];

const SQL_KEYWORDS = [
    "ALTER", "AND", "AS", "ASC", "BY", "CREATE", "DELETE", "DESC", "DISTINCT",
    "DROP", "FROM", "GROUP", "HAVING", "IN", "INNER", "INSERT", "INTO", "IS",
    "JOIN", "LEFT", "LIKE", "LIMIT", "NOT", "NULL", "OFFSET", "ON", "OR", "ORDER",
    "OUTER", "PRIMARY", "REFERENCES", "SELECT", "SET", "TABLE", "UNION", "UPDATE",
    "VALUES", "WHERE",
];

const JAVA_KEYWORDS = [
    "abstract", "boolean", "break", "byte", "case", "catch", "char", "class",
    "const", "continue", "default", "do", "double", "else", "enum", "extends",
    "final", "finally", "float", "for", "if", "implements", "import", "instanceof",
    "int", "interface", "long", "new", "package", "private", "protected", "public",
    "return", "short", "static", "super", "switch", "this", "throw", "throws",
    "try", "void", "while",
];

const GO_KEYWORDS = [
    "break", "case", "chan", "const", "continue", "default", "defer", "else",
    "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
    "map", "package", "range", "return", "select", "struct", "switch", "type", "var",
];

const C_KEYWORDS = [
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed", "sizeof",
    "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile",
    "while",
];

const CPP_KEYWORDS = [
    ...C_KEYWORDS,
    "bool", "catch", "class", "const_cast", "delete", "dynamic_cast", "explicit",
    "false", "friend", "namespace", "new", "nullptr", "operator", "private",
    "protected", "public", "reinterpret_cast", "static_cast", "template", "this",
    "throw", "true", "try", "typeid", "typename", "using", "virtual",
];

const RUST_KEYWORDS = [
    "as", "async", "await", "break", "const", "continue", "crate", "dyn", "else",
    "enum", "extern", "fn", "for", "if", "impl", "in", "let", "loop", "match",
    "mod", "move", "mut", "pub", "ref", "return", "self", "static", "struct",
    "super", "trait", "type", "unsafe", "use", "where", "while",
];

const PHP_KEYWORDS = [
    "abstract", "and", "array", "as", "break", "callable", "case", "catch", "class",
    "clone", "const", "continue", "declare", "default", "do", "echo", "else",
    "elseif", "empty", "extends", "final", "finally", "fn", "for", "foreach",
    "function", "global", "if", "implements", "include", "instanceof", "interface",
    "namespace", "new", "or", "private", "protected", "public", "require",
    "return", "static", "switch", "throw", "trait", "try", "use", "var", "while",
    "yield",
];

const YAML_KEYWORDS = ["true", "false", "null", "yes", "no", "on", "off"];

/**
 * ОПИСАНИЯ ЯЗЫКОВ
 *
 * keywords — слова, которые подсвечиваются как ключевые;
 * lineComments — маркеры комментария до конца строки;
 * blockComments — пары маркеров многострочного комментария;
 * strings — кавычки, которыми начинается строка.
 */
const LANGUAGE_DEFINITIONS = {
    javascript: {
        keywords: JS_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'", "`"],
    },
    typescript: {
        keywords: TS_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'", "`"],
    },
    python: {
        keywords: PYTHON_KEYWORDS,
        lineComments: ["#"],
        blockComments: [],
        strings: ["\"", "'"],
    },
    json: {
        keywords: [],
        lineComments: [],
        blockComments: [],
        strings: ["\""],
    },
    bash: {
        keywords: BASH_KEYWORDS,
        lineComments: ["#"],
        blockComments: [],
        strings: ["\"", "'"],
    },
    sql: {
        keywords: SQL_KEYWORDS,
        lineComments: ["--"],
        blockComments: [["/*", "*/"]],
        strings: ["'"],
    },
    java: {
        keywords: JAVA_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'"],
    },
    go: {
        keywords: GO_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'", "`"],
    },
    c: {
        keywords: C_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'"],
    },
    cpp: {
        keywords: CPP_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'"],
    },
    rust: {
        keywords: RUST_KEYWORDS,
        lineComments: ["//"],
        blockComments: [["/*", "*/"]],
        strings: ["\""],
    },
    php: {
        keywords: PHP_KEYWORDS,
        lineComments: ["//", "#"],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'"],
    },
    yaml: {
        keywords: YAML_KEYWORDS,
        lineComments: ["#"],
        blockComments: [],
        strings: ["\"", "'"],
    },
    html: {
        keywords: [],
        lineComments: [],
        blockComments: [["<!--", "-->"]],
        strings: ["\"", "'"],
    },
    css: {
        keywords: [],
        lineComments: [],
        blockComments: [["/*", "*/"]],
        strings: ["\"", "'"],
    },
};

// псевдонимы языков: имя в разметке может быть любым
const LANGUAGE_ALIASES = {
    js: "javascript",
    jsx: "javascript",
    mjs: "javascript",
    ts: "typescript",
    tsx: "typescript",
    py: "python",
    python3: "python",
    sh: "bash",
    shell: "bash",
    zsh: "bash",
    console: "bash",
    yml: "yaml",
    htm: "html",
    xml: "html",
    svg: "html",
    markdown: "html",
    md: "html",
    "c++": "cpp",
    cs: "java",
    kotlin: "java",
    kt: "java",
    swift: "java",
    rb: "php",
    ruby: "php",
    golang: "go",
};

// для неизвестного языка работает набор общих правил
const DEFAULT_DEFINITION = {
    keywords: [],
    lineComments: ["#", "//"],
    blockComments: [["/*", "*/"]],
    strings: ["\"", "'"],
};

const TOKEN_BOOLEAN = "boolean";
const TOKEN_COMMENT = "comment";
const TOKEN_FUNCTION = "function";
const TOKEN_KEYWORD = "keyword";
const TOKEN_NUMBER = "number";
const TOKEN_PLAIN = "plain";
const TOKEN_STRING = "string";

const IDENTIFIER_PATTERN = /[A-Za-z_$][\w$]*/y;
const NUMBER_PATTERN = /\d+(?:[._]\d+)*(?:[eE][+-]?\d+)?/y;

export class CodeHighlighter {
    /**
     * @param {object} definitions описания языков
     */
    constructor(definitions = LANGUAGE_DEFINITIONS) {
        this._definitions = definitions;
    }

    /**
     * Описание языка по имени из разметки.
     *
     * @param {string} language имя языка
     * @returns {object}
     */
    getDefinition(language) {
        const name = (language || "").toLowerCase().trim();

        if (!name) {
            return DEFAULT_DEFINITION;
        }

        const key = LANGUAGE_ALIASES[name] ?? name;

        return this._definitions[key] ?? DEFAULT_DEFINITION;
    }

    /**
     * Подсвечивает код.
     *
     * @param {string} code исходный код
     * @param {string} language имя языка
     * @returns {{type: string, value: string}[]}
     */
    highlight(code, language) {
        if (!code) {
            return [];
        }

        const definition = this.getDefinition(language);
        const keywords = new Set(definition.keywords);
        const booleans = new Set(["true", "false", "null", "None", "nil", "undefined"]);

        const tokens = [];
        let plain = "";
        let index = 0;

        const flush = () => {
            if (plain) {
                tokens.push({type: TOKEN_PLAIN, value: plain});
                plain = "";
            }
        };

        while (index < code.length) {
            const matched = this._matchComment(code, index, definition)
                ?? this._matchString(code, index, definition)
                ?? this._matchNumber(code, index)
                ?? this._matchIdentifier(code, index, keywords, booleans);

            if (!matched) {
                plain += code[index];
                index += 1;
                continue;
            }

            flush();
            tokens.push(matched.token);
            index += matched.length;
        }

        flush();

        return tokens;
    }

    _matchComment(code, index, definition) {
        for (const [open, close] of definition.blockComments) {
            if (!code.startsWith(open, index)) {
                continue;
            }

            const end = code.indexOf(close, index + open.length);
            const value = end === -1
                ? code.slice(index)
                : code.slice(index, end + close.length);

            return {token: {type: TOKEN_COMMENT, value}, length: value.length};
        }

        for (const marker of definition.lineComments) {
            if (!code.startsWith(marker, index)) {
                continue;
            }

            const end = code.indexOf("\n", index);
            const value = end === -1 ? code.slice(index) : code.slice(index, end);

            return {token: {type: TOKEN_COMMENT, value}, length: value.length};
        }

        return null;
    }

    _matchString(code, index, definition) {
        for (const quote of definition.strings) {
            if (!code.startsWith(quote, index)) {
                continue;
            }

            let cursor = index + quote.length;

            while (cursor < code.length) {
                if (code[cursor] === "\\") {
                    cursor += 2;
                    continue;
                }

                if (code.startsWith(quote, cursor)) {
                    cursor += quote.length;
                    break;
                }

                cursor += 1;
            }

            const value = code.slice(index, Math.min(cursor, code.length));

            return {token: {type: TOKEN_STRING, value}, length: value.length};
        }

        return null;
    }

    _matchNumber(code, index) {
        NUMBER_PATTERN.lastIndex = index;

        const match = NUMBER_PATTERN.exec(code);

        if (!match) {
            return null;
        }

        return {token: {type: TOKEN_NUMBER, value: match[0]}, length: match[0].length};
    }

    _matchIdentifier(code, index, keywords, booleans) {
        IDENTIFIER_PATTERN.lastIndex = index;

        const match = IDENTIFIER_PATTERN.exec(code);

        if (!match) {
            return null;
        }

        const value = match[0];

        let type = TOKEN_PLAIN;

        if (keywords.has(value)) {
            type = TOKEN_KEYWORD;
        } else if (booleans.has(value)) {
            type = TOKEN_BOOLEAN;
        } else if (this._isCall(code, index + value.length)) {
            type = TOKEN_FUNCTION;
        }

        return {token: {type, value}, length: value.length};
    }

    _isCall(code, index) {
        let cursor = index;

        while (cursor < code.length && /\s/.test(code[cursor])) {
            cursor += 1;
        }

        return code[cursor] === "(";
    }
}

export const codeHighlighter = new CodeHighlighter();
