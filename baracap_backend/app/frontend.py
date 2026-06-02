from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response


STATIC_DIR = Path(__file__).resolve().parent / "static"

FRONTEND_PAGES = {
    "/",
}


def render_page() -> Response:
    page_path = STATIC_DIR / "baracap-ui.html"
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Frontend page not found")
    html = page_path.read_text(encoding="utf-8")
    return Response(content=html, media_type="text/html; charset=utf-8")


def register_frontend(app: FastAPI) -> None:
    @app.get("/baracap-app.js", include_in_schema=False)
    async def frontend_script() -> Response:
        script = (STATIC_DIR / "baracap-ui.js").read_text(encoding="utf-8")
        return Response(content=script, media_type="application/javascript; charset=utf-8")

    @app.get("/baracap-ui.js", include_in_schema=False)
    async def frontend_ui_script() -> Response:
        script = (STATIC_DIR / "baracap-ui.js").read_text(encoding="utf-8")
        return Response(content=script, media_type="application/javascript; charset=utf-8")

    @app.get("/baracap-ui.css", include_in_schema=False)
    async def frontend_ui_styles() -> Response:
        styles = (STATIC_DIR / "baracap-ui.css").read_text(encoding="utf-8")
        return Response(content=styles, media_type="text/css; charset=utf-8")

    @app.get("/baracap-dev-server.js", include_in_schema=False)
    async def frontend_dev_server_script() -> Response:
        script_path = STATIC_DIR / "baracap-dev-server.js"
        script = script_path.read_text(encoding="utf-8") if script_path.exists() else ""
        return Response(content=script, media_type="application/javascript; charset=utf-8")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(status_code=204)

    for route in FRONTEND_PAGES:
        app.add_api_route(
            route,
            render_page,
            methods=["GET"],
            include_in_schema=False,
        )
