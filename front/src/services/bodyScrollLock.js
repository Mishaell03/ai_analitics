const locksByBody = new WeakMap();

/** Блокирует фон до закрытия последнего окна, независимо от порядка закрытия. */
export function lockBodyScroll(body = document.body) {
    let state = locksByBody.get(body);
    if (!state) {
        state = {
            locks: new Set(),
            overflow: body.style.getPropertyValue("overflow"),
            priority: body.style.getPropertyPriority("overflow"),
        };
        locksByBody.set(body, state);
        body.style.setProperty("overflow", "hidden");
    }

    const token = Symbol();
    state.locks.add(token);

    return () => {
        if (!state.locks.delete(token) || state.locks.size) return;

        if (state.overflow) {
            body.style.setProperty("overflow", state.overflow, state.priority);
        } else {
            body.style.removeProperty("overflow");
        }
        locksByBody.delete(body);
    };
}
