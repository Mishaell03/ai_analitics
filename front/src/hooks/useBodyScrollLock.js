import {useEffect} from "react";
import {lockBodyScroll} from "@/services/bodyScrollLock.js";

export function useBodyScrollLock(locked = true) {
    useEffect(() => {
        if (locked) return lockBodyScroll();
    }, [locked]);
}
