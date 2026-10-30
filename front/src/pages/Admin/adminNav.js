import {
    BookOpen,
    ChartColumn,
    ScrollText,
    Users,
} from "lucide-react";
import {ROUTES} from "@/router/AppRouter.jsx";

/**
 * Навигация админки.
 *
 * Показываем только готовые разделы с рабочими маршрутами.
 * Заголовок группы (title) подставляется через i18n по ключу title.
 */
export const ADMIN_NAV = [
    {
        title: "sidebarGroupMain",
        items: [
            {
                title: "sidebarAnalytics",
                path: ROUTES.admin,
                icon: ChartColumn,
            },
            {
                title: "sidebarUsers",
                path: ROUTES.admin_users,
                icon: Users,
            },
            {
                title: "sidebarCourses",
                path: ROUTES.admin_courses,
                icon: BookOpen,
            },
            {
                title: "sidebarLogs",
                path: ROUTES.admin_logs,
                icon: ScrollText,
            },
        ],
    },
];
