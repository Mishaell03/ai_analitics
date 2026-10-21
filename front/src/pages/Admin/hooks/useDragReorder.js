import {useCallback, useState} from "react";

/**
 * Перетаскивание строк таблицы.
 *
 * Хук хранит только визуальное состояние перетаскивания: индексы
 * исходной и текущей строк. Новый порядок и его сохранение выполняет
 * вызывающая сторона — списки курсов, модулей и уроков сохраняются
 * разными запросами.
 *
 * @param {Function} onDrop вызывается с (fromIndex, toIndex)
 * @returns {{
 *   dragIndex: number|null,
 *   dragOverIndex: number|null,
 *   getDragProps: Function,
 * }}
 */
export function useDragReorder(onDrop) {
    const [dragIndex, setDragIndex] = useState(null);
    const [dragOverIndex, setDragOverIndex] = useState(null);

    const reset = useCallback(() => {
        setDragIndex(null);
        setDragOverIndex(null);
    }, []);

    const getDragProps = useCallback((index, disabled = false) => ({
        draggable: !disabled,
        onDragStart: () => setDragIndex(index),
        onDragOver: (event) => {
            event.preventDefault();

            if (dragIndex === null || dragIndex === index) {
                return;
            }

            setDragOverIndex(index);
        },
        onDrop: () => {
            if (dragIndex !== null && dragIndex !== index) {
                onDrop(dragIndex, index);
            }

            reset();
        },
        onDragEnd: reset,
    }), [dragIndex, onDrop, reset]);

    return {dragIndex, dragOverIndex, getDragProps};
}
