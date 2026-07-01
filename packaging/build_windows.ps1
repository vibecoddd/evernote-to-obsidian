param(
    [string]$Python = "python",
    [string]$Spec = "packaging/pyinstaller-evernote2obsidian.spec"
)

$ErrorActionPreference = "Stop"

& $Python -m pip install -r requirements-dev.txt
& $Python -m PyInstaller --clean --noconfirm $Spec
& $Python packaging/smoke_test.py

Write-Host "Windows bundle built under dist/evernote2obsidian"
