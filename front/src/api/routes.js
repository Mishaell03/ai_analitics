export const API_ROUTES = {
// Auth
    LOGIN: "/auth",
    REGISTER: "/register",
    LOGOUT: "/logout",

// User
    USER_INFO: "/me",
    USER_PROFILE: "/user/profile",

// Courses
    COURSES: "/courses",
    COURSE_BY_ID: (id) => `/courses/${id}`,

// Lessons
    LESSONS: "/lessons",
    LESSON_BY_ID: (id) => `/lessons/${id}`,
};
