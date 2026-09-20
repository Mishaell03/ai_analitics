import {Route, Routes} from "react-router-dom";
import MainLayout from "./layouts/MainLayout.jsx";
import {Login} from "./pages/Auth/Login.jsx";
import {Registration} from "@/pages/Auth/Registration.jsx";
import {Home} from "@/pages/Home/Home.jsx";

function App() {

    return (
        <Routes>
            <Route element={<MainLayout/>}>
                <Route element={<Login/>} path='/login'/>
                <Route element={<Registration/>} path='/registration'/>
                <Route element={<Home/>} path='/'/>
            </Route>
        </Routes>
    )
}

export default App
