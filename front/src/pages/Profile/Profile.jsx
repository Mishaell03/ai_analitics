import {useCallback, useEffect, useMemo, useRef, useState} from "react";
import {getTranslation} from "@/locales/i18n.js";
import styles from "./profile.module.css";
import {BookOpen, ImageOff, LogOut, Pencil, RefreshCw, ShieldCheck, Sparkles, User, X} from "lucide-react";
import {Link, useNavigate} from "react-router-dom";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import {useAuth} from "@/context/AuthContext.jsx";
import ImageCache from "@/context/ImageCache.js";
import {formatPhone, validateProfile} from "@/services/mask.js";

const language = "ru";
const PAGE_SIZE = 100;

export function Profile() {
    const navigate = useNavigate();
    const {user, loading: authLoading, refresh, logout} = useAuth();

    const t = (key) => getTranslation(`profile.profile.${key}`, language);

    const [avatar, setAvatar] = useState(null);
    const [courses, setCourses] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [refreshing, setRefreshing] = useState(false);
    const [coursesLoading, setCoursesLoading] = useState(true);
    const [error, setError] = useState(false);

    const [loggingOut, setLoggingOut] = useState(false);
    const [showLogoutModal, setShowLogoutModal] = useState(false);

    /*
     * ---------- edit form ----------
     */

    const [editing, setEditing] = useState(false);
    const [saving, setSaving] = useState(false);

    const [name, setName] = useState(user?.name ?? "");
    const [phone, setPhone] = useState(formatPhone(user?.phone ?? ""));
    const [email, setEmail] = useState(user?.email ?? "");

    const [fieldErrors, setFieldErrors] = useState({});
    const [saveError, setSaveError] = useState("");

    const refreshRef = useRef(refresh);

    useEffect(() => {
        refreshRef.current = refresh;
    }, [refresh]);

    const handleRefresh = useCallback(async () => {
        setError(false);
        setRefreshing(true);

        try {
            await refreshRef.current();
        } catch {
            setError(true);
        } finally {
            setRefreshing(false);
        }
    }, []);

    const fetchCourses = useCallback(async () => {
        setError(false);
        setCoursesLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.COURSES, {
                params: {
                    page,
                    page_size: PAGE_SIZE,
                },
            });

            setCourses(data.courses ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch {
            setError(true);
        } finally {
            setCoursesLoading(false);
        }
    }, [page]);

    useEffect(() => {
        const {has_image: hasImage, avatar_key: avatarKey} = user ?? {};

        if (!hasImage || !avatarKey) {
            setAvatar(null);
            return;
        }

        let url;

        async function loadAvatar() {
            const blobUrl = await ImageCache.get(avatarKey);

            if (blobUrl) {
                url = blobUrl;
                setAvatar(url);
            }
        }

        loadAvatar();

        return () => {
            if (url) {
                URL.revokeObjectURL(url);
            }
        };
    }, [user?.has_image, user?.avatar_key]);

    useEffect(() => {
        fetchCourses();
    }, [fetchCourses]);

    const enrolledCourses = useMemo(
        () => courses.filter((course) => course.is_enrolled),
        [courses]
    );

    const tError = (key) => getTranslation(`error.error.${key}`, language);

    const handleNameChange = (event) => {
        setName(event.target.value);

        if (fieldErrors.name) {
            setFieldErrors((current) => ({...current, name: undefined}));
        }
    };

    const handlePhoneChange = (event) => {
        setPhone(formatPhone(event.target.value));

        if (fieldErrors.phone) {
            setFieldErrors((current) => ({...current, phone: undefined}));
        }
    };

    const handleEmailChange = (event) => {
        setEmail(event.target.value);

        if (fieldErrors.email) {
            setFieldErrors((current) => ({...current, email: undefined}));
        }

        setSaveError("");
    };

    const handleOpenEdit = () => {
        if (saving) return;

        setName(user?.name ?? "");
        setPhone(formatPhone(user?.phone ?? ""));
        setEmail(user?.email ?? "");

        setFieldErrors({});
        setSaveError("");

        setEditing(true);
    };

    const handleCancelEdit = () => {
        if (saving) return;

        setName(user?.name ?? "");
        setPhone(formatPhone(user?.phone ?? ""));
        setEmail(user?.email ?? "");

        setFieldErrors({});
        setSaveError("");

        setEditing(false);
    };

    const handleSave = async (event) => {
        event.preventDefault();

        if (saving) return;

        setSaveError("");

        const errors = validateProfile({name, phone, email});

        if (Object.keys(errors).length > 0) {
            setFieldErrors(errors);
            return;
        }

        setFieldErrors({});
        setSaving(true);

        try {
            await api.patch(API_ROUTES.USER_UPDATE, {
                name: name.trim() || null,
                phone: phone.trim() || null,
                email: email.trim(),
            });

            await refreshRef.current();

            setEditing(false);
        } catch (requestError) {
            const message =
                requestError.response?.data?.detail?.message ||
                requestError.response?.data?.detail?.error ||
                tError("serverError");

            setSaveError(message);
        } finally {
            setSaving(false);
        }
    };

    const handleOpenLogoutModal = () => {
        if (loggingOut) return;

        setShowLogoutModal(true);
    };

    const handleLogout = async () => {
        if (loggingOut) return;

        setLoggingOut(true);

        try {
            await logout();
            navigate(ROUTES.login);
        } catch {
            setShowLogoutModal(false);
        } finally {
            setLoggingOut(false);
        }
    };

    const handleNextPage = () => {
        setPage((current) =>
            Math.min(totalPages, current + 1)
        );
    };

    const handlePreviousPage = () => {
        setPage((current) =>
            Math.max(1, current - 1)
        );
    };

    if (authLoading) {
        return (
            <main className={styles.profile}>
                <div className={styles.loading}>
                    <div className={styles.loadingAvatar}/>

                    <div className={styles.loadingContent}>
                        <span/>
                        <span/>
                        <span/>
                    </div>
                </div>
            </main>
        );
    }

    if (!user) {
        return (
            <main className={styles.profile}>
                <div className={styles.state}>
                    <div className={styles.stateIcon}>
                        <User/>
                    </div>

                    <h1>{t("guestTitle")}</h1>
                    <p>{t("guestDescription")}</p>

                    <Link to={ROUTES.login} className={styles.primaryButton}>
                        <span>{t("guestButton")}</span>
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className={styles.profile}>
            <section className={styles.hero}>
                <div className={styles.badge}>
                    <span className={styles.badgeDot}/>
                    {t("badge")}
                </div>
                <div className={styles.heroGrid}>
                    <div className={styles.avatarBox}>
                        <div className={styles.avatar}>
                            {avatar ? (
                                <img src={avatar} alt={t("detailsName")}/>
                            ) : (
                                <User color="var(--accent)"/>
                            )}
                        </div>
                    </div>
                    <div className={styles.heroContent}>
                        <h1>
                            {user.name || t("detailsNameEmpty")}
                        </h1>
                        <p className={styles.heroEmail}>
                            {user.email}
                        </p>

                        <div className={styles.tags}>
                            <span className={styles.tag} data-admin={Boolean(user.is_admin)}>
                                {user.is_admin ? <ShieldCheck/> : <Sparkles/>}
                                {user.is_admin ? t("adminBadge") : t("userBadge")}
                            </span>

                            <span className={styles.tag}>
                                <BookOpen/>
                                {enrolledCourses.length} {t("coursesCount")}
                            </span>
                        </div>

                        <div className={styles.heroActions}>
                            <button type="button" className={styles.editButton} onClick={handleOpenEdit}
                                    disabled={editing || saving}>
                                <Pencil/>
                                <span>{t("editButton")}</span>
                            </button>

                            <button type="button" className={styles.refreshButton} onClick={handleRefresh}
                                    disabled={refreshing}>
                                <RefreshCw/>
                                <span>{refreshing ? t("refreshProcess") : t("refreshButton")}</span>
                            </button>

                            <button type="button" className={styles.logoutButton} onClick={handleOpenLogoutModal}
                                    disabled={loggingOut}>
                                <LogOut/>
                                <span>{t("logoutButton")}</span>
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* ---------- my courses ---------- */}

            <section className={styles.courses}>
                <div className={styles.sectionHeading}>
                    <div>
                        <span>{t("coursesEyebrow")}</span>
                        <h2>{t("coursesTitle")}</h2>
                    </div>

                    <Link to={ROUTES.courses} className={styles.sectionLink}>
                        {t("coursesLink")}
                    </Link>
                </div>

                {coursesLoading && (
                    <div className={styles.grid}>
                        {Array.from(
                            {length: 3},
                            (_, index) => (
                                <div className={styles.skeleton} key={index}>
                                    <div className={styles.skeletonImage}/>
                                    <div className={styles.skeletonBody}>
                                        <span/>
                                        <span/>
                                        <span/>
                                    </div>
                                </div>
                            )
                        )}
                    </div>
                )}

                {!coursesLoading && error && (
                    <div className={styles.empty}>
                        <div className={styles.emptyIcon}>
                            <ImageOff/>
                        </div>

                        <h3>{t("coursesErrorTitle")}</h3>
                        <p>{t("coursesErrorDescription")}</p>

                        <button type="button" className={styles.retryButton} onClick={fetchCourses}>
                            {t("coursesErrorRetry")}
                        </button>
                    </div>
                )}

                {!coursesLoading &&
                    !error &&
                    enrolledCourses.length === 0 && (
                        <div className={styles.empty}>
                            <div className={styles.emptyIcon}>
                                <BookOpen/>
                            </div>

                            <h3>{t("coursesEmptyTitle")}</h3>
                            <p>{t("coursesEmptyDescription")}</p>

                            <Link to={ROUTES.courses} className={styles.primaryButton}>
                                <span>{t("coursesLink")}</span>
                            </Link>
                        </div>
                    )}

                {!coursesLoading &&
                    !error &&
                    enrolledCourses.length > 0 && (
                        <div className={styles.grid}>
                            {enrolledCourses.map((course) => (
                                <Link className={styles.card} to={ROUTES.course + "/" + course.slug}
                                      key={course.slug}>
                                    <div className={styles.cardImage}>
                                        {course.main_image_url ? (
                                            <>
                                                <img src={course.main_image_url} alt="" loading="lazy"/>
                                                <div className={styles.imageOverlay}/>
                                            </>
                                        ) : (
                                            <ImageOff/>
                                        )}

                                        <span className={styles.cardLabel}>
                                            {t("coursesEyebrow")}
                                        </span>
                                    </div>

                                    <div className={styles.cardBody}>
                                        <div className={styles.cardTop}>
                                            <h3>{course.title}</h3>

                                            <span className={styles.cardArrow}>
                                                <BookOpen/>
                                            </span>
                                        </div>

                                        <p>{course.description}</p>

                                        <div className={styles.cardFooter}>
                                            <span>{t("coursesContinue")}</span>
                                            <span className={styles.cardLine}/>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}

                {!coursesLoading &&
                    !error &&
                    totalPages > 1 && (
                        <nav className={styles.pagination} aria-label={t("coursesTitle")}>
                            <button type="button" className={styles.pageButton} disabled={page <= 1}
                                    onClick={handlePreviousPage}>
                                ‹
                            </button>

                            <div className={styles.pageInfo}>
                                <strong>{page}</strong>
                                <span>/</span>
                                <span>{totalPages}</span>
                            </div>

                            <button type="button" className={styles.pageButton} disabled={page >= totalPages}
                                    onClick={handleNextPage}>
                                ›
                            </button>
                        </nav>
                    )}
            </section>

            {/* ---------- edit modal ---------- */}

            {editing && (
                <div
                    className={styles.modalOverlay}
                    onClick={() => {
                        if (!saving) {
                            handleCancelEdit();
                        }
                    }}
                >
                    <div
                        className={`${styles.modal} ${styles.modalWide}`}
                        onClick={(event) => event.stopPropagation()}
                    >
                        <button
                            type="button"
                            className={styles.modalClose}
                            onClick={handleCancelEdit}
                            disabled={saving}
                            aria-label={t("editClose")}
                        >
                            <X/>
                        </button>

                        <h2>{t("editTitle")}</h2>

                        <form className={styles.form} onSubmit={handleSave} noValidate>
                            <div className={styles.field}>
                                <label htmlFor="profile-name">{t("detailsName")}</label>

                                <input
                                    id="profile-name"
                                    type="text"
                                    value={name}
                                    onChange={handleNameChange}
                                    placeholder={t("detailsNamePlaceholder")}
                                    disabled={saving}
                                />

                                {fieldErrors.name && (
                                    <span className="error">{t(`fieldError.${fieldErrors.name}`)}</span>
                                )}
                            </div>

                            <div className={styles.field}>
                                <label htmlFor="profile-phone">{t("detailsPhone")}</label>

                                <input
                                    id="profile-phone"
                                    type="tel"
                                    inputMode="numeric"
                                    autoComplete="tel"
                                    value={phone}
                                    onChange={handlePhoneChange}
                                    onBlur={() => setPhone((current) => formatPhone(current))}
                                    placeholder={t("detailsPhonePlaceholder")}
                                    disabled={saving}
                                />

                                {fieldErrors.phone && (
                                    <span className="error">{t(`fieldError.${fieldErrors.phone}`)}</span>
                                )}
                            </div>

                            <div className={styles.field}>
                                <label htmlFor="profile-email">{t("detailsEmail")}</label>

                                <input
                                    id="profile-email"
                                    type="email"
                                    autoComplete="email"
                                    value={email}
                                    onChange={handleEmailChange}
                                    placeholder="user@example.com"
                                    disabled={saving}
                                />

                                {fieldErrors.email && (
                                    <span className="error">{t(`fieldError.${fieldErrors.email}`)}</span>
                                )}
                            </div>

                            {saveError && (
                                <div className={styles.formError}>{saveError}</div>
                            )}

                            <div className={styles.formActions}>
                                <button type="button" className={styles.cancelButton} onClick={handleCancelEdit}
                                        disabled={saving}>{t("editCancel")}</button>

                                <button type="submit" className={styles.saveButton} disabled={saving}>
                                    {saving ? t("editSaving") : t("editSave")}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ---------- logout modal ---------- */}

            {showLogoutModal && (
                <div
                    className={styles.modalOverlay}
                    onClick={() => {
                        if (!loggingOut) {
                            setShowLogoutModal(false);
                        }
                    }}
                >
                    <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
                        <div className={styles.modalIcon}>
                            <LogOut/>
                        </div>

                        <h2>{t("logoutTitle")}</h2>
                        <p>{t("logoutDescription")}</p>

                        <div className={styles.modalActions}>
                            <button type="button" className={styles.modalCancel}
                                    onClick={() => setShowLogoutModal(false)}
                                    disabled={loggingOut}>{t("logoutCancel")}</button>

                            <button type="button" className={styles.modalConfirm} onClick={handleLogout}
                                    disabled={loggingOut}>
                                {loggingOut ? t("logoutProcess") : t("logoutConfirm")}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
