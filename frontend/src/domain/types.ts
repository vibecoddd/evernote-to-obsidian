export type SourceMode = "account" | "enex";

export interface EvernoteCredentials {
  username: string;
  /** Kept only in renderer memory; never persist or log this value. */
  password: string;
}

export interface SourceConfig {
  mode: SourceMode;
  evernote_backend: "china" | "international";
  credentials: EvernoteCredentials;
  input: {
    enex_files: string[];
    input_directory: string;
    encoding: string;
  };
}

export interface TargetConfig {
  output: {
    obsidian_vault: string;
    create_vault_if_not_exists: boolean;
    backup_existing: boolean;
    overwrite_existing: boolean;
  };
  conversion: {
    preserve_html_tags: boolean;
    convert_tables: boolean;
    convert_links: boolean;
    extract_images: boolean;
    image_folder: string;
    max_filename_length: number;
    clean_html: boolean;
    markdown_extensions: string[];
  };
  metadata: {
    include_created_date: boolean;
    include_modified_date: boolean;
    include_tags: boolean;
    include_notebook: boolean;
    include_source: boolean;
    date_format: string;
    frontmatter_style: "yaml" | "json";
  };
  file_organization: {
    organize_by_notebook: boolean;
    organize_by_tags: boolean;
    organize_by_date: boolean;
    date_folder_format: string;
    handle_duplicates: "rename" | "skip" | "overwrite";
    invalid_char_replacement: string;
    max_folder_depth: number;
  };
  logging: { level: string; file: string; console: boolean; format: string };
  sync: { incremental: boolean; state_file: string; check_modification_time: boolean; skip_unchanged: boolean };
  advanced: { parallel_processing: boolean; max_workers: number; chunk_size: number; memory_limit: string; temp_directory: string };
}

export interface MigrationRequest extends TargetConfig {
  source_mode: SourceMode;
  evernote_backend: SourceConfig["evernote_backend"];
  evernote_credentials: EvernoteCredentials;
  input: SourceConfig["input"];
}

export interface PreflightIssue { code: string; message: string }
export interface PreflightResult {
  ok: boolean;
  errors: PreflightIssue[];
  warnings: PreflightIssue[];
  summary: { source_mode: SourceMode; enex_files: string[]; vault: string | null };
}

export interface ProgressStatistics {
  total_notes?: number;
  converted_notes?: number;
  total_attachments?: number;
  exported_files?: string[];
  errors?: string[];
}
export interface LogEntry { level: "info" | "error"; message: string; at: string }
export type MigrationStatus = "idle" | "running" | "cancelling" | "completed" | "failed" | "cancelled" | "not_found";
export interface MigrationProgress {
  taskId?: string;
  status: MigrationStatus;
  step?: number;
  totalSteps?: number;
  stepName?: string;
  progress: number;
  message: string;
  stats?: ProgressStatistics;
}
export interface TerminalResult { status: "completed" | "failed" | "cancelled"; message: string; stats?: ProgressStatistics }

export interface WizardState {
  step: number;
  source: SourceConfig;
  target: TargetConfig;
  preflight: PreflightResult | null;
  migration: MigrationProgress;
  backend: { url: string | null; status: "starting" | "ready" | "error" };
  error: string | null;
  logs: LogEntry[];
  result: TerminalResult | null;
}

export type DeepPartial<T> = T extends Array<infer Item>
  ? Item[]
  : T extends object
    ? { [Key in keyof T]?: DeepPartial<T[Key]> }
    : T;

export type WizardAction =
  | { type: "navigation/next" | "navigation/back" }
  | { type: "form/source"; source: DeepPartial<SourceConfig> }
  | { type: "form/target"; target: DeepPartial<TargetConfig> }
  | { type: "preflight/result"; result: PreflightResult }
  | { type: "migration/progress"; progress: MigrationProgress }
  | { type: "migration/log"; entry: LogEntry }
  | { type: "migration/terminal"; result: TerminalResult }
  | { type: "backend/ready"; url: string }
  | { type: "error"; message: string }
  | { type: "error/clear" }
  | { type: "reset" };
