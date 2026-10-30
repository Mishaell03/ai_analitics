/** Новые страницы дополняют консоль, пересечения страниц не дублируются. */
export function appendLogItems(current, incoming, isAI) {
    const key = (item) => isAI ? item.question_id : `${item.source}-${item.id}`;
    const items = new Map(current.map((item) => [key(item), item]));
    for (const item of incoming) items.set(key(item), item);
    return [...items.values()];
}
