import {useCallback, useEffect, useRef, useState} from "react";

const TOAST_DURATION = 4000;

/**
 * Короткое уведомление о результате действия.
 *
 * Показывает одно сообщение за раз и прячет его через несколько секунд.
 * Таймер сбрасывается при размонтировании, чтобы не обновлять состояние
 * уже закрытой страницы.
 *
 * @returns {{message: {type: string, text: string}|null, showMessage: Function, hideMessage: Function}}
 */
export function useToast() {
    const [message, setMessage] = useState(null);

    const timerRef = useRef(null);

    const hideMessage = useCallback(() => {
        window.clearTimeout(timerRef.current);
        timerRef.current = null;

        setMessage(null);
    }, []);

    const showMessage = useCallback((type, text) => {
        window.clearTimeout(timerRef.current);

        setMessage({type, text});

        timerRef.current = window.setTimeout(() => {
            timerRef.current = null;
            setMessage(null);
        }, TOAST_DURATION);
    }, []);

    useEffect(() => () => {
        window.clearTimeout(timerRef.current);
    }, []);

    return {message, showMessage, hideMessage};
}
