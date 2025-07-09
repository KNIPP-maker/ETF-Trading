"""
ETF Data Models
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ETF(BaseModel):
    """ETF 기본 정보"""
    symbol: str = Field(..., description="ETF 심볼")
    name: str = Field(..., description="ETF 이름")
    exchange: str = Field(..., description="거래소")
    sector: Optional[str] = Field(None, description="섹터")
    expense_ratio: Optional[float] = Field(None, description="보수율")
    aum: Optional[float] = Field(None, description="자산규모")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ETFPrice(BaseModel):
    """ETF 가격 정보"""
    symbol: str = Field(..., description="ETF 심볼")
    price: float = Field(..., description="현재 가격")
    change: float = Field(..., description="변동폭")
    change_percent: float = Field(..., description="변동률")
    volume: int = Field(..., description="거래량")
    timestamp: datetime = Field(default_factory=datetime.now)


class Position(BaseModel):
    """포지션 정보"""
    symbol: str = Field(..., description="ETF 심볼")
    quantity: int = Field(..., description="보유 수량")
    avg_price: float = Field(..., description="평균 매수가")
    current_price: float = Field(..., description="현재 가격")
    unrealized_pnl: float = Field(..., description="평가손익")
    unrealized_pnl_percent: float = Field(..., description="평가손익률")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Trade(BaseModel):
    """거래 정보"""
    id: Optional[int] = Field(None, description="거래 ID")
    symbol: str = Field(..., description="ETF 심볼")
    action: str = Field(..., description="매수/매도")
    quantity: int = Field(..., description="거래 수량")
    price: float = Field(..., description="거래 가격")
    total_amount: float = Field(..., description="총 거래 금액")
    commission: float = Field(default=0.0, description="수수료")
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="거래 상태")


class Portfolio(BaseModel):
    """포트폴리오 정보"""
    total_value: float = Field(..., description="총 포트폴리오 가치")
    cash_balance: float = Field(..., description="현금 잔고")
    positions: List[Position] = Field(default_factory=list, description="보유 포지션")
    total_unrealized_pnl: float = Field(..., description="총 평가손익")
    total_unrealized_pnl_percent: float = Field(..., description="총 평가손익률")
    updated_at: datetime = Field(default_factory=datetime.now) 