import type { ChildProcess, SpawnOptions } from "node:child_process";

export interface BackendHandle {
  url: string;
  process: Pick<ChildProcess, "kill" | "killed" | "exitCode" | "once">;
  stop: () => Promise<void>;
}

export interface StartBackendOptions {
  appRoot?: string;
  env?: NodeJS.ProcessEnv;
  isPackaged?: boolean;
  platform?: NodeJS.Platform;
  reservePort?: () => Promise<number>;
  resourcesPath?: string;
  spawnImpl?: (
    command: string,
    args: readonly string[],
    options: SpawnOptions,
  ) => ChildProcess;
  stopTimeoutMs?: number;
}
