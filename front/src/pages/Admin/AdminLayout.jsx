import {Outlet} from "react-router-dom";
import AdminSidebar from "@/pages/Admin/AdminSidebar.jsx";
import styles from "./adminLayout.module.css";

/**
 * Оболочка админки: слева панель навигации, справа текущий раздел.
 */
function AdminLayout() {
    return (
        <main className={styles.admin}>
            <AdminSidebar/>

            <div className={styles.content}>
                <Outlet/>
            </div>
        </main>
    );
}

export default AdminLayout;
