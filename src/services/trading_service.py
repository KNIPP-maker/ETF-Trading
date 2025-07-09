"""
Trading Service for ETF Auto Trader
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger

from models.etf import Position, Trade, Portfolio
from services.data_service import DataService
from config.settings import Settings


class TradingService:
    """트레이딩 서비스"""
    
    def __init__(self):
        self.settings = Settings()
        self.data_service = DataService()
        self.positions: Dict[str, Position] = {}
        self.cash_balance = 100000.0  # 초기 자본금
        self.trades: List[Trade] = []
        self.is_initialized = False
    
    async def initialize(self):
        """서비스 초기화"""
        logger.info("Trading Service 초기화 중...")
        
        # 데이터 서비스 초기화
        await self.data_service.initialize()
        
        # 포지션 로드 (실제로는 데이터베이스에서 로드)
        await self.load_positions()
        
        self.is_initialized = True
        logger.info("Trading Service 초기화 완료")
    
    async def cleanup(self):
        """서비스 정리"""
        logger.info("Trading Service 정리 중...")
        # 필요한 정리 작업 수행
        logger.info("Trading Service 정리 완료")
    
    async def load_positions(self):
        """포지션 로드 (데이터베이스에서)"""
        # 실제 구현에서는 데이터베이스에서 로드
        logger.info("포지션 로드 완료")
    
    async def get_portfolio(self) -> Portfolio:
        """포트폴리오 정보 조회"""
        if not self.is_initialized:
            return Portfolio(
                total_value=self.cash_balance,
                cash_balance=self.cash_balance,
                positions=[],
                total_unrealized_pnl=0.0,
                total_unrealized_pnl_percent=0.0
            )
        
        # 현재 가격으로 포지션 업데이트
        positions = list(self.positions.values())
        total_unrealized_pnl = 0.0
        total_position_value = 0.0
        
        for position in positions:
            current_price = await self.data_service.get_current_price(position.symbol)
            if current_price:
                position.current_price = current_price.price
                position.unrealized_pnl = (current_price.price - position.avg_price) * position.quantity
                position.unrealized_pnl_percent = (position.unrealized_pnl / (position.avg_price * position.quantity)) * 100
                
                total_unrealized_pnl += position.unrealized_pnl
                total_position_value += current_price.price * position.quantity
        
        total_value = self.cash_balance + total_position_value
        total_unrealized_pnl_percent = (total_unrealized_pnl / total_value) * 100 if total_value > 0 else 0.0
        
        return Portfolio(
            total_value=total_value,
            cash_balance=self.cash_balance,
            positions=positions,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_percent=total_unrealized_pnl_percent
        )
    
    async def execute_trade(self, symbol: str, action: str, quantity: int) -> Dict:
        """매매 실행"""
        if not self.is_initialized:
            return {"error": "Trading service not initialized"}
        
        if not await self.data_service.is_market_open():
            return {"error": "Market is closed"}
        
        try:
            # 현재 가격 조회
            current_price = await self.data_service.get_current_price(symbol)
            if not current_price:
                return {"error": f"Unable to get price for {symbol}"}
            
            price = current_price.price
            total_amount = price * quantity
            commission = total_amount * 0.001  # 0.1% 수수료
            
            if action.lower() == "buy":
                # 매수 로직
                if total_amount + commission > self.cash_balance:
                    return {"error": "Insufficient cash balance"}
                
                # 포지션 업데이트
                if symbol in self.positions:
                    # 기존 포지션에 추가
                    existing = self.positions[symbol]
                    total_quantity = existing.quantity + quantity
                    total_cost = (existing.avg_price * existing.quantity) + total_amount
                    new_avg_price = total_cost / total_quantity
                    
                    existing.quantity = total_quantity
                    existing.avg_price = new_avg_price
                    existing.updated_at = datetime.now()
                else:
                    # 새 포지션 생성
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=quantity,
                        avg_price=price,
                        current_price=price,
                        unrealized_pnl=0.0,
                        unrealized_pnl_percent=0.0
                    )
                
                self.cash_balance -= (total_amount + commission)
                
            elif action.lower() == "sell":
                # 매도 로직
                if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                    return {"error": "Insufficient position"}
                
                position = self.positions[symbol]
                position.quantity -= quantity
                
                if position.quantity == 0:
                    # 포지션 완전 매도
                    del self.positions[symbol]
                else:
                    position.updated_at = datetime.now()
                
                self.cash_balance += (total_amount - commission)
            
            else:
                return {"error": "Invalid action. Use 'buy' or 'sell'"}
            
            # 거래 기록
            trade = Trade(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                total_amount=total_amount,
                commission=commission,
                status="completed"
            )
            self.trades.append(trade)
            
            logger.info(f"거래 실행: {action} {quantity} {symbol} @ {price}")
            
            return {
                "success": True,
                "trade": trade.dict(),
                "new_cash_balance": self.cash_balance
            }
            
        except Exception as e:
            logger.error(f"거래 실행 실패: {e}")
            return {"error": f"Trade execution failed: {str(e)}"}
    
    async def check_stop_loss(self):
        """손절매 체크"""
        if not self.is_initialized:
            return
        
        for symbol, position in self.positions.items():
            current_price = await self.data_service.get_current_price(symbol)
            if current_price:
                loss_percent = ((current_price.price - position.avg_price) / position.avg_price) * 100
                
                if loss_percent <= -self.settings.stop_loss_percentage:
                    logger.warning(f"손절매 실행: {symbol}, 손실률: {loss_percent:.2f}%")
                    await self.execute_trade(symbol, "sell", position.quantity)
    
    async def check_take_profit(self):
        """익절매 체크"""
        if not self.is_initialized:
            return
        
        for symbol, position in self.positions.items():
            current_price = await self.data_service.get_current_price(symbol)
            if current_price:
                profit_percent = ((current_price.price - position.avg_price) / position.avg_price) * 100
                
                if profit_percent >= self.settings.take_profit_percentage:
                    logger.info(f"익절매 실행: {symbol}, 수익률: {profit_percent:.2f}%")
                    await self.execute_trade(symbol, "sell", position.quantity) 