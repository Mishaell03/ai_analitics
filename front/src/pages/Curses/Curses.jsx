import {getTranslation} from "@/locales/i18n.js";
import styles from "./courses.module.css";
import {ArrowRight, ChevronLeft, ChevronRight, ImageOff, Search, SlidersHorizontal} from "lucide-react";
import {Link} from "react-router-dom";
import {useCallback, useEffect, useMemo, useState,} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";

const language = "ru";

export function Courses() {
    const t = (key) =>
        getTranslation(`courses.courses.${key}`, language);

    const [courses, setCourses] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const [search, setSearch] = useState("");
    const [activeFilter, setActiveFilter] = useState("all");

    const filters = useMemo(
        () => [
            {
                id: "all",
                label: t("filterAll"),
            },
            {
                id: "analytics",
                label: t("filterAnalytics"),
            },
            {
                id: "ai",
                label: t("filterAi"),
            },
            {
                id: "career",
                label: t("filterCareer"),
            },
        ],
        []
    );

    /*
     * ---------- load courses ----------
     */

    const fetchCourses = useCallback(async () => {
        setLoading(true);
        setError(false);

        try {
            const {data} = await api.get(API_ROUTES.COURSES, {
                params: {
                    page,
                },
            });

            setCourses(data.courses ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch {
            setError(true);
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        fetchCourses();
    }, [fetchCourses]);

    /*
     * ---------- filtering ----------
     */

    const filteredCourses = useMemo(() => {
        const query = search.trim().toLowerCase();

        return courses.filter((course) => {
            const matchesSearch =
                !query ||
                course.title
                    ?.toLowerCase()
                    .includes(query) ||
                course.description
                    ?.toLowerCase()
                    .includes(query);

            const matchesCategory =
                activeFilter === "all" ||
                !course.category ||
                course.category === activeFilter;

            return matchesSearch && matchesCategory;
        });
    }, [courses, search, activeFilter]);

    /*
     * ---------- handlers ----------
     */

    const handleFilterChange = (filter) => {
        setActiveFilter(filter);
    };

    const handleSearchChange = (event) => {
        setSearch(event.target.value);
    };

    const handleResetFilters = () => {
        setSearch("");
        setActiveFilter("all");
    };


    return (
        <main className={styles.courses}>
            <section className={styles.hero}>
                <div className={styles.heroContent}>
                    <div className={styles.badge}>
                        <span className={styles.badgeDot}/>
                        {t("headerBadge")}
                    </div>
                    <h1>{t("headerTitle")}
                        <span>{t("headerSubtitle")}</span>
                    </h1>
                    <p className={styles.heroDescription}>{t("headerDescription")}</p>
                </div>

                <div className={styles.heroStats}>
                    <div className={styles.stat}>
                        <strong>{totalPages > 1 ? `${totalPages}+` : courses.length}</strong>

                        <span>
                            {t("coursesCount")}
                        </span>
                    </div>

                    <div className={styles.statDivider}/>

                    <div className={styles.stat}>
                        <strong>100%</strong>

                        <span>
                            {t("onlineLearning")}
                        </span>
                    </div>
                </div>
            </section>

            {/* ---------- toolbar ---------- */}

            <section className={styles.toolbar}>
                <label className={styles.search}>
                    <Search/>

                    <input type="search" value={search} onChange={handleSearchChange}
                           placeholder={t("searchPlaceholder")}/>
                </label>

                <div className={styles.filterWrapper}>
                    <div className={styles.filterIcon}><SlidersHorizontal/></div>

                    <div className={styles.filters}>
                        {filters.map((filter) => (
                            <button key={filter.id} type="button" className={styles.filter}
                                    data-active={activeFilter === filter.id}
                                    onClick={() => handleFilterChange(filter.id)}>
                                {filter.label}
                            </button>
                        ))}
                    </div>
                </div>
            </section>

            {/* ---------- content ---------- */}

            <section className={styles.content}>
                <div className={styles.sectionHeading}>
                    <div>
                        <span>{t("catalogEyebrow")}</span>
                        <h2>{t("catalogTitle")}</h2>
                    </div>

                    {!loading && !error && (
                        <p>{filteredCourses.length}{" "}{t("coursesFound")}</p>
                    )}
                </div>

                {/* ---------- loading ---------- */}

                {loading && (
                    <div className={styles.grid}>
                        {Array.from(
                            {length: 8},
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

                {/* ---------- error ---------- */}

                {!loading && error && (
                    <div className={styles.state}>
                        <div className={styles.stateIcon}><ImageOff/></div>
                        <h3>{t("errorTitle")}</h3>
                        <p>{t("errorDescription")}</p>
                        <button type="button" className={styles.retryButton} onClick={fetchCourses} disabled={loading}>
                            {t("errorRetry")}
                        </button>
                    </div>
                )}

                {/* ---------- empty ---------- */}

                {!loading &&
                    !error &&
                    filteredCourses.length === 0 && (
                        <div className={styles.state}>
                            <div className={styles.stateIcon}><Search/></div>
                            <h3>{t("emptyTitle")}</h3>
                            <p>{t("emptyDescription")}</p>
                            <button type="button" className={styles.retryButton} onClick={handleResetFilters}>
                                {t("emptyReset")}
                            </button>
                        </div>
                    )}

                {/* ---------- courses ---------- */}

                {!loading &&
                    !error &&
                    filteredCourses.length > 0 && (
                        <div className={styles.grid}>
                            {filteredCourses.map((course) => (
                                <Link className={styles.card} to={ROUTES.course + "/" + course.slug} key={course.slug}>
                                    <div className={styles.cardImage}>
                                        {course.main_image_url ? (
                                            <>
                                                <img src={course.main_image_url} alt="" loading="lazy"/>
                                                <div className={styles.imageOverlay}/>
                                            </>
                                        ) : (
                                            <ImageOff/>
                                        )}

                                        <span className={styles.courseLabel}>
                                            {t("cardCourse")}
                                        </span>
                                    </div>

                                    <div className={styles.cardBody}>
                                        <div className={styles.cardTop}>
                                            <h3>
                                                {course.title}
                                            </h3>

                                            <span className={styles.cardArrow}>
                                                <ArrowRight/>
                                            </span>
                                        </div>

                                        <p>{course.description}</p>

                                        <div className={styles.cardFooter}>
                                            <span>{course.is_enrolled ? t("cardContinue") : t("cardAction")}</span>
                                            <span className={styles.cardLine}/>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
            </section>

            {/* ---------- pagination ---------- */}

            {!loading && !error && totalPages > 1 && (
                <nav className={styles.pagination} aria-label={t("paginationLabel")}>
                    <button type="button" className={styles.pageButton} disabled={page <= 1}
                            onClick={() => setPage((current) => current - 1)} aria-label={t("paginationPrevious")}>
                        <ChevronLeft/>
                    </button>

                    <div className={styles.pageInfo}>
                        <strong>{page}</strong>
                        <span>/</span>
                        <span>{totalPages}</span>
                    </div>

                    <button type="button" className={styles.pageButton} disabled={page >= totalPages}
                            onClick={() => setPage((current) => current + 1)} aria-label={t("paginationNext")}>
                        <ChevronRight/>
                    </button>
                </nav>
            )}
        </main>
    );
}