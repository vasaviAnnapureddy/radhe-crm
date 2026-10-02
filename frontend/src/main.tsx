import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Fonts are bundled with the app, so no request goes to an outside font service.
import "@fontsource-variable/fraunces";
import "@fontsource-variable/manrope";
import "./styles/theme.css";
import App from "./app/App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
