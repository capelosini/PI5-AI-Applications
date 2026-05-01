import { BrowserRouter, Routes, Route } from "react-router"
import Home from "@/routes/Home"
import AppLayout from "@/AppLayout"

export function App() {
    return (
        <BrowserRouter>
            <AppLayout>
                <Routes>
                    <Route path="/" element={<Home />} />
                </Routes>
            </AppLayout>
        </BrowserRouter>
    )
}