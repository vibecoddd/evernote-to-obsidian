import type { MigrationProgress, SourceConfig, TargetConfig, WizardAction, WizardState } from "./types";

const initialSource: SourceConfig = {
  mode: "account", evernote_backend: "china", credentials: { username: "", password: "" },
  input: { enex_files: [], input_directory: "", encoding: "utf-8" },
};

const initialTarget: TargetConfig = {
  output: { obsidian_vault: "", create_vault_if_not_exists: true, backup_existing: true, overwrite_existing: false },
  conversion: { preserve_html_tags: false, convert_tables: true, convert_links: true, extract_images: true, image_folder: "attachments", max_filename_length: 100, clean_html: true, markdown_extensions: [".md"] },
  metadata: { include_created_date: true, include_modified_date: true, include_tags: true, include_notebook: true, include_source: true, date_format: "%Y-%m-%d %H:%M:%S", frontmatter_style: "yaml" },
  file_organization: { organize_by_notebook: true, organize_by_tags: false, organize_by_date: false, date_folder_format: "%Y/%m", handle_duplicates: "rename", invalid_char_replacement: "_", max_folder_depth: 10 },
  migration: { auto_open_obsidian: true, keep_temp_files: false, create_welcome_note: true, create_templates: true, optimize_settings: true },
  logging: { level: "INFO", file: "evernote2obsidian.log", console: true, format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s" },
  sync: { incremental: true, state_file: ".sync_state.json", check_modification_time: true, skip_unchanged: true },
  advanced: { parallel_processing: false, max_workers: 4, chunk_size: 100, memory_limit: "1GB", temp_directory: "" },
};

const initialMigration: MigrationProgress = { status: "idle", progress: 0, message: "" };

export const initialWizardState: WizardState = {
  step: 0, source: initialSource, target: initialTarget, preflight: null, migration: initialMigration,
  backend: { url: null, status: "starting" }, error: null, logs: [], result: null,
};

export function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "navigation/next": return { ...state, step: state.step + 1 };
    case "navigation/back": return { ...state, step: Math.max(0, state.step - 1) };
    case "form/source": return { ...state, source: { ...state.source, ...action.source, credentials: { ...state.source.credentials, ...action.source.credentials }, input: { ...state.source.input, ...action.source.input } } };
    case "form/target": return { ...state, target: { ...state.target, ...action.target, output: { ...state.target.output, ...action.target.output }, conversion: { ...state.target.conversion, ...action.target.conversion }, metadata: { ...state.target.metadata, ...action.target.metadata }, file_organization: { ...state.target.file_organization, ...action.target.file_organization }, migration: { ...state.target.migration, ...action.target.migration }, logging: { ...state.target.logging, ...action.target.logging }, sync: { ...state.target.sync, ...action.target.sync }, advanced: { ...state.target.advanced, ...action.target.advanced } } };
    case "preflight/result": return { ...state, preflight: action.result };
    case "migration/progress": return { ...state, migration: action.progress };
    case "migration/log": return { ...state, logs: [...state.logs, action.entry] };
    case "migration/terminal": return { ...state, result: action.result, migration: { ...state.migration, status: action.result.status, message: action.result.message, stats: action.result.stats } };
    case "backend/ready": return { ...state, backend: { url: action.url, status: "ready" }, error: null };
    case "error": return { ...state, error: action.message, backend: state.backend.status === "starting" ? { ...state.backend, status: "error" } : state.backend };
    case "error/clear": return { ...state, error: null };
    case "reset": return { ...initialWizardState, backend: state.backend };
  }
}
