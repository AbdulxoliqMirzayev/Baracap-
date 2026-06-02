import os
import socket
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "baracap_backend"
STATIC_DIR = BACKEND_DIR / "app" / "static"
DEFAULT_POSTGRES_URL = "postgresql+asyncpg://postgres:password@localhost:5432/baracap_db"


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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1


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
    public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if public_domain and "FRONTEND_URL" not in os.environ:
        os.environ["FRONTEND_URL"] = f"https://{public_domain}"
    else:
        os.environ.setdefault("FRONTEND_URL", f"http://127.0.0.1:{port}")

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "baracap-dev-server.js").write_text(
        "\n".join(
            [
                f"window.BARACAP_SERVER_ORIGIN = 'http://127.0.0.1:{port}';",
                f"window.BARACAP_API_BASE = 'http://127.0.0.1:{port}/api';",
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
    port = requested_port or find_open_port(8000)
    configure_environment(port)
    host = os.environ.get("HOST") or os.environ.get("APP_HOST") or "0.0.0.0"

    sys.path.insert(0, str(BACKEND_DIR))
    os.chdir(BACKEND_DIR)

    import uvicorn

    print(f"BARACAP running at http://127.0.0.1:{port}", flush=True)
    print(f"API docs: http://127.0.0.1:{port}/docs", flush=True)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
