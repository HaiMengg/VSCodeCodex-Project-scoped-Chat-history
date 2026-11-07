"""Portable installer for the verified Codex workspace-history patch (Python 3)."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from transforms import VERSION, SETTING, digest
from transforms import META_OLD, META_NEW, MATCH, UI_REPLACEMENTS
from transforms import HELPER, RECENT, RECENT_NEW, TOP, TOP_NEW

FILES = ['out/extension.js', 'package.json', 'webview/assets/src-622b307a9baf.js',
         'webview/assets/app-server-manager-signals-3484150562ce.js']
BACKUP_DIR = '.workspace-history-portable-backup'


def locate(explicit):
    if explicit:
        return explicit.expanduser().resolve()
    base = Path(os.environ.get('VSCODE_EXTENSIONS', str(Path.home() / '.vscode/extensions')))
    candidates = []
    for path in base.glob('openai.chatgpt-*'):
        manifest = path / 'package.json'
        if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8'))['version'] == VERSION:
            candidates.append(path)
    if len(candidates) != 1:
        raise ValueError(f'Expected one Codex {VERSION} installation; found {len(candidates)}. Use --extension PATH.')
    return candidates[0]


def settings_path():
    if sys.platform == 'win32':
        return Path(os.environ['APPDATA']) / 'Code/User/settings.json'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/Code/User/settings.json'
    return Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'Code/User/settings.json'


def prepare_settings(path):
    if not path.exists():
        return None
    data = path.read_bytes()
    text = data.decode('utf-8-sig')
    pattern = r'(?m)^(\s*"chatgpt\.historyCurrentWorkspaceOnly"\s*:\s*)(true|false)\b'
    matches = list(re.finditer(pattern, text))
    if len(matches) > 1:
        raise ValueError(f'Duplicate filter settings in {path}; resolve them before installing.')
    if not matches or matches[0].group(2) == 'true':
        return None
    match = matches[0]
    text = text[:match.start(2)] + 'true' + text[match.end(2):]
    encoding = 'utf-8-sig' if data.startswith(b'\xef\xbb\xbf') else 'utf-8'
    return path, data, text.encode(encoding)


def plan(root):
    current = [(root / name).read_bytes() for name in FILES]
    package = json.loads(current[1])
    if package.get('publisher') != 'openai' or package.get('name') != 'chatgpt' or package.get('version') != VERSION:
        raise ValueError(f'Only OpenAI Codex {VERSION} is supported; no changes made.')
    source, ui, signals = [current[index].decode('utf-8') for index in [0, 2, 3]]
    already = META_NEW in source and MATCH in ui and HELPER in signals and RECENT_NEW in signals and TOP_NEW in signals
    if already:
        return current, None
    if any(marker in source + ui + signals for marker in
           ['codex-workspace-history-patch-v1', 'codex-workspace-history-patch-v2', 'codexWorkspaceHistoryVisible']):
        raise ValueError('Partial/older patch detected. Restore it with its original tools before using this installer.')
    for old, new in [(META_OLD, META_NEW)]:
        if source.count(old) != 1:
            raise ValueError('Extension bundle differs from supported build; no changes made.')
        source = source.replace(old, new)
    for old, new in UI_REPLACEMENTS:
        if ui.count(old) != 1:
            raise ValueError('History bundle differs from supported build; no changes made.')
        ui = ui.replace(old, new)
    for old, new in [(RECENT, RECENT_NEW), (TOP, TOP_NEW)]:
        if signals.count(old) != 1:
            raise ValueError('Sidebar bundle differs from supported build; no changes made.')
        signals = signals.replace(old, new)
    signals += '\n' + HELPER
    package['contributes']['configuration']['properties'][SETTING] = {
        'type': 'boolean', 'default': True, 'scope': 'window',
        'description': 'Local patch: show Codex sidebar history matching the open workspace folders.'
    }
    return current, [source.encode('utf-8'),
                     (json.dumps(package, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
                     ui.encode('utf-8'), signals.encode('utf-8')]


def restore(root):
    directory = root / BACKUP_DIR
    state = json.loads((directory / 'state.json').read_text(encoding='utf-8'))
    targets = []
    for index, name in enumerate(FILES):
        entry = state['files'][index]
        if entry['name'] != name:
            raise ValueError('Unexpected backup manifest.')
        path = root / name
        data = path.read_bytes()
        original = (directory / f'{index}.original').read_bytes()
        if digest(original) != entry['original'] or digest(data) not in [entry['original'], entry['patched']]:
            raise ValueError(f'File changed since installation: {path}. Refusing to overwrite.')
        targets.append((path, data, original))
    setting = state.get('settings')
    if setting:
        path = Path(setting['path'])
        if path.exists() and digest(path.read_bytes()) == setting['patched']:
            original = (directory / 'settings.original').read_bytes()
            if digest(original) != setting['original']:
                raise ValueError('Settings backup checksum mismatch.')
            targets.append((path, path.read_bytes(), original))
        else:
            print('Settings changed since installation; preserving current settings.')
    write_transaction(targets)
    print('Restored original extension files. Reopen the Codex sidebar; restart VS Code if needed.')


def write_transaction(targets):
    for path, expected, replacement in targets:
        if path.read_bytes() != expected:
            raise ValueError(f'File changed during preparation: {path}')
    written = []
    try:
        for path, expected, replacement in targets:
            written.append((path, expected))
            path.write_bytes(replacement)
    except Exception:
        for path, data in reversed(written):
            path.write_bytes(data)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'install', 'restore'], nargs='?', default='check')
    parser.add_argument('--extension', type=Path, help='Codex extension folder for custom/remote/Insiders installations')
    parser.add_argument('--settings', type=Path, help='VS Code profile settings.json; defaults to standard VS Code user settings')
    args = parser.parse_args()
    root = locate(args.extension)
    print('Extension:', root)
    if args.action == 'restore':
        restore(root)
        return
    current, replacements = plan(root)
    settings = prepare_settings(args.settings or settings_path())
    print('Patch:', 'already installed' if replacements is None else 'compatible')
    print('Filter:', 'explicitly disabled; install will enable it' if settings else 'enabled by default or user setting')
    if args.action == 'check':
        print('Read-only check complete.')
        return
    if replacements is None:
        if settings:
            # Preserve existing patch ownership; do not claim backups from another installer.
            path, original, replacement = settings
            write_transaction([settings])
            print('Enabled filter setting. Existing patch and its backup files left intact.')
        else:
            print('Nothing to change.')
        return
    directory = root / BACKUP_DIR
    state_path = directory / 'state.json'
    if state_path.exists():
        old = json.loads(state_path.read_text())
        if any(digest(data) != entry['original'] for data, entry in zip(current, old['files'])):
            raise ValueError('Existing backup belongs to different files; refusing to replace it.')
    directory.mkdir(exist_ok=True)
    state = {'version': 1, 'extensionVersion': VERSION, 'files': []}
    targets = []
    for index, (name, original, replacement) in enumerate(zip(FILES, current, replacements)):
        (directory / f'{index}.original').write_bytes(original)
        state['files'].append({'name': name, 'original': digest(original), 'patched': digest(replacement)})
        targets.append((root / name, original, replacement))
    if settings:
        path, original, replacement = settings
        (directory / 'settings.original').write_bytes(original)
        state['settings'] = {'path': str(path.resolve()), 'original': digest(original), 'patched': digest(replacement)}
        targets.append(settings)
    state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    write_transaction(targets)
    print('Installed with backups. Filter enabled.')
    print('Try reopening the Codex sidebar. If it still shows old history, fully restart VS Code.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
