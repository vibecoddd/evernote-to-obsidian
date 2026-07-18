import type { Dispatch } from "react";

import type { DeepPartial, TargetConfig, WizardAction } from "../domain/types";
import { FormField } from "./FormField";

function Check({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return <label className="check"><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />{label}</label>;
}

export function targetIsValid(target: TargetConfig): boolean { return Boolean(target.output.obsidian_vault.trim() && target.conversion.image_folder.trim()); }

export function TargetStep({ target, dispatch }: { target: TargetConfig; dispatch: Dispatch<WizardAction> }) {
  const selectVault = async () => { const vault = await window.desktop.selectDirectory(); if (vault) dispatch({ type: "form/target", target: { output: { obsidian_vault: vault } } }); };
  const update = (targetUpdate: DeepPartial<TargetConfig>) => dispatch({ type: "form/target", target: targetUpdate });
  return <section aria-labelledby="target-heading"><h2 id="target-heading">配置目标</h2><p>选择 Obsidian Vault，并按需要调整转换设置。</p>
    <div className="form-grid"><FormField id="vault" label="Obsidian Vault 目录"><div className="path-picker"><input id="vault" value={target.output.obsidian_vault} onChange={(event) => update({ output: { obsidian_vault: event.target.value } })} /><button type="button" onClick={() => void selectVault()}>选择 Vault 目录</button></div></FormField>
      <FormField id="image-folder" label="附件文件夹"><input id="image-folder" value={target.conversion.image_folder} onChange={(event) => update({ conversion: { image_folder: event.target.value } })} /></FormField>
      <FormField id="organization" label="笔记组织方式"><select id="organization" value={target.file_organization.organize_by_tags ? "tags" : target.file_organization.organize_by_date ? "date" : "notebook"} onChange={(event) => update({ file_organization: { organize_by_notebook: event.target.value === "notebook", organize_by_tags: event.target.value === "tags", organize_by_date: event.target.value === "date" } })}><option value="notebook">按笔记本</option><option value="tags">按标签</option><option value="date">按日期</option></select></FormField>
      <FormField id="temp-directory" label="临时文件目录" hint="留空时使用系统临时目录。"><input id="temp-directory" value={target.advanced.temp_directory} onChange={(event) => update({ advanced: { temp_directory: event.target.value } })} /></FormField></div>
    <fieldset><legend>Vault 与转换</legend><Check label="如果不存在则创建 Vault" checked={target.output.create_vault_if_not_exists} onChange={(checked) => update({ output: { create_vault_if_not_exists: checked } })} /><Check label="备份已有文件" checked={target.output.backup_existing} onChange={(checked) => update({ output: { backup_existing: checked } })} /><Check label="保留 HTML 标签" checked={target.conversion.preserve_html_tags} onChange={(checked) => update({ conversion: { preserve_html_tags: checked } })} /><Check label="转换表格" checked={target.conversion.convert_tables} onChange={(checked) => update({ conversion: { convert_tables: checked } })} /><Check label="转换链接" checked={target.conversion.convert_links} onChange={(checked) => update({ conversion: { convert_links: checked } })} /><Check label="提取附件" checked={target.conversion.extract_images} onChange={(checked) => update({ conversion: { extract_images: checked } })} /></fieldset>
    <fieldset><legend>迁移后设置</legend><Check label="创建欢迎笔记" checked={target.migration.create_welcome_note} onChange={(checked) => update({ migration: { create_welcome_note: checked } })} /><Check label="创建模板" checked={target.migration.create_templates} onChange={(checked) => update({ migration: { create_templates: checked } })} /><Check label="保留临时文件" checked={target.migration.keep_temp_files} onChange={(checked) => update({ migration: { keep_temp_files: checked } })} /></fieldset>
  </section>;
}
