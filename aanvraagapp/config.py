from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalMailSettings(BaseModel):
    provider: Literal["local"]
    username: str
    password: str
    from_email: str
    port: int
    server: str
    from_name: str
    starttls: int
    ssl_tls: int


# TODO Implement this.
class DeploymentMailSettings(BaseModel):
    provider: Literal["deployment"]
    username: str
    password: str
    from_email: str
    port: int
    server: str
    from_name: str
    starttls: int
    ssl_tls: int


MailSettings = Annotated[LocalMailSettings | DeploymentMailSettings, Discriminator("provider")]


class LocalDatabaseSettings(BaseModel):
    provider: Literal["local"]
    host: str
    port: str
    db: str
    user: str
    password: str

    @property
    def database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


# TODO: Implement this.
class DeploymentDatabaseSettings(BaseModel):
    provider: Literal["deployment"]
    host: str
    port: str
    db: str
    user: str
    password: str

    @property
    def database_uri(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


DatabaseSettings = Annotated[DeploymentDatabaseSettings | LocalDatabaseSettings, Discriminator("provider")]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    # Mail
    mail: MailSettings

    # Database
    database: DatabaseSettings

    # Google
    gemini_api_key: str

    # Auth
    session_cookie_name: str = "session_token"
    session_expiry_hours: int = 24 * 14
    cors_allowed_origin: str

    @property
    def session_expiry_seconds(self):
        return self.session_expiry_hours * 3600

    # Redis
    redis_host: str
    redis_port: int
    redis_db: int

    @property
    def redis_uri(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"




settings = Settings()  # type: ignore[reportCallIssue]
