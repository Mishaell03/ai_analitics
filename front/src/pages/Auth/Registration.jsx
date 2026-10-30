import duck from "@/assets/auth/auth_duck.png";
import duckMobile from "@/assets/auth/up_duck.png";
import {useState} from "react";
import {useTranslation} from "@/hooks/useTranslation.js";
import {getLanguage} from "@/locales/i18n.js";
import styles from "./registration.module.css";
import {Eye, EyeOff} from "lucide-react";
import cloud from "@/assets/auth/cloud.png"
import cloud2 from "@/assets/auth/cloud2.png"
import {API_ROUTES} from "@/api/routes.js";
import {api} from "@/api/axios.js";
import { getDeviceId, getDeviceName } from "@/services/device.js";
import {Link, useNavigate} from "react-router-dom";import AuthCheck from "@/context/AuthService.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import {useAuth} from "@/context/AuthContext.jsx";
import {formatPhone, isValidPhone} from "@/services/mask.js";

const EMAIL_PATTERN = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

const NAME_PATTERN = /^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё -]*$/;

// коды согласий из users_consents на бэке
const CONSENTS = [
    {
        code: "PERSONAL_DATA",
        key: "personalData",
        text: "consentPersonalData",
        required: true,
    },
    {
        code: "MARKETING",
        key: "marketing",
        text: "consentMarketing",
        required: false,
    },
    {
        code: "ANALYTICS",
        key: "analytics",
        text: "consentAnalytics",
        required: false,
    },
];

export function Registration() {
    const navigate = useNavigate();

    const [showPassword, setShowPassword] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [password, setPassword] = useState("");
    const [consents, setConsents] = useState({
        personalData: false,
        marketing: false,
        analytics: false,
    });

    const [error, setError] = useState("");
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(false);

    const {setUser} = useAuth();
    const t = useTranslation("auth.register");
    const tError = useTranslation("error.error");

    /*
     * ---------- validation ----------
     *
     * Ошибки полей считаем всегда, но подсветку включаем только после
     * нажатия кнопки: иначе форма ругается на пустые поля, которые
     * пользователь ещё не успел заполнить.
     */

    function validate() {
        const errors = {};

        if (!name.trim() || !NAME_PATTERN.test(name.trim())) {
            errors.name = "fillName";
        }

        if (!email.trim() || !EMAIL_PATTERN.test(email.trim())) {
            errors.email = "fillEmail";
        }

        if (!phone.trim() || !isValidPhone(phone)) {
            errors.phone = "fillPhone";
        }

        if (!password || password.length < 8) {
            errors.password = "fillPassword";
        }

        if (CONSENTS.some((consent) => consent.required && !consents[consent.key])) {
            errors.consents = "acceptConsents";
        }

        return errors;
    }

    function handleTextChange(setter, key) {
        return (event) => {
            setter(event.target.value);

            if (fieldErrors[key]) {
                setFieldErrors((current) => {
                    const next = {...current};
                    delete next[key];
                    return next;
                });
            }
        };
    }

    function handlePhoneChange(e) {
        setPhone(formatPhone(e.target.value));

        if (fieldErrors.phone) {
            setFieldErrors((current) => {
                const next = {...current};
                delete next.phone;
                return next;
            });
        }
    }

    function handleConsentChange(key) {
        setConsents((current) => ({...current, [key]: !current[key]}));

        if (fieldErrors.consents && CONSENTS.some((consent) => consent.required && consent.key === key)) {
            setFieldErrors((current) => {
                const next = {...current};
                delete next.consents;
                return next;
            });
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        const errors = validate();

        setFieldErrors(errors);

        // подсветка полей уже объясняет, что не так, итоговую ошибку
        // оставляем только для ответов сервера
        if (Object.keys(errors).length > 0) {
            return;
        }

        setError("");

        try {
            setLoading(true);

            const response = await api.post(
                API_ROUTES.REGISTER,
                {
                    email: email.trim(),
                    password: password.trim(),

                    name: name.trim(),
                    phone: phone.trim(),

                    consents: CONSENTS.map(({code, key}) => ({
                        code,
                        is_accepted: consents[key],
                    })),

                    device_id: getDeviceId(),
                    device_name: getDeviceName(),
                    language: getLanguage(),
                }
            );
            // console.log(response);

            if (response.data.success === true) {
                const user = await AuthCheck.refresh();
                setUser(user)
                navigate(ROUTES.home);
            }

            // console.info("Register succçess")
        } catch (error) {
            // console.log(error);
            // console.log(error.response);


            const message =
                error.response?.data?.detail?.message ||
                error.response?.data?.detail?.error ||
                tError("serverError");

            setError(message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className={styles.registration}>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>

            <form className={styles.registrationCart} onSubmit={handleSubmit}>
                <div className={styles.registrationBox}>

                    <div className={styles.registrationHeader}>
                        <div className={styles.company}>
                            <img src="/icon.png" alt="logo"/>
                            <div className={styles.companyText}>
                                <p>Duck Docs <span>AI</span></p>
                                <span className={styles.companySubtitle}>DataLab</span>
                            </div>
                        </div>

                        <div>
                            <h1>{t("title")}</h1>
                        </div>
                    </div>

                    <div className={styles.registrationInput}>

                        <div className={styles.box}>
                            <p>
                                {t("name")}
                                <span className={styles.required}>*</span>
                            </p>

                            <input
                                type="text"
                                autoComplete="given-name"
                                placeholder={t("name")}
                                value={name}
                                onChange={handleTextChange(setName, "name")}
                                aria-invalid={Boolean(fieldErrors.name)}
                                className={fieldErrors.name ? styles.inputError : undefined}
                            />

                            {fieldErrors.name && (
                                <span className={styles.fieldError}>
                                    {t("fillName")}
                                </span>
                            )}
                        </div>

                        <div className={styles.box}>
                            <p>
                                {t("email")}
                                <span className={styles.required}>*</span>
                            </p>

                            <input
                                type="email"
                                autoComplete="email"
                                placeholder={t("email")}
                                value={email}
                                onChange={handleTextChange(setEmail, "email")}
                                aria-invalid={Boolean(fieldErrors.email)}
                                className={fieldErrors.email ? styles.inputError : undefined}
                            />

                            {fieldErrors.email && (
                                <span className={styles.fieldError}>
                                    {t("fillEmail")}
                                </span>
                            )}
                        </div>

                        <div className={styles.box}>
                            <p>
                                {t("phone")}
                                <span className={styles.required}>*</span>
                            </p>

                            <input
                                type="tel"
                                inputMode="numeric"
                                autoComplete="tel"
                                placeholder="+7 (999) 000-00-01"
                                value={phone}
                                onChange={handlePhoneChange}
                                onBlur={() => setPhone((current) => formatPhone(current))}
                                aria-invalid={Boolean(fieldErrors.phone)}
                                className={fieldErrors.phone ? styles.inputError : undefined}
                            />

                            {fieldErrors.phone && (
                                <span className={styles.fieldError}>
                                    {t("fillPhone")}
                                </span>
                            )}
                        </div>

                        <div className={styles.box}>
                            <p>
                                {t("password")}
                                <span className={styles.required}>*</span>
                            </p>

                            <div className={styles.passwordInput}>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    autoComplete="new-password"
                                    placeholder="Password123"
                                    value={password}
                                    onChange={handleTextChange(setPassword, "password")}
                                    aria-invalid={Boolean(fieldErrors.password)}
                                    className={fieldErrors.password ? styles.inputError : undefined}
                                />

                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowPassword((prev) => !prev)
                                    }
                                    className={styles.passwordToggle}
                                >
                                    {showPassword ? <Eye/> : <EyeOff/>}
                                </button>
                            </div>

                            {fieldErrors.password && (
                                <span className={styles.fieldError}>
                                    {t("fillPassword")}
                                </span>
                            )}
                        </div>

                        <div className={styles.consents}>
                            <p className={styles.consentsTitle}>{t("consentsTitle")}</p>

                            {fieldErrors.consents && (
                                <span className={styles.fieldError}>
                                    {t("acceptConsents")}
                                </span>
                            )}

                            {CONSENTS.map(({code, key, text, required}) => (
                                <label className={styles.consent} key={code}>
                                    <input
                                        type="checkbox"
                                        checked={consents[key]}
                                        onChange={() => handleConsentChange(key)}
                                    />

                                    <span>
                                        {t(text)}

                                        {required && (
                                            <span
                                                className={fieldErrors.consents
                                                    ? styles.required
                                                    : styles.consentRequired}
                                            >
                                                *
                                            </span>
                                        )}
                                    </span>
                                </label>
                            ))}
                        </div>

                        {error && (
                            <div className="error">
                                {error}
                            </div>
                        )}
                        <button
                            type="submit"
                            className={styles.registrationButton}
                            disabled={loading}
                        >
                            {loading ? t("title") + "..." : t("create")}
                        </button>
                        <div className={styles.authBox}>
                            <p>
                                {t('hasAccount')}    <Link to='/login'>{t('login')}</Link>
                            </p>
                        </div>
                    </div>
                </div>
            </form>

            <div className={styles.registrationImg}>
                <img src={cloud} className={styles.cloudDucks}></img>
                <img src={cloud} className={styles.cloudDucks}></img>
                <picture>
                    <source media="(max-width: 899px)" srcSet={duckMobile}/>
                    <img
                        src={duck}
                        alt="duck-duck"
                        className={styles.duckImg}
                    />
                </picture>
            </div>

        </div>
    );
}
