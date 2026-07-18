import { StrictMode, useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { createApiClient, type ApiClient } from "./api/client";
import { App } from "./App";
import "./styles/app.css";

function Bootstrap() {
  const [client, setClient] = useState<ApiClient | null>(null);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(async () => {
    setError(null);
    setClient(null);
    try {
      const backendUrl = await window.desktop?.getBackendUrl();
      if (!backendUrl) throw new Error("后端地址不可用，请重试。");
      setClient(createApiClient(backendUrl));
    } catch {
      setError("无法连接迁移后端，请确认应用仍在运行后重试。");
    }
  }, []);

  useEffect(() => { void start(); }, [start]);

  if (error) {
    return <main aria-live="assertive"><p>{error}</p><button type="button" onClick={() => void start()}>重试</button></main>;
  }
  if (client) return <App api={client} />;
  return <main aria-live="polite">印象笔记迁移工具正在启动…</main>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Bootstrap />
  </StrictMode>,
);
