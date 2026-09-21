const AVATAR_CACHE = "avatar-cache";

/**
 * Кэш аватаров в Cache API.
 *
 * Ключ кэша — стабильный (путь без query-параметров).
 * Fetch — по полному URL (с подписью S3 и т.п.).
 *
 * save(fetchUrl, cacheKey) — скачать по fetchUrl, положить по cacheKey
 * get(cacheKey)            — достать blob URL по cacheKey
 * clear()                  — очистить весь кэш
 */
class ImageCache {

    /**
     * Скачивает аватар по fetchUrl и кладёт в кэш под ключом cacheKey.
     * Если запись по cacheKey уже есть — не перезаписывает.
     * Возвращает true при успехе.
     */
    static async save(fetchUrl, cacheKey) {
        if (!fetchUrl || !cacheKey) {
            return false;
        }

        const cache = await caches.open(AVATAR_CACHE);

        const existing = await cache.match(cacheKey);
        if (existing) {
            return true;
        }

        const response = await fetch(fetchUrl, {
            credentials: "include",
        });

        if (!response.ok) {
            return false;
        }

        // Кладём по стабильному ключу, а не по подписанному URL
        await cache.put(cacheKey, response.clone());
        return true;
    }

    /**
     * Возвращает blob URL из кэша по стабильному ключу,
     * или null если не найден.
     */
    static async get(cacheKey) {
        if (!cacheKey) {
            return null;
        }

        const cache = await caches.open(AVATAR_CACHE);
        const response = await cache.match(cacheKey);

        if (!response) {
            return null;
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    }

    /**
     * Полная очистка кэша аватаров.
     */
    static async clear() {
        await caches.delete(AVATAR_CACHE);
    }
}

export default ImageCache;