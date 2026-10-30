import { Outlet } from "react-router-dom";
import Header from "@/layouts/Header/Header.jsx";
import RouteScrollReset from "@/components/Navigation/RouteScrollReset.jsx";

const MainLayout = () => {
    return (
        <div className="app">
            <RouteScrollReset/>
            <header>
                 <Header/>
            </header>

            <main>
                <Outlet />
            </main>


            <header>
                {/* Footer */}
            </header>
        </div>
    );
};

export default MainLayout;
