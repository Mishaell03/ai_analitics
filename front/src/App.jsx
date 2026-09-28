import {Route, Routes} from "react-router-dom";
import MainLayout from "./layouts/MainLayout.jsx";
import {Login} from "./pages/Auth/Login.jsx";
import {Registration} from "@/pages/Auth/Registration.jsx";
import {Home} from "@/pages/Home/Home.jsx";
import {ROUTES} from "@/router/AppRouter.jsx";
import {Courses} from "@/pages/Curses/Curses.jsx";
import {Course} from "@/pages/Curses/Course.jsx";
import {About} from "@/pages/About/About.jsx";

function App() {

    return (
        <Routes>
            <Route element={<MainLayout/>}>
                <Route element={<Login/>} path={ROUTES.login}/>
                <Route element={<Registration/>} path={ROUTES.registration}/>
                <Route element={<Home/>} path={ROUTES.home}/>
                <Route element={<Courses/>} path={ROUTES.courses}/>
                <Route element={<Course/>} path={ROUTES.course + "/:slug"}/>
                <Route element={<About/>} path={ROUTES.about_us}/>
            </Route>
        </Routes>
    )
}

export default App
