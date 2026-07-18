import type { Dispatch } from "react";

import type { SourceConfig, WizardAction } from "../domain/types";
import { FormField } from "./FormField";

export function sourceIsValid(source: SourceConfig): boolean {
  return source.mode === "enex" ? source.input.enex_files.length > 0 : Boolean(source.credentials.username.trim() && source.credentials.password);
}

export function SourceStep({ source, dispatch }: { source: SourceConfig; dispatch: Dispatch<WizardAction> }) {
  const selectFiles = async () => {
    const files = await window.desktop.selectEnexFiles();
    if (files.length) dispatch({ type: "form/source", source: { input: { enex_files: files } } });
  };
  return <section aria-labelledby="source-heading"><h2 id="source-heading">选择数据源</h2><p>请选择要迁移的印象笔记帐户或已导出的 ENEX 文件。</p>
    <fieldset><legend>数据来源</legend>
      <label><input type="radio" name="source-mode" checked={source.mode === "account"} onChange={() => dispatch({ type: "form/source", source: { mode: "account" } })} />印象笔记帐户</label>
      <label><input type="radio" name="source-mode" checked={source.mode === "enex"} onChange={() => dispatch({ type: "form/source", source: { mode: "enex" } })} />ENEX 文件</label>
    </fieldset>
    {source.mode === "account" ? <div className="form-grid">
      <FormField id="username" label="用户名"><input id="username" autoComplete="username" value={source.credentials.username} onChange={(event) => dispatch({ type: "form/source", source: { credentials: { username: event.target.value } } })} /></FormField>
      <FormField id="password" label="密码" hint="密码仅保留在本次应用会话内。"><input id="password" type="password" autoComplete="current-password" value={source.credentials.password} onChange={(event) => dispatch({ type: "form/source", source: { credentials: { password: event.target.value } } })} /></FormField>
      <FormField id="backend" label="服务区域"><select id="backend" value={source.evernote_backend} onChange={(event) => dispatch({ type: "form/source", source: { evernote_backend: event.target.value as SourceConfig["evernote_backend"] } })}><option value="china">中国区</option><option value="international">国际区</option></select></FormField>
    </div> : <div><button type="button" onClick={() => void selectFiles()}>选择 ENEX 文件</button>{source.input.enex_files.length > 0 && <ul aria-label="已选择的 ENEX 文件">{source.input.enex_files.map((file) => <li key={file}>{file}</li>)}</ul>}</div>}
  </section>;
}
