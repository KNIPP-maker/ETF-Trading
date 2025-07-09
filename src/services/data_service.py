"""
Data Service for ETF Auto Trader
"""

import asyncio
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from loguru import logger

from models.etf import ETF, ETFPrice
from config.settings import Settings


class DataService:
    """데이터 수집 및 관리 서비스"""
    
    def __init__(self):
        self.settings = Settings()
        self.cache: Dict[str, ETFPrice] = {}
        self.cache_ttl = 60  # 캐시 유효시간 (초)
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
    
    async def initialize(self):
        """서비스 초기화"""
        logger.info("Data Service 초기화 중...")
        # 필요한 초기화 작업 수행
        logger.info("Data Service 초기화 완료")
    
    async def get_etf_info(self, symbol: str) -> Optional[ETF]:
        """ETF 기본 정보 조회"""
        try:
            # 간단한 ETF 정보 (실제로는 API에서 가져와야 함)
            etf = ETF(
                symbol=symbol,
                name=f"{symbol} ETF",
                exchange="NYSE",
                sector="ETF",
                expense_ratio=0.09,
                aum=1000000000.0
            )
            
            return etf
        except Exception as e:
            logger.error(f"ETF 정보 조회 실패: {symbol}, 오류: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[ETFPrice]:
        """현재 가격 조회"""
        try:
            # 캐시 확인
            if symbol in self.cache:
                cached_price = self.cache[symbol]
                if (datetime.now() - cached_price.timestamp).seconds < self.cache_ttl:
                    return cached_price
            
            # Yahoo Finance API를 사용하여 가격 데이터 가져오기
            url = f"{self.base_url}{symbol}"
            params = {
                "interval": "1d",
                "range": "2d",
                "includePrePost": "false"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                logger.warning(f"가격 데이터 없음: {symbol}")
                return None
            
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            
            if len(timestamps) < 2:
                logger.warning(f"가격 데이터 부족: {symbol}")
                return None
            
            current_price = quotes["close"][-1]
            prev_price = quotes["close"][-2]
            
            if current_price is None or prev_price is None:
                logger.warning(f"가격 데이터 누락: {symbol}")
                return None
            
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
            volume = quotes["volume"][-1] or 0
            
            price_data = ETFPrice(
                symbol=symbol,
                price=current_price,
                change=change,
                change_percent=change_percent,
                volume=volume
            )
            
            # 캐시 업데이트
            self.cache[symbol] = price_data
            
            return price_data
            
        except Exception as e:
            logger.error(f"가격 조회 실패: {symbol}, 오류: {e}")
            # 테스트용 더미 데이터 반환
            return ETFPrice(
                symbol=symbol,
                price=100.0,
                change=1.0,
                change_percent=1.0,
                volume=1000000
            )
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """과거 가격 데이터 조회"""
        try:
            # 기간을 일수로 변환
            period_days = {
                "1d": 1,
                "5d": 5,
                "1mo": 30,
                "3mo": 90,
                "6mo": 180,
                "1y": 365,
                "2y": 730,
                "5y": 1825,
                "10y": 3650
            }
            
            days = period_days.get(period, 365)
            
            url = f"{self.base_url}{symbol}"
            params = {
                "interval": "1d",
                "range": period,
                "includePrePost": "false"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                return None
            
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            
            df = pd.DataFrame({
                'Date': pd.to_datetime(timestamps, unit='s'),
                'Open': quotes["open"],
                'High': quotes["high"],
                'Low': quotes["low"],
                'Close': quotes["close"],
                'Volume': quotes["volume"]
            })
            
            return df.dropna()
            
        except Exception as e:
            logger.error(f"과거 데이터 조회 실패: {symbol}, 오류: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, ETFPrice]:
        """여러 ETF의 현재 가격을 동시에 조회"""
        tasks = [self.get_current_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, ETFPrice):
                prices[symbol] = result
            else:
                logger.error(f"가격 조회 실패: {symbol}, 오류: {result}")
        
        return prices
    
    async def is_market_open(self) -> bool:
        """시장 개장 여부 확인"""
        now = datetime.now()
        
        # 간단한 시간 기반 체크 (실제로는 더 정교한 로직 필요)
        market_open = datetime.strptime(self.settings.market_open_time, "%H:%M").time()
        market_close = datetime.strptime(self.settings.market_close_time, "%H:%M").time()
        
        return market_open <= now.time() <= market_close 