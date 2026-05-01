import { createRoot } from "react-dom/client";
import { App } from "@/app";
import "@/styles/main.css";

const root = document.querySelector("#root");
const reactRoot = createRoot(root);

reactRoot.render(<App />);
