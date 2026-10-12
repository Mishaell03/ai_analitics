export const API_ROUTES = {
// Auth
    LOGIN: "/auth",
    REGISTER: "/register",
    LOGOUT: "/logout",

// User
    USER_INFO: "/me",
    USER_UPDATE: "/me",
    USER_PROFILE: "/user/profile",

// Courses
    COURSES: "/courses",
    COURSE_BY_ID: (slug) => `/courses/${slug}`,
    ENROLL_COURSE_BY_ID: (slug) => `/courses/enroll/${slug}`,
    UNENROLL_COURSE_BY_ID: (slug) => `/courses/unenroll/${slug}`,

// Lessons
    LESSONS: "/lessons",
    LESSON_BY_ID: (id) => `/lessons/${id}`,

// Admin
    ADMIN_DASHBOARD: "/admin/dashboard",
};
