"""
Application Settings
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Database
    database_url: str = "sqlite:///./etf_trader.db"
    
    # Trading Configuration
    trading_enabled: bool = False
    max_position_size: float = 10000.0
    stop_loss_percentage: float = 5.0
    take_profit_percentage: float = 10.0
    
    # API Keys
    broker_api_key: Optional[str] = None
    broker_secret_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/etf_trader.log"
    
    # Notification
    enable_notifications: bool = False
    slack_webhook_url: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    
    # Trading Schedule
    market_open_time: str = "09:00"
    market_close_time: str = "15:30"
    trading_timezone: str = "Asia/Seoul"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False 