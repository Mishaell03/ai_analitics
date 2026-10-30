import {useLayoutEffect, useRef} from "react";
import {useLocation} from "react-router-dom";

function RouteScrollReset() {
    const {pathname, search} = useLocation();
    const previousPage = useRef({pathname, search});

    useLayoutEffect(() => {
        const previous = previousPage.current;
        previousPage.current = {pathname, search};

        // Первую загрузку не трогаем: при обновлении позицию восстанавливает браузер.
        if (previous.pathname !== pathname || previous.search !== search) {
            window.scrollTo({top: 0, left: 0, behavior: "instant"});
        }
    }, [pathname, search]);

    return null;
}

export default RouteScrollReset;
