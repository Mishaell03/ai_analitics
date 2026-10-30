import {Route, Routes} from "react-router-dom";
import MainLayout from "./layouts/MainLayout.jsx";
import {Login} from "./pages/Auth/Login.jsx";
import {Registration} from "@/pages/Auth/Registration.jsx";
import {Home} from "@/pages/Home/Home.jsx";
import {ROUTES} from "@/router/AppRouter.jsx";
import {Courses} from "@/pages/Curses/Curses.jsx";
import {Course} from "@/pages/Curses/Course.jsx";
import {Lesson} from "@/pages/Curses/Lesson.jsx";
import {About} from "@/pages/About/About.jsx";
import {Profile} from "@/pages/Profile/Profile.jsx";
import {Teachers} from "@/pages/Teachers/Teachers.jsx";
import {Dashboard} from "@/pages/Admin/Dashboard/Dashboard.jsx";
import {Users} from "@/pages/Admin/Users/Users.jsx";
import AdminCourses from "@/pages/Admin/Courses/AdminCourses.jsx";
import AdminLayout from "@/pages/Admin/AdminLayout.jsx";
import AdminLogs from "@/pages/Admin/Logs/AdminLogs.jsx";

function App() {

    return (
        <Routes>
            <Route element={<MainLayout/>}>
                <Route element={<Login/>} path={ROUTES.login}/>
                <Route element={<Registration/>} path={ROUTES.registration}/>
                <Route element={<Home/>} path={ROUTES.home}/>
                <Route element={<Courses/>} path={ROUTES.courses}/>
                <Route element={<Course/>} path={ROUTES.course + "/:slug"}/>
                <Route element={<Lesson/>} path={ROUTES.lesson + "/:slug/modules/:moduleId/lessons/:lessonId"}/>
                <Route element={<About/>} path={ROUTES.about_us}/>
                <Route element={<Teachers/>} path={ROUTES.teachers}/>
                <Route element={<Profile/>} path={ROUTES.profile}/>

                {/* ---------- admin ---------- */}

                <Route element={<AdminLayout/>}>
                    <Route element={<Dashboard/>} path={ROUTES.admin}/>
                    <Route element={<Users/>} path={ROUTES.admin_users}/>
                    <Route element={<AdminLogs/>} path={ROUTES.admin_logs}/>
                    <Route element={<AdminCourses/>} path={ROUTES.admin_courses}/>
                </Route>
            </Route>
        </Routes>
    )
}

export default App
