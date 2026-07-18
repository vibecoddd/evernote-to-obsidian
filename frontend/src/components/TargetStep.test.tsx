import { render, screen } from "@testing-library/react";
import { useReducer } from "react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";

import { initialWizardState, wizardReducer } from "../domain/wizardReducer";
import { TargetStep } from "./TargetStep";

beforeEach(() => {
  window.desktop = {
    getBackendUrl: vi.fn(), selectDirectory: vi.fn(), selectEnexFiles: vi.fn(), openPath: vi.fn(),
    setMigrationActive: vi.fn(), onCloseRequested: vi.fn(), confirmClose: vi.fn(),
  };
});

test("collects target settings and selects a Vault directory through the desktop bridge", async () => {
  const user = userEvent.setup();
  const dispatch = vi.fn();
  vi.mocked(window.desktop.selectDirectory).mockResolvedValue("/Users/alice/Vault");
  function Harness() {
    const [state, reduce] = useReducer(wizardReducer, initialWizardState);
    return <TargetStep target={state.target} dispatch={(action) => { dispatch(action); reduce(action); }} />;
  }
  render(<Harness />);

  await user.click(screen.getByRole("button", { name: "选择 Vault 目录" }));
  await user.click(screen.getByLabelText("如果不存在则创建 Vault"));
  await user.click(screen.getByLabelText("备份已有文件"));
  await user.click(screen.getByLabelText("转换表格"));
  await user.selectOptions(screen.getByLabelText("笔记组织方式"), "tags");
  await user.clear(screen.getByLabelText("附件文件夹"));
  await user.type(screen.getByLabelText("附件文件夹"), "media");
  await user.click(screen.getByLabelText("创建欢迎笔记"));
  await user.click(screen.getByLabelText("创建模板"));
  await user.clear(screen.getByLabelText("临时文件目录"));
  await user.type(screen.getByLabelText("临时文件目录"), "/tmp/migration");

  expect(window.desktop.selectDirectory).toHaveBeenCalledOnce();
  expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "form/target", target: { output: { obsidian_vault: "/Users/alice/Vault" } } }));
  expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "form/target", target: { conversion: { image_folder: "media" } } }));
  expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "form/target", target: { migration: { create_welcome_note: false } } }));
  expect(dispatch).toHaveBeenCalledWith(expect.objectContaining({ type: "form/target", target: { advanced: { temp_directory: "/tmp/migration" } } }));
  expect(screen.getByLabelText("附件文件夹")).toHaveValue("media");
});
