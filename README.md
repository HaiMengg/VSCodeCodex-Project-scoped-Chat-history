# Codex Workspace History

An unofficial patch for the Codex VS Code extension that shows recent chats for
the workspace you currently have open, instead of mixing chats across projects.

The patch filters sidebar history by the chat's recorded working directory.
It changes visibility only: your chats are not deleted or moved.

## Compatibility

- **Codex extension:** `openai.chatgpt` version **26.1021.22027** only.
- **Python:** 3.9 or newer. No third-party packages required.
- **Verified environment:** Windows with VS Code. The installer supports default
  macOS/Linux paths, but those environments have not been verified live.
- Your account must be able to write to the extension's installation folder.

This is a local modification, not an official OpenAI feature or a separate VS Code
extension. It checks the version and expected bundle fragments before patching.
Unsupported builds are rejected instead of modified.

## Install on Windows

1. Clone or download this repository. Keep its files together.
2. Run **Check.cmd** to check compatibility without changing files.
3. Run **Install.cmd** to apply the patch and create backups.
4. Reopen the Codex sidebar. If old history remains, fully close all VS Code
   windows and open VS Code again.

The installer automatically locates the supported Codex extension in
`%USERPROFILE%\.vscode\extensions`. It also enables
`chatgpt.historyCurrentWorkspaceOnly` if it is explicitly disabled in the default
VS Code user settings. Workspace and profile overrides can still disable it.

## Command line

Run these commands from this repository's folder:

```sh
python installer.py check
python installer.py install
python installer.py restore
```

For a custom extension location or a different VS Code profile, provide both paths:

```powershell
python installer.py install --extension "C:\path\to\openai.chatgpt-26.1021.22027-win32-x64" --settings "C:\path\to\settings.json"
```

The same options work with `check` and `restore`. Use them for Insiders, forks,
remote installations, or profiles stored outside the default location. Run the
installer on the machine where the extension files live.

## Disable or uninstall

To temporarily disable filtering, set this in VS Code settings:

```json
"chatgpt.historyCurrentWorkspaceOnly": false
```

Reopen the sidebar; restart VS Code if needed.

To uninstall, run **Restore.cmd** or `python installer.py restore`. The installer
restores the original extension files. It restores the settings file only when
that file has not changed since installation; otherwise, it preserves your edits.

Backups are stored in `.workspace-history-portable-backup` inside the patched
extension folder. Keep that directory until you restore. Restoration refuses to
overwrite extension files changed by another patch or update.

## Behavior and limitations

- Chats match **exact workspace root paths**. Chats started in subfolders or
  separate worktrees are excluded unless those folders are workspace roots.
- Multiple workspace roots are supported.
- Windows paths ignore letter case and slash direction; POSIX paths preserve case.
- With no folder open, history remains global.
- Search and archived-chat views can still show chats from other projects.
- Workspace roots and the setting are captured when the webview is created.
  Reopen the sidebar or restart after changing them.
- Extension updates can overwrite the patch. This installer does not disable
  updates, install Codex, downgrade it, or automatically patch new versions.
- Existing complete V3 patches are recognized without replacing their backups.
  Use their original V3 tools to restore those installations. Restore partial
  older patches before installing this package.

## How it works

The installer modifies four files in the installed extension: its manifest,
extension-host bundle, history-manager bundle, and sidebar subscription bundle.
It passes workspace roots to the webview and filters both history-manager rows
and the sidebar's incoming `recentThreads` subscription and top-level summaries.
The subscription filter covers rows supplied by the shared desktop host as well
as locally cached history.

Before writing, the installer validates the complete patch plan and backs up the
original files with SHA-256 hashes. If a write fails, it attempts to restore files
written during that operation. Running installation again on a complete patch
leaves the extension files unchanged.

## Tests

```sh
python -B test_installer.py
```

Tests cover installation, repeat installation, byte-for-byte restoration, preserving
settings comments and later edits, refusing changed extension files, and rejecting
unknown bundles before writing. The distributable was also checked against clean
copies of the supported vendor bundles: its generated JavaScript matched the
working patch, and restoration recovered the original files and settings.

## Repository contents

| File | Purpose |
| --- | --- |
| `installer.py` | Compatibility checks, installation, backups, and restoration |
| `transforms.py` | Exact transformations for the supported extension build |
| `Check.cmd` | Windows launcher for read-only compatibility checks |
| `Install.cmd` | Windows installation launcher |
| `Restore.cmd` | Windows restoration launcher |
| `test_installer.py` | Installer lifecycle tests |

This repository contains patch tools and replacement fragments, not full vendor
bundles, chat transcripts, credentials, or machine-specific configuration.
