import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"


class Settings:
    APP_NAME: str = "BBPS Proxy System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    CACHE_PREFIX: str = os.getenv("CACHE_PREFIX", "bbps:")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_PREFIX: str = "bbps_"
    
    BBPS_API_BASE_URL: str = os.getenv("BBPS_API_BASE_URL", "https://api.bbps.org/v1")
    BBPS_API_KEY: str = os.getenv("BBPS_API_KEY", "")
    BBPS_API_SECRET: str = os.getenv("BBPS_API_SECRET", "")
    BBPS_OU_ID: str = os.getenv("BBPS_OU_ID", "")
    BBPS_AGENT_ID: str = os.getenv("BBPS_AGENT_ID", "")
    
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    CSV_UPLOAD_DIR: Path = APP_DIR / "uploads" / "csv"
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))
    
    _bbps_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def get_bbps_config(cls) -> Dict[str, Any]:
        if cls._bbps_config is None:
            config_path = DATA_DIR / "bbps_urls.yaml"
            if config_path.exists():
                with open(config_path, "r") as f:
                    cls._bbps_config = yaml.safe_load(f)
            else:
                cls._bbps_config = {"bbps_backend_urls": {}}
        return cls._bbps_config
    
    @classmethod
    def get_category_urls(cls, category: str) -> Dict[str, str]:
        config = cls.get_bbps_config()
        return config.get("bbps_backend_urls", {}).get(category, {})
    
    @classmethod
    def get_category_base_url(cls, category: str) -> str:
        env_key = f"BBPS_{category.upper()}_BASE_URL"
        env_url = os.getenv(env_key)
        if env_url:
            return env_url
        
        urls = cls.get_category_urls(category)
        return urls.get("base_url", "")
    
    @classmethod
    def get_endpoint_template(cls, category: str, endpoint_key: str) -> str:
        urls = cls.get_category_urls(category)
        return urls.get(endpoint_key, "")
    
    @classmethod
    def get_full_url(cls, category: str, endpoint_key: str, path_params: Optional[Dict[str, str]] = None) -> str:
        base_url = cls.get_category_base_url(category)
        urls = cls.get_category_urls(category)
        endpoint = urls.get(endpoint_key, "")
        
        if path_params:
            for key, value in path_params.items():
                endpoint = endpoint.replace(f"{{{key}}}", str(value))
        
        return f"{base_url}{endpoint}"
    
    @classmethod
    def reload_config(cls) -> None:
        cls._bbps_config = None
        cls.get_bbps_config()
    
    @classmethod
    def ensure_upload_dirs(cls) -> None:
        cls.CSV_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_upload_dirs()
