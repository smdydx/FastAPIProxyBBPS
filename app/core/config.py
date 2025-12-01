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
    
    _bbps_config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def get_bbps_config(cls) -> Dict[str, Any]:
        if cls._bbps_config is None:
            config_path = DATA_DIR / "bbps_urls.yaml"
            with open(config_path, "r") as f:
                cls._bbps_config = yaml.safe_load(f)
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


settings = Settings()
