import duck from "@/assets/auth/login_duck.png";
import duckMobile from "@/assets/auth/up_duck.png";
import {useState} from "react";
import {getTranslation} from "@/locales/i18n.js";
import styles from "./login.module.css";
import {Eye, EyeOff} from "lucide-react";
import cloud from "@/assets/auth/cloud.png"
import cloud2 from "@/assets/auth/cloud2.png"
import {API_ROUTES} from "@/api/routes.js";
import {api} from "@/api/axios.js";
import { getDeviceId, getDeviceName } from "@/services/device.js";

export function Login() {
    const [showPassword, setShowPassword] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const language = "ru";
    const t = (key) => getTranslation(`auth.login.${key}`, language);
    const tError = (key) => getTranslation(`error.error.${key}`, language);

    async function handleSubmit(e) {
        e.preventDefault();

        setError("");

        if (!email || !password) {
            setError(t("fillAllFields"));
            return;
        }
        if (!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) {
            setError(t("fillEmail"));
            return;
        }

        if (password.length < 8) {
            setError(t("fillPassword"));
            return;
        }

        try {
            setLoading(true);

            const response = await api.post(
                API_ROUTES.LOGIN,
                {
                    email: email.trim(),
                    password: password.trim(),

                    device_id: getDeviceId(),
                    device_name: getDeviceName(),
                    language: language,
                }
            );
            // console.log(response);

            localStorage.setItem("session_token", response.data.token);
            // console.info("Login success")
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
        <div className={styles.login}>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>
            <img src={cloud2} className={styles.cloud}></img>
            <form className={styles.loginCart} onSubmit={handleSubmit}>
                <div className={styles.loginBox}>

                    <div className={styles.loginHeader}>
                        <div className={styles.company}>
                            <img src="/icon.png" alt="logo"/>
                            <p>
                                Duck doc <span>AI</span>
                            </p>
                        </div>

                        <div>
                            <h1>{t("title")}</h1>
                        </div>
                    </div>

                    <div className={styles.loginInput}>

                        <div className={styles.box}>
                            <p>{t("email")}</p>

                            <input
                                type="email"
                                placeholder={t("email")}
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>

                        <div className={styles.box}>
                            <div className={styles.passwordHeader}>
                                <p>{t("password")}</p>

                                <a href="#">
                                    {t("forgotPassword")}
                                </a>
                            </div>

                            <div className={styles.passwordInput}>
                                <input
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Password123"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
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
                        </div>
                        {error && (
                            <div className="error">
                                {error}
                            </div>
                        )}
                        <button
                            type="submit"
                            className={styles.loginButton}
                            disabled={loading}
                        >
                            {loading ? t("title") + "..." : t("login")}
                        </button>

                    </div>
                </div>
            </form>

            <div className={styles.loginImg}>
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
