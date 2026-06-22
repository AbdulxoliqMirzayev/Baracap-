import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "baracap_backend"
STATIC_DIR = BACKEND_DIR / "app" / "static"
DEFAULT_POSTGRES_URL = "postgresql+asyncpg://postgres:password@localhost:5432/baracap_db"


def normalize_origin(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("//"):
        return f"https:{value}"
    return f"https://{value}"


def is_local_origin(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.hostname in {"127.0.0.1", "localhost", "0.0.0.0"}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def find_open_port(start: int = 8000) -> int:
    port = start
    while True:
        if is_local_port_available(port):
            return port
        port += 1


def is_local_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def configure_environment(port: int) -> None:
    root_env = load_env_file(ROOT / ".env")
    backend_env = load_env_file(BACKEND_DIR / ".env")
    env_values = {**backend_env, **root_env}

    for key, value in env_values.items():
        os.environ.setdefault(key, value)

    env_db_url = os.environ.get("DATABASE_URL", "")
    use_postgres = os.environ.get("BARACAP_USE_POSTGRES") == "1"
    if not env_db_url or (env_db_url == DEFAULT_POSTGRES_URL and not use_postgres):
        db_path = (BACKEND_DIR / "baracap_dev.db").resolve().as_posix()
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

    os.environ.setdefault("AUTO_CREATE_TABLES", "true")
    os.environ.setdefault("DEV_AUTH_ENABLED", "true")
    os.environ.setdefault("JWT_SECRET", "baracap_local_dev_secret_change_for_prod")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    configured_frontend = normalize_origin(os.environ.get("FRONTEND_URL", ""))
    deployment_origin = (
        normalize_origin(os.environ.get("PUBLIC_DOMAIN", ""))
        or normalize_origin(os.environ.get("CUSTOM_DOMAIN", ""))
        or normalize_origin(os.environ.get("RAILWAY_PUBLIC_DOMAIN", ""))
        or normalize_origin(os.environ.get("RAILWAY_STATIC_URL", ""))
    )
    local_origin = f"http://127.0.0.1:{port}"
    if deployment_origin:
        public_origin = deployment_origin
    elif configured_frontend and not is_local_origin(configured_frontend):
        public_origin = configured_frontend
    else:
        public_origin = local_origin

    if deployment_origin and (not configured_frontend or is_local_origin(configured_frontend)):
        os.environ["FRONTEND_URL"] = public_origin
    elif configured_frontend and is_local_origin(configured_frontend):
        os.environ["FRONTEND_URL"] = public_origin
    else:
        os.environ.setdefault("FRONTEND_URL", public_origin)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "baracap-dev-server.js").write_text(
        "\n".join(
            [
                f"window.BARACAP_SERVER_ORIGIN = '{public_origin}';",
                f"window.BARACAP_API_BASE = '{public_origin}/api';",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    env_values = {
        **load_env_file(BACKEND_DIR / ".env"),
        **load_env_file(ROOT / ".env"),
    }
    requested_port = int(os.environ.get("PORT") or env_values.get("PORT") or "0")
    if requested_port and is_local_port_available(requested_port):
        port = requested_port
    else:
        port = find_open_port(requested_port or 8000)
    configure_environment(port)
    host = os.environ.get("HOST") or os.environ.get("APP_HOST") or "0.0.0.0"

    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)

    import uvicorn

    print(f"BARACAP running at http://127.0.0.1:{port}", flush=True)
    print(f"API docs: http://127.0.0.1:{port}/docs", flush=True)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
