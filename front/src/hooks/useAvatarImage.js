import {useEffect, useState} from "react";
import ImageCache from "@/context/ImageCache.js";

/**
 * Стабильный ключ кэша — путь без query-параметров.
 * Подпись S3 меняется, путь остаётся прежним.
 */
function getCacheKey(url) {
    try {
        return new URL(url).pathname;
    } catch {
        return url;
    }
}

/**
 * Подписанная ссылка на minio → blob URL для <img src>.
 *
 * Сначала смотрим кэш, и только потом качаем: картинка не
 * перекачивается, пока не сменится путь (смена аватара).
 * blob URL освобождается, когда компонент больше не нужен.
 */
export function useAvatarImage(url) {
    const [src, setSrc] = useState(null);

    const cacheKey = url ? getCacheKey(url) : null;

    useEffect(() => {
        if (!url || !cacheKey) {
            setSrc(null);
            return;
        }

        let blobUrl;

        async function loadAvatar() {
            if (!await ImageCache.get(cacheKey)) {
                await ImageCache.save(url, cacheKey);
            }

            const loaded = await ImageCache.get(cacheKey);

            if (loaded) {
                blobUrl = loaded;
                setSrc(loaded);
            }
        }

        loadAvatar();

        return () => {
            if (blobUrl) {
                URL.revokeObjectURL(blobUrl);
            }
        };
    }, [url, cacheKey]);

    return src;
}
