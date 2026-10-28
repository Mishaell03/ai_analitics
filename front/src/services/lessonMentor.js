/** Merge paginated history with a request that may already have arrived via POST. */
export function mergeMentorMessages(current, incoming) {
    const messages = new Map(current.map(item => [item.request_id, item]));
    for (const item of incoming) {
        const previous = messages.get(item.request_id);
        // An older history response must not turn a finished POST result back into pending.
        if (previous?.status && previous.status !== "pending" && item.status === "pending") continue;
        messages.set(item.request_id, item);
    }
    return [...messages.values()].sort((a, b) => a.question_id - b.question_id).slice(-10);
}
