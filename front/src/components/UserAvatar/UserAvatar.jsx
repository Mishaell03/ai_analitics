import {useAvatarImage} from "@/hooks/useAvatarImage.js";
import styles from "./userAvatar.module.css";

/**
 * Первая буква имени, иначе — первая буква почты.
 */
function getInitial(name, email) {
    return (name || email || "?").trim().charAt(0).toUpperCase();
}

/**
 * Аватар любого пользователя по подписанной ссылке с бэкенда.
 *
 * Пока картинка не приехала или её нет — показываем букву,
 * чтобы список не дёргался при загрузке.
 */
function UserAvatar({url, name, email, size = 38}) {
    const src = useAvatarImage(url);

    return (
        <span
            className={styles.avatar}
            style={{width: size, height: size}}
        >
            {src ? (
                <img src={src} alt={name || email || ""}/>
            ) : (
                <span
                    className={styles.initial}
                    style={{fontSize: Math.round(size / 2.6)}}
                >
                    {getInitial(name, email)}
                </span>
            )}
        </span>
    );
}

export default UserAvatar;
