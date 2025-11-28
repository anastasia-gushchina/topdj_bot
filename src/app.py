import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

from src.bot_main import bot_startup, bot_shutdown, webhook_router, dp as bot_dp
from src.bot.payment_result import payment_result_router
from src.bot.purchase_pack import purchase_router
from src.bot.admin_states import admin_router
from src.settings import settings


VERSION = "0.1"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot_startup()
    yield
    await bot_shutdown()


app_cfg = {}
if not settings.debug:
    app_cfg["openapi_url"] = None
app = FastAPI(title="Telegram bot service", version=VERSION, lifespan=lifespan, **app_cfg)

bot_dp.include_router(payment_result_router)
bot_dp.include_router(purchase_router)
bot_dp.include_router(admin_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if settings.debug:

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"] = openapi_schema.get("components", {})

    sec_schemes = openapi_schema["components"].get("securitySchemes", {})
    sec_schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema["components"]["securitySchemes"] = sec_schemes
    security = openapi_schema.get("security", [])
    security.append({"bearerAuth": []})
    openapi_schema["security"] = security
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(webhook_router)


@app.get("/liveness", include_in_schema=False)
async def liveness() -> str:
    return "OK"
