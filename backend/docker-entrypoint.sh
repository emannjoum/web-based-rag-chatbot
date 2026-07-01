#!/bin/sh
set -e

python <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("MYSQL_HOST", "mysql")
port = int(os.environ.get("MYSQL_PORT", "3306"))
deadline = time.time() + 90

while time.time() < deadline:
    try:
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    print(f"MySQL is not reachable at {host}:{port}", file=sys.stderr)
    sys.exit(1)
PY

python -c "
import os
from chatbot.infrastructure.persistence.mysql.migrations import run_migrations
run_migrations(os.environ['MYSQL_URL'])
"

exec "$@"
