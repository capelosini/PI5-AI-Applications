import { createRoot } from "react-dom/client"
import { App } from "@/app"

const root = document.querySelector("#root")
const reactRoot = createRoot(root)

reactRoot.render(<App />)