"""Generate machine-local MCP config; optionally install the downloaded scoped key."""
import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
python = root / '.venv/bin/python'
if not python.exists():
    raise SystemExit('Сначала создайте plugin/.venv и установите plugin/requirements.txt.')
if len(sys.argv) > 1:
    data = json.loads(Path(sys.argv[1]).expanduser().read_text())
    # Validate before copying, without printing secrets.
    sys.path.insert(0, str(root / 'scripts'))
    import server
    os.environ['SERVICE_SYSTEM_CONNECTION'] = str(Path(sys.argv[1]).expanduser())
    server.read_connection()
    target = root / 'connection.json'
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(data, handle)
config = {'mcpServers': {'service-system': {'command': str(python), 'args': [str(root / 'scripts/server.py')], 'cwd': str(root), 'tool_timeout_sec': 45}}}
(root / '.mcp.json').write_text(json.dumps(config, indent=2))
print('Локальная конфигурация плагина готова. Ключ подключения в вывод не включён.')
