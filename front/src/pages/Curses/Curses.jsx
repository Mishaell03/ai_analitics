import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./courses.module.css";
import {ArrowRight, ChevronLeft, ChevronRight, ImageOff, Search, SlidersHorizontal} from "lucide-react";
import {Link} from "react-router-dom";
import {useCallback, useEffect, useMemo, useRef, useState,} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {ROUTES} from "@/router/AppRouter.jsx";
import Description from "@/components/Markdown/Description.jsx";

export function Courses() {
    const t = useTranslation("courses.courses");

    const [courses, setCourses] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [activeFilter, setActiveFilter] = useState("all");
    const [filtersOpen, setFiltersOpen] = useState(false);
    const requestVersion = useRef(0);
    const searchDebounceTimer = useRef(null);

    const filters = useMemo(
        () => [
            {
                id: "all",
                label: t("filterAll"),
            },
            {
                id: "enrolled",
                label: t("filterEnrolled"),
            },
            {
                id: "not_enrolled",
                label: t("filterNotEnrolled"),
            },
        ],
        [t]
    );

    /*
     * ---------- load courses ----------
     */

    const fetchCourses = useCallback(async () => {
        const requestId = ++requestVersion.current;
        setLoading(true);
        setError(false);

        try {
            const query = debouncedSearch.trim().replace(/\s+/g, " ");
            const {data} = await api.get(API_ROUTES.COURSES, {
                params: {
                    page,
                    ...(query ? {q: query} : {}),
                    ...(activeFilter !== "all" ? {enrollment_filter: activeFilter} : {}),
                },
            });

            if (requestId !== requestVersion.current) return;
            setCourses(data.courses ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch {
            if (requestId !== requestVersion.current) return;
            setError(true);
        } finally {
            if (requestId === requestVersion.current) setLoading(false);
        }
    }, [page, debouncedSearch, activeFilter]);

    useEffect(() => () => window.clearTimeout(searchDebounceTimer.current), []);

    useEffect(() => {
        fetchCourses();
    }, [fetchCourses]);

    /*
     * ---------- filtering ----------
     */

    const filteredCourses = courses;

    /*
     * ---------- handlers ----------
     */

    const handleFilterChange = (filter) => {
        setPage(1);
        setActiveFilter(filter);
    };

    const handleSearchChange = (event) => {
        const value = event.target.value;
        setSearch(value);
        window.clearTimeout(searchDebounceTimer.current);
        searchDebounceTimer.current = window.setTimeout(
            () => {
                setPage(1);
                setDebouncedSearch(value);
            },
            300,
        );
    };

    const handleResetFilters = () => {
        window.clearTimeout(searchDebounceTimer.current);
        setSearch("");
        setDebouncedSearch("");
        setActiveFilter("all");
        setPage(1);
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
                           aria-label={t("searchPlaceholder")}
                           placeholder={t("searchPlaceholder")}/>
                </label>

                <div className={styles.filterWrapper}>
                    <button
                        type="button"
                        className={styles.filterToggle}
                        aria-expanded={filtersOpen}
                        aria-controls="course-filters"
                        aria-label={t("additionalFilters")}
                        onClick={() => setFiltersOpen((open) => !open)}
                    >
                        <SlidersHorizontal/>
                    </button>

                    <div className={styles.filters} id="course-filters" data-open={filtersOpen}>
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

                                        {course.description && <Description content={course.description} className={styles.cardDescription} preview/>}

                                        {course.is_enrolled && (
                                            <div className={styles.courseProgress} data-complete={course.is_course_completed}>
                                                {!course.is_course_completed && <span>{t("courseInProgress")}</span>}
                                                <small>{t("courseProgress")}: {course.lessons_completed}/{course.lessons_total}</small>
                                            </div>
                                        )}

                                        <div className={styles.cardFooter} data-complete={course.is_course_completed}>
                                            <span>{course.is_course_completed
                                                ? t("courseCompleted")
                                                : course.is_enrolled ? t("cardContinue") : t("cardAction")}</span>
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
