import {CheckCircle2, TriangleAlert} from "lucide-react";
import styles from "./adminToast.module.css";

/**
 * Уведомление о результате действия.
 *
 * Показывает одно сообщение, которое скрывает useToast.
 */
function AdminToast({message}) {
    if (!message) {
        return null;
    }

    return (
        <div className={styles.toast} data-tone={message.type}>
            {message.type === "success" ? <CheckCircle2/> : <TriangleAlert/>}
            <span>{message.text}</span>
        </div>
    );
}

export default AdminToast;
