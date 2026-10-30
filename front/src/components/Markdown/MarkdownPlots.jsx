import styles from "./markdown.module.css";
import {useTranslation} from "@/hooks/useTranslation.js";

export default function MarkdownPlots({plots = []}) {
    const t = useTranslation("courses.course");
    return <div className={styles.plotGallery}>
        {plots.slice(0, 3).filter((plot) => typeof plot === "string"
            && plot.length <= 349528 && /^[A-Za-z0-9+/]+={0,2}$/.test(plot))
            .map((plot, index) => <figure key={index}>
                <img src={`data:image/png;base64,${plot}`} alt={t("codeExercisePlot", {number: index + 1})}/>
            </figure>)}
    </div>;
}
