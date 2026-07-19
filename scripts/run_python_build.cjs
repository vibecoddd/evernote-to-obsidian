#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const projectRoot = path.resolve(__dirname, "..");
const buildScript = path.join("scripts", "build_electron_app.py");
const versionCheck = "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)";

function candidates() {
  const result = [];
  if (process.env.PYTHON) {
    result.push([process.env.PYTHON]);
  }

  const venvPython =
    process.platform === "win32"
      ? path.join(projectRoot, ".venv", "Scripts", "python.exe")
      : path.join(projectRoot, ".venv", "bin", "python");
  if (fs.existsSync(venvPython)) {
    result.push([venvPython]);
  }

  if (process.platform === "win32") {
    result.push(["py", "-3"], ["python"]);
  } else {
    result.push(["python3"], ["python"]);
  }
  return result;
}

function isSupportedPython(command) {
  const check = spawnSync(command[0], [...command.slice(1), "-c", versionCheck], {
    cwd: projectRoot,
    stdio: "ignore",
  });
  return check.status === 0;
}

const python = candidates().find(isSupportedPython);
if (!python) {
  console.error("Could not find Python 3.8+ for Electron packaging.");
  process.exit(1);
}

const run = spawnSync(python[0], [...python.slice(1), buildScript, ...process.argv.slice(2)], {
  cwd: projectRoot,
  stdio: "inherit",
  env: process.env,
});

if (run.error) {
  console.error(run.error.message);
  process.exit(1);
}

process.exit(run.status === null ? 1 : run.status);
