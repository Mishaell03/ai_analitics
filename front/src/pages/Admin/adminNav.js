import {
    ChartColumn,
    ClipboardList,
    Flag,
    Settings,
    Users,
} from "lucide-react";
import {ROUTES} from "@/router/AppRouter.jsx";

/**
 * Навигация админки.
 *
 * path задан только у готовых разделов — у остальных soon: true,
 * они рисуются, но не кликаются, чтобы не вести в 404.
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
        ],
    },
    {
        title: "sidebarGroupManage",
        items: [
            {
                title: "sidebarAssignments",
                icon: ClipboardList,
                soon: true,
            },
            {
                title: "sidebarReports",
                icon: Flag,
                soon: true,
            },
            {
                title: "sidebarSettings",
                icon: Settings,
                soon: true,
            },
        ],
    },
];
