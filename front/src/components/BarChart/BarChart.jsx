import {formatNumber} from "@/services/format.js";
import styles from "./barChart.module.css";

// сколько делений у шкалы по вертикали
const GRID_STEPS = 4;

// запас сверху, чтобы тултип над столбцом не наезжал на заголовок
const HEADROOM = 0.85;

/**
 * Округляет шаг шкалы к "красивому" значению 1 / 2 / 5 / 10,
 * чтобы подписи оси не выглядели как 37 или 213.
 */
function niceStep(value) {
    const rough = value / GRID_STEPS;
    const magnitude = 10 ** Math.floor(Math.log10(rough || 1));
    const normalized = rough / magnitude;

    const factor =
        normalized <= 1 ? 1 :
            normalized <= 2 ? 2 :
                normalized <= 5 ? 5 :
                    10;

    return factor * magnitude;
}

/**
 * Верхняя граница шкалы с запасом под тултип.
 */
function getScale(values) {
    const peak = Math.max(...values, 1);

    let step = niceStep(peak);

    if (peak / (step * GRID_STEPS) > HEADROOM) {
        step *= 2;
    }

    return step * GRID_STEPS;
}

/**
 * Столбчатая диаграмма.
 *
 * data — [{key, title, value}]. Значения приходят из API,
 * пустой массив разметку не ломает: показывается пустая шкала.
 */
function BarChart({data, label, unit, loading = false, skeletonRows = 3}) {
    const max = getScale(data.map((item) => item.value));

    const ticks = Array.from(
        {length: GRID_STEPS + 1},
        (_, index) => (max / GRID_STEPS) * index
    );

    const bars = loading
        ? Array.from({length: skeletonRows}, (_, index) => ({key: index, title: ""}))
        : data;

    return (
        <div
            className={styles.chart}
            role="img"
            aria-label={label}
            aria-busy={loading}
            data-loading={loading}
        >
            <div className={styles.plot}>
                {ticks.map((tick) => (
                    <span
                        key={tick}
                        className={styles.gridline}
                        style={{bottom: `${(tick / max) * 100}%`}}
                    />
                ))}
            </div>

            <div className={styles.axis}>
                {[...ticks].reverse().map((tick) => (
                    <span
                        key={tick}
                        className={styles.tick}
                        style={{bottom: `calc(${(tick / max) * 100}% - 0.55em)`}}
                    >
                        {formatNumber(tick)}
                    </span>
                ))}
            </div>

            <div className={styles.bars}>
                {bars.map((item, index) => (
                    <div
                        className={styles.column}
                        key={item.key}
                        data-empty={!loading && !item.value}
                    >
                        <div className={styles.track}>
                            <div
                                className={styles.bar}
                                data-top={index === 0}
                                style={{
                                    height: loading
                                        ? "100%"
                                        : `${Math.max((item.value / max) * 100, 2)}%`,
                                }}
                            >
                                {!loading && (
                                    <span className={styles.value}>
                                        {formatNumber(item.value)}
                                        <em>{unit}</em>
                                    </span>
                                )}
                            </div>
                        </div>

                        <span className={styles.title}>{item.title}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default BarChart;
