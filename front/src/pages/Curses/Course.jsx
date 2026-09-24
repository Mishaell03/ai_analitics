import {getTranslation} from "@/locales/i18n.js";
import styles from "./course.module.css";
import {
    ArrowLeft,
    ArrowRight,
    BookOpen,
    ChevronLeft,
    ChevronRight,
    ExternalLink,
    ImageOff,
    Play,
} from "lucide-react";
import {Link, useParams} from "react-router-dom";
import {
    useCallback,
    useEffect,
    useState,
} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

const language = "ru";
const PAGE_SIZE = 20;

export function Course() {
    const t = (key) =>
        getTranslation(
            `courses.course.${key}`,
            language
        );

    const {slug} = useParams();

    const [course, setCourse] = useState(null);
    const [modules, setModules] = useState([]);

    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const fetchCourse = useCallback(async () => {
        setError(false);

        if (!course) {
            setLoading(true);
        }

        try {
            const {data} = await api.get(
                `${API_ROUTES.COURSES}/${slug}`,
                {
                    params: {
                        page,
                        page_size: PAGE_SIZE,
                    },
                }
            );

            if (data.course) {
                setCourse(data.course);
            }

            setModules(data.modules ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [slug, page]);

    useEffect(() => {
        fetchCourse();
    }, [fetchCourse]);

    const handlePreviousPage = () => {
        setPage((current) =>
            Math.max(1, current - 1)
        );
    };

    const handleNextPage = () => {
        setPage((current) =>
            Math.min(totalPages, current + 1)
        );
    };

    if (loading && !course) {
        return (
            <main className={styles.course}>
                <div className={styles.loading}>
                    <div className={styles.loadingImage}/>

                    <div className={styles.loadingContent}>
                        <span/>
                        <span/>
                        <span/>
                        <span/>
                    </div>
                </div>
            </main>
        );
    }

    if (error && !course) {
        return (
            <main className={styles.course}>
                <div className={styles.state}>
                    <div className={styles.stateIcon}>
                        <ImageOff/>
                    </div>

                    <h1>
                        {t("errorTitle")}
                    </h1>

                    <p>
                        {t("errorDescription")}
                    </p>

                    <button
                        type="button"
                        className={styles.retryButton}
                        onClick={fetchCourse}
                    >
                        {t("errorRetry")}
                    </button>
                </div>
            </main>
        );
    }

    return (
        <main className={styles.course}>
            <section className={styles.hero}>
                <Link
                    to="/courses"
                    className={styles.backLink}
                >
                    <ArrowLeft/>

                    <span>
                        {t("backToCourses")}
                    </span>
                </Link>

                <div className={styles.heroGrid}>
                    <div className={styles.heroImage}>
                        {course?.main_image_url ? (
                            <>
                                <img
                                    src={course.main_image_url}
                                    alt={course.title}
                                />

                                <div
                                    className={
                                        styles.heroImageOverlay
                                    }
                                />
                            </>
                        ) : (
                            <ImageOff/>
                        )}
                    </div>

                    <div className={styles.heroContent}>
                        <div className={styles.badge}>
                            <BookOpen/>

                            <span>
                                {t("courseLabel")}
                            </span>
                        </div>

                        <h1>
                            {course?.title}
                        </h1>

                        {course?.description && (
                            <p className={styles.description}>
                                {course.description}
                            </p>
                        )}

                        {course?.content_url && (
                            <a
                                href={course.content_url}
                                target="_blank"
                                rel="noreferrer"
                                className={
                                    styles.contentButton
                                }
                            >
                                <Play/>

                                <span>
                                    {t("startCourse")}
                                </span>

                                <ExternalLink/>
                            </a>
                        )}
                    </div>
                </div>
            </section>

            <section className={styles.modulesSection}>
                <div className={styles.sectionHeading}>
                    <div>
                        <span>
                            {t("modulesEyebrow")}
                        </span>

                        <h2>
                            {t("modulesTitle")}
                        </h2>
                    </div>

                    {totalPages > 1 && (
                        <p>
                            {t("pageInfo")} {page}{" "}
                            {t("pageOf")} {totalPages}
                        </p>
                    )}
                </div>

                {loading && (
                    <div className={styles.modulesLoading}>
                        <div
                            className={
                                styles.moduleSkeleton
                            }
                        />

                        <div
                            className={
                                styles.moduleSkeleton
                            }
                        />

                        <div
                            className={
                                styles.moduleSkeleton
                            }
                        />
                    </div>
                )}

                {!loading && error && (
                    <div className={styles.empty}>
                        <div className={styles.emptyIcon}>
                            <ImageOff/>
                        </div>

                        <h3>
                            {t("modulesErrorTitle")}
                        </h3>

                        <p>
                            {t("modulesErrorDescription")}
                        </p>

                        <button
                            type="button"
                            className={styles.retryButton}
                            onClick={fetchCourse}
                        >
                            {t("errorRetry")}
                        </button>
                    </div>
                )}

                {!loading &&
                    !error &&
                    modules.length === 0 && (
                        <div className={styles.empty}>
                            <div className={styles.emptyIcon}>
                                <BookOpen/>
                            </div>

                            <h3>
                                {t("emptyModulesTitle")}
                            </h3>

                            <p>
                                {t("emptyModulesDescription")}
                            </p>
                        </div>
                    )}

                {!loading &&
                    !error &&
                    modules.length > 0 && (
                        <div className={styles.modules}>
                            {modules.map(
                                (module, index) => (
                                    <article
                                        className={
                                            styles.module
                                        }
                                        key={
                                            module.module_id
                                        }
                                    >
                                        <div
                                            className={
                                                styles.moduleNumber
                                            }
                                        >
                                            {String(
                                                (page - 1) *
                                                PAGE_SIZE +
                                                index +
                                                1
                                            ).padStart(
                                                2,
                                                "0"
                                            )}
                                        </div>

                                        <div
                                            className={
                                                styles.moduleContent
                                            }
                                        >
                                            <div
                                                className={
                                                    styles.moduleTop
                                                }
                                            >
                                                <div>
                                                    <span
                                                        className={
                                                            styles.moduleLabel
                                                        }
                                                    >
                                                        {t(
                                                            "moduleLabel"
                                                        )}
                                                    </span>

                                                    <h3>
                                                        {
                                                            module.title
                                                        }
                                                    </h3>
                                                </div>

                                                {module.content_url && (
                                                    <a
                                                        href={
                                                            module.content_url
                                                        }
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className={
                                                            styles.moduleButton
                                                        }
                                                        aria-label={t(
                                                            "openModule"
                                                        )}
                                                    >
                                                        <ArrowRight/>
                                                    </a>
                                                )}
                                            </div>

                                            {module.description && (
                                                <p>
                                                    {
                                                        module.description
                                                    }
                                                </p>
                                            )}

                                            {module.content_url && (
                                                <a
                                                    href={
                                                        module.content_url
                                                    }
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className={
                                                        styles.moduleLink
                                                    }
                                                >
                                                    <span>
                                                        {t(
                                                            "openModule"
                                                        )}
                                                    </span>

                                                    <ExternalLink/>
                                                </a>
                                            )}
                                        </div>
                                    </article>
                                )
                            )}
                        </div>
                    )}

                {!loading &&
                    !error &&
                    totalPages > 1 && (
                        <nav
                            className={styles.pagination}
                            aria-label={t(
                                "paginationLabel"
                            )}
                        >
                            <button
                                type="button"
                                className={
                                    styles.pageButton
                                }
                                disabled={page <= 1}
                                onClick={
                                    handlePreviousPage
                                }
                                aria-label={t(
                                    "paginationPrevious"
                                )}
                            >
                                <ChevronLeft/>
                            </button>

                            <div
                                className={
                                    styles.pageInfo
                                }
                            >
                                <strong>{page}</strong>

                                <span>/</span>

                                <span>{totalPages}</span>
                            </div>

                            <button
                                type="button"
                                className={
                                    styles.pageButton
                                }
                                disabled={
                                    page >= totalPages
                                }
                                onClick={
                                    handleNextPage
                                }
                                aria-label={t(
                                    "paginationNext"
                                )}
                            >
                                <ChevronRight/>
                            </button>
                        </nav>
                    )}
            </section>
        </main>
    );
}