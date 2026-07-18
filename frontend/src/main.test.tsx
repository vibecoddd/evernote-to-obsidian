import "./main";

import { expect, test } from "vitest";

test("renders the startup status in the renderer root", () => {
  expect(document.querySelector("main")).toHaveTextContent(
    "印象笔记迁移工具正在启动…",
  );
});
