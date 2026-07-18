import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(cleanup);

if (typeof document !== "undefined") {
  const root = document.createElement("div");
  root.id = "root";
  document.body.append(root);
}
