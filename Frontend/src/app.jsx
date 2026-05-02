import { BrowserRouter, Routes, Route } from "react-router"
import Home from "@/routes/Home"
import Spectate from "@/routes/Spectate"
import AppLayout from "@/AppLayout"

export function App() {
    return (
        <BrowserRouter>
            <AppLayout>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/spectate/:gameId" element={<Spectate />} />
                </Routes>
            </AppLayout>
        </BrowserRouter>
    )
}