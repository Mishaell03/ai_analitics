import { Outlet } from "react-router-dom";

const MainLayout = () => {
    return (
        <div className="app">
            <header>
                {/* Header */}
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