import { useEffect, useMemo, useState, type Dispatch } from "react";

import type { ApiClient } from "../api/client";
import type { MigrationRequest, PreflightResult, WizardAction, WizardState } from "../domain/types";
import { ErrorPanel } from "./ErrorPanel";

function requestFrom(state: WizardState): MigrationRequest { return { ...state.target, source_mode: state.source.mode, evernote_backend: state.source.evernote_backend, evernote_credentials: state.source.credentials, input: state.source.input }; }

export function PreflightStep({ state, api, dispatch, onConfirm }: { state: WizardState; api: ApiClient; dispatch: Dispatch<WizardAction>; onConfirm: () => void }) {
  const config = useMemo(() => requestFrom(state), [state.source, state.target]);
  const [loading, setLoading] = useState(true);
  const [response, setResponse] = useState<PreflightResult | null>(null);
  useEffect(() => {
    let active = true;
    setLoading(true);
    void api.preflight(config).then((result) => { if (active) { setResponse(result); dispatch({ type: "preflight/result", result }); dispatch({ type: "error/clear" }); } }).catch(() => { if (active) dispatch({ type: "error", message: "预检失败，请检查后端连接后重试。" }); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [api, config, dispatch]);
  const result = response ?? state.preflight;
  return <section aria-labelledby="preflight-heading"><h2 id="preflight-heading">迁移预检</h2><p>正在检查来源文件、凭据和 Vault 写入权限。</p>
    {loading ? <p aria-live="polite">正在执行预检…</p> : <><ErrorPanel message={state.error} errors={result?.errors} warnings={result?.warnings} /><button type="button" onClick={onConfirm} disabled={!result?.ok}>确认并开始迁移</button></>}
  </section>;
}
