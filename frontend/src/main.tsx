import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <main aria-live="polite">印象笔记迁移工具正在启动…</main>
  </StrictMode>,
);
