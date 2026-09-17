import {Route, Routes} from "react-router-dom";
import MainLayout from "./layouts/MainLayout.jsx";
import {Login} from "./pages/Auth/Login.jsx";

function App() {

    return (
        <Routes>
            <Route element={<MainLayout/>}>
                <Route element={<Login/>} path='/login'/>
            </Route>
        </Routes>
    )
}

export default App
