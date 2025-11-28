from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict()

    debug: bool | None = False
    environment: str = "dev"
    is_autotest: bool = False
    redis_url: str = ""
    redis_user_ttl: int = 60 * 60 * 24 * 60  # 60 days
    redis_password: str = ""
    redis_host: str = ""
    redis_port: str = ""
    redis_db: int = 0

    bot_token: str | None = None
    bot_payments_token: str | None = None
    bot_webhook_url: str | None = None
    bot_webhook_path: str = "/telegram/bot"
    bot_webhook_secret: str | None = None
    notification_admin_chat_id: int = 1725617264
    admins_ids: list[int] = [1725617264]
    error_chat_id: int = 1725617264

    files_path: str = ""

    db_url: str
    echo_sql: bool = False


settings: Settings = Settings()
