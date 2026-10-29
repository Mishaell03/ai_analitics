import {useEffect, useRef, useState} from "react";
import {ChevronLeft, ChevronRight, Maximize, Minimize, Presentation} from "lucide-react";
import {parseAssetReference} from "@/services/media.js";
import {useTranslation} from "@/hooks/useTranslation.js";
import styles from "./markdown.module.css";

function MarkdownSlides({slides = [], media, onMediaError}) {
    const t = useTranslation("courses.course");
    const [index, setIndex] = useState(0);
    const [expanded, setExpanded] = useState(false);
    const [failedUrl, setFailedUrl] = useState(null);
    const root = useRef(null);
    const touch = useRef(null);
    const current = Math.min(index, Math.max(0, slides.length - 1));
    const slide = slides[current];
    const file = media?.[parseAssetReference(slide?.src)];
    const imageUrl = file?.kind === "image" ? file.url : null;

    useEffect(() => {
        const element = root.current;
        const syncFullscreen = () => setExpanded(document.fullscreenElement === element);
        document.addEventListener("fullscreenchange", syncFullscreen);
        return () => {
            document.removeEventListener("fullscreenchange", syncFullscreen);
            if (document.fullscreenElement === element && document.exitFullscreen) {
                document.exitFullscreen().catch(() => {});
            }
        };
    }, []);

    useEffect(() => {
        if (!expanded) return;
        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        const escape = (event) => {
            if (event.key === "Escape" && document.fullscreenElement !== root.current) {
                setExpanded(false);
            }
        };
        document.addEventListener("keydown", escape);
        return () => {
            document.body.style.overflow = previousOverflow;
            document.removeEventListener("keydown", escape);
        };
    }, [expanded]);

    const navigate = (step) => {
        setIndex((previous) => Math.max(0, Math.min(slides.length - 1, previous + step)));
    };

    const toggleFullscreen = async () => {
        if (expanded) {
            if (document.fullscreenElement === root.current) {
                await document.exitFullscreen().catch(() => {});
            } else {
                setExpanded(false);
            }
            return;
        }
        // На мобильных браузерах без Fullscreen API остаётся полноэкранный режим страницы.
        try {
            if (!root.current.requestFullscreen) throw new Error("Fullscreen unavailable");
            await root.current.requestFullscreen();
            setExpanded(true);
        } catch {
            setExpanded(true);
        }
    };

    return (
        <section ref={root} className={styles.slides} data-expanded={expanded}
                 aria-label={t("slidesTitle")} aria-roledescription={t("slidesCarousel")}
                 tabIndex={0} onKeyDown={(event) => {
                     if (expanded && event.key === "Escape" && document.fullscreenElement !== root.current) {
                         event.preventDefault();
                         event.stopPropagation();
                         setExpanded(false);
                         return;
                     }
                     if (expanded && event.key === "Tab") {
                         const buttons = root.current.querySelectorAll("button:not(:disabled)");
                         const first = buttons[0];
                         const last = buttons[buttons.length - 1];
                         if (event.shiftKey && (event.target === first || event.target === root.current)) {
                             event.preventDefault();
                             last.focus();
                         } else if (!event.shiftKey && event.target === last) {
                             event.preventDefault();
                             first.focus();
                         }
                         return;
                     }
                     if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
                     if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
                         event.preventDefault();
                         event.stopPropagation();
                         navigate(event.key === "ArrowLeft" ? -1 : 1);
                     }
                 }}>
            <div className={styles.slidesHeader}>
                <span><Presentation size={18} aria-hidden="true"/>{t("slidesTitle")}</span>
                <button type="button" className={styles.slidesButton} onClick={toggleFullscreen}
                        aria-label={t(expanded ? "slidesExitFullscreen" : "slidesFullscreen")}
                        title={t(expanded ? "slidesExitFullscreen" : "slidesFullscreen")}
                        aria-pressed={expanded}>
                    {expanded ? <Minimize size={18} aria-hidden="true"/> : <Maximize size={18} aria-hidden="true"/>}
                </button>
            </div>
            <div className={styles.slidesStage}
                 onTouchStart={(event) => {
                     touch.current = event.touches.length === 1
                         ? {x: event.touches[0].clientX, y: event.touches[0].clientY} : null;
                 }}
                 onTouchMove={(event) => { if (event.touches.length !== 1) touch.current = null; }}
                 onTouchCancel={() => { touch.current = null; }}
                 onTouchEnd={(event) => {
                     const start = touch.current;
                     touch.current = null;
                     if (!start || event.touches.length || !event.changedTouches.length) return;
                     const dx = event.changedTouches[0].clientX - start.x;
                     const dy = event.changedTouches[0].clientY - start.y;
                     if (Math.abs(dx) >= 50 && Math.abs(dx) > Math.abs(dy)) navigate(dx < 0 ? 1 : -1);
                 }}>
                {imageUrl && failedUrl !== imageUrl ? (
                    <img key={imageUrl} className={styles.slidesImage} src={imageUrl}
                         alt={slide.alt || file.original_name || t("slidesSlide", {number: current + 1})}
                         title={slide.title || undefined} draggable={false}
                         onError={() => {
                             setFailedUrl(imageUrl);
                             onMediaError?.(file.media_key || parseAssetReference(slide.src));
                         }}/>
                ) : (
                    <p className={styles.slidesPlaceholder} role="status">
                        {t(slide ? "slidesUnavailable" : "slidesEmpty")}
                    </p>
                )}
            </div>
            <div className={styles.slidesControls}>
                <button type="button" className={styles.slidesButton} disabled={!slides.length || current === 0}
                        onClick={() => navigate(-1)} aria-label={t("slidesPrevious")}>
                    <ChevronLeft size={18} aria-hidden="true"/><span>{t("slidesPrevious")}</span>
                </button>
                <span className={styles.slidesCounter} role="status" aria-live="polite" aria-atomic="true"
                      aria-label={t("slidesCounter", {current: slides.length ? current + 1 : 0, total: slides.length})}>
                    {slides.length ? current + 1 : 0} / {slides.length}
                </span>
                <button type="button" className={styles.slidesButton} disabled={!slides.length || current === slides.length - 1}
                        onClick={() => navigate(1)} aria-label={t("slidesNext")}>
                    <span>{t("slidesNext")}</span><ChevronRight size={18} aria-hidden="true"/>
                </button>
            </div>
        </section>
    );
}

export default MarkdownSlides;
