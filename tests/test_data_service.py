"""
Data Service Tests
"""

import pytest
import asyncio
from src.services.data_service import DataService


@pytest.fixture
def data_service():
    return DataService()


@pytest.mark.asyncio
async def test_initialize(data_service):
    """초기화 테스트"""
    await data_service.initialize()
    # 초기화가 성공적으로 완료되었는지 확인


@pytest.mark.asyncio
async def test_get_etf_info(data_service):
    """ETF 정보 조회 테스트"""
    etf_info = await data_service.get_etf_info("SPY")
    assert etf_info is not None
    assert etf_info.symbol == "SPY"


@pytest.mark.asyncio
async def test_get_current_price(data_service):
    """현재 가격 조회 테스트"""
    price = await data_service.get_current_price("SPY")
    assert price is not None
    assert price.symbol == "SPY"
    assert price.price > 0


@pytest.mark.asyncio
async def test_get_multiple_prices(data_service):
    """여러 가격 조회 테스트"""
    symbols = ["SPY", "QQQ", "IWM"]
    prices = await data_service.get_multiple_prices(symbols)
    
    assert len(prices) > 0
    for symbol in prices:
        assert prices[symbol].price > 0 