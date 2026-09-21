import {useEffect, useState} from "react";
import {useAuth} from "@/context/AuthContext.jsx";
import ImageCache from "@/context/ImageCache.js";
import styles from "./avatar.module.css";
import {User} from "lucide-react";

function Avatar() {
    const {user} = useAuth();
    const [avatar, setAvatar] = useState(null);

    useEffect(() => {
        if (!user?.has_image || !user?.avatar_key) {
            setAvatar(null);
            return;
        }

        let url;

        async function loadAvatar() {
            const blobUrl = await ImageCache.get(user.avatar_key);

            if (blobUrl) {
                url = blobUrl;
                setAvatar(url);
            }
        }

        loadAvatar();

        return () => {
            if (url) {
                URL.revokeObjectURL(url);
            }
        };
    }, [user?.avatar_key]);


    return (
        <div className={styles.avatar}>
            {avatar ? (
                <img
                    src={avatar}
                    alt="avatar"
                />
            ) : <User color="var(--accent)"/>
            }
        </div>
    );
}

export default Avatar;