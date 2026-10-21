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
    ADMIN_USERS: "/admin/users",
    ADMIN_USER_DETAIL: (id) => `/admin/users/${id}`,
    ADMIN_USER_BLOCK: (id) => `/admin/users/${id}/block`,

// Admin courses
    ADMIN_COURSES: "/admin/courses",
    ADMIN_COURSE_BY_ID: (id) => `/admin/courses/${id}`,
    ADMIN_COURSE_ACTIVATE: (id) => `/admin/courses/${id}/activate`,
    ADMIN_COURSE_DEACTIVATE: (id) => `/admin/courses/${id}/deactivate`,

// Admin modules
    ADMIN_COURSE_MODULES: (courseId) => `/admin/courses/${courseId}/modules`,
    ADMIN_COURSE_MODULES_REORDER: (courseId) => `/admin/courses/${courseId}/modules/reorder`,
    ADMIN_MODULES: "/admin/modules",
    ADMIN_MODULE_BY_ID: (id) => `/admin/modules/${id}`,
    ADMIN_MODULE_ACTIVATE: (id) => `/admin/modules/${id}/activate`,
    ADMIN_MODULE_DEACTIVATE: (id) => `/admin/modules/${id}/deactivate`,

// Admin lessons
    ADMIN_COURSE_LESSONS: (courseId, moduleId) => `/admin/courses/${courseId}/modules/${moduleId}/lessons`,
    ADMIN_COURSE_LESSONS_REORDER: (courseId, moduleId) =>
        `/admin/courses/${courseId}/modules/${moduleId}/lessons/reorder`,
    ADMIN_LESSON: (courseId, moduleId, lessonId) =>
        `/admin/courses/${courseId}/modules/${moduleId}/lessons/${lessonId}`,
    ADMIN_LESSON_CONTENT: (courseId, moduleId, lessonId) =>
        `/admin/courses/${courseId}/modules/${moduleId}/lessons/${lessonId}/content`,
    ADMIN_LESSON_UPLOAD_URL: (courseId, moduleId, lessonId) =>
        `/admin/courses/${courseId}/modules/${moduleId}/lessons/${lessonId}/upload-url`,

// Admin covers
    ADMIN_COURSE_IMAGE: (courseSlug) => `/admin/courses/${courseSlug}/image`,

// Admin lesson media
    ADMIN_LESSON_MEDIA: (courseId, moduleId, lessonId) =>
        `/admin/courses/${courseId}/modules/${moduleId}/lessons/${lessonId}/media`,
    ADMIN_LESSON_MEDIA_ITEM: (lessonId, mediaKey) => `/admin/lessons/${lessonId}/media/${mediaKey}`,
    ADMIN_MEDIA_URL: (mediaKey) => `/admin/media/${mediaKey}/url`,
};
