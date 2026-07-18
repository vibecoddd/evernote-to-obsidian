import "@testing-library/jest-dom/vitest";

if (typeof document !== "undefined") {
  const root = document.createElement("div");
  root.id = "root";
  document.body.append(root);
}
