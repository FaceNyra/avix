from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
	token: str

	postgres_db: str
	postgres_user: str
	postgres_password: str
	postgres_port: int
	postgres_host: str

	redis_host: str
	redis_port: int
	redis_password: str
	redis_db: int

	@computed_field
	@property
	def database_url(self) -> str:
		return (
			f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
			f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
		)

	@computed_field
	@property
	def redis_url(self) -> str:
		if self.redis_password:
			return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
		return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

	model_config = SettingsConfigDict(
		env_file=BASE_DIR / ".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)


settings = Settings()
