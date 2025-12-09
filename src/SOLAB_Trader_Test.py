import sys
import asyncio
import os
import time
import traceback
import winsound
import random
import math
from datetime import datetime
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLineEdit, QSplitter, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPalette
from qasync import QEventLoop
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.kiwoom_client import KiwoomRESTClient
from services.trade_logger import TradeLogger

load_dotenv()

# =================================================================================
# ⚙️ [설정] 기관급 설정을 위한 파라미터
# =================================================================================
IS_SIMULATION = False
TOTAL_CAPITAL = 10_000_000_000  # 100억 세팅
# [중요] 선물/지수 코드 설정 (HTS에서 확인 후 변경 필수)
# 2025년 12월물 예시 코드입니다. 실제 코드로 변경하세요.
INDEX_CODE = "200"        # KOSPI 200 지수
FUTURES_CODE = "101WC000" # KOSPI 200 선물 (최근월물 코드)
# [디자인 상수]
COLOR_BG        = "#1e1e1e"
COLOR_FG        = "#ffffff"
COLOR_PANEL     = "#2d2d2d"
COLOR_BUY       = "#d32f2f"
COLOR_SELL      = "#303f9f"
COLOR_PROFIT    = "#ff3333"
COLOR_LOSS      = "#3333ff"
COLOR_SIGNAL_BG = "#333"

FONT_NUM        = QFont("Consolas", 12, QFont.Bold)
FONT_TITLE      = QFont("Malgun Gothic", 12, QFont.Bold)
FONT_SIGNAL     = QFont("Malgun Gothic", 18, QFont.Bold)

def exception_hook(exctype, value, tb):
    print("".join(traceback.format_exception(exctype, value, tb)))
sys.excepthook = exception_hook
# ==========================================================================
# [전략 엔진] Basis 기반 차익거래/헤징 판독기
# ==========================================================================
class InternalSignalEngine:
    def __init__(self):
        # [설정] Basis 임계값 튜닝
        # 0.5 이상이면 강력한 매수 신호(콘탱고)
        # -0.5 이하이면 강력한 매도 신호(백워데이션)
        self.STRONG_BUY = 0.30
        self.WEAK_BUY = 0.10
        self.WEAK_SELL = -0.10
        self.STRONG_SELL = -0.30

    def analyze(self, basis):
        """
        Basis를 분석하여 매매 신호와 UI 스타일을 반환
        """
        # 1. 레버리지 진입 구간 (상승장 예상)
        if basis >= self.STRONG_BUY:
            return {
                "action": "STRONG_BUY_LEV",
                "msg": f"🚀 [강력 매수] 선물 주도 대상승 (Basis {basis:.2f})",
                "color": "#ff0000", "border": "#ff0000", "bg": "#330000"
            }
        elif basis >= self.WEAK_BUY:
            return {
                "action": "WEAK_BUY_LEV",
                "msg": f"📈 [매수 관점] 약한 콘탱고 (Basis {basis:.2f})",
                "color": "#ffaaaa", "border": "#ff5555", "bg": "#221111"
            }
        
        # 2. 인버스 진입 구간 (하락장 예상)
        elif basis <= self.STRONG_SELL:
            return {
                "action": "STRONG_BUY_INV",
                "msg": f"📉 [강력 하락] 선물 투매 발생 (Basis {basis:.2f})",
                "color": "#00ffff", "border": "#00ffff", "bg": "#003333"
            }
        elif basis <= self.WEAK_SELL:
            return {
                "action": "WEAK_BUY_INV",
                "msg": f"📉 [하락 관점] 약한 백워데이션 (Basis {basis:.2f})",
                "color": "#aaaaff", "border": "#5555ff", "bg": "#111122"
            }
            
        # 3. 중립 구간
        else:
            return {
                "action": "HOLD",
                "msg": f"👀 [관망] 방향성 탐색 중 (Basis {basis:.2f})",
                "color": "#888", "border": "#444", "bg": "#1e1e1e"
            }

# ==========================================================================
# [UI 컴포넌트]
# ==========================================================================
class OrderPanel(QWidget):
    def __init__(self, main_win, code, name):
        super().__init__(main_win)
        self.main_win = main_win
        self.code = code
        self.name = name
        self.holding_qty = 0
        self.avg_price = 0
        self.curr_price = 0
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2,2,2,2); layout.setSpacing(5)

       

        # 헤더
        header = QFrame(); header.setStyleSheet(f"background-color: {COLOR_PANEL}; border-radius: 5px;")
        h_layout = QHBoxLayout(header)
        lbl_name = QLabel(f"{self.name}"); lbl_name.setFont(FONT_TITLE); lbl_name.setStyleSheet(f"color: {COLOR_FG};"); lbl_name.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(lbl_name); layout.addWidget(header)

        # 정보창
        info = QFrame(); info.setStyleSheet(f"background-color: {COLOR_BG}; border: 1px solid #444;")
        i_layout = QVBoxLayout(info)
        row1 = QHBoxLayout(); self.lbl_qty = QLabel("0주"); self.lbl_val = QLabel("0원")
        for l in [self.lbl_qty, self.lbl_val]: l.setFont(FONT_NUM); l.setStyleSheet("color: #ddd;"); row1.addWidget(l)
        row2 = QHBoxLayout(); self.lbl_pnl = QLabel("0"); self.lbl_rate = QLabel("0.00%")
        for l in [self.lbl_pnl, self.lbl_rate]: l.setFont(FONT_NUM); row2.addWidget(l)
        i_layout.addLayout(row1); i_layout.addLayout(row2); layout.addWidget(info)

        # 호가창
        self.table = QTableWidget(); self.table.setColumnCount(3); self.table.horizontalHeader().hide(); self.table.verticalHeader().hide(); self.table.setRowCount(15)
        self.table.setFont(FONT_NUM); self.table.setStyleSheet(f"background-color: {COLOR_BG}; gridline-color: #333; color: white;")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_ui(self, price, holding, avg):
        self.curr_price = price
        self.holding_qty = holding
        self.avg_price = avg
        val_amt = holding * price
        self.lbl_qty.setText(f"{holding:,}주"); self.lbl_val.setText(f"{int(val_amt):,}원")
        pnl = 0; rate = 0.0
        if holding > 0:
            pnl = (price - avg) * holding
            rate = (price - avg) / avg * 100
        color = COLOR_PROFIT if pnl > 0 else COLOR_LOSS if pnl < 0 else "#ccc"
        self.lbl_pnl.setText(f"{int(pnl):,}원"); self.lbl_pnl.setStyleSheet(f"color: {color};")
        self.lbl_rate.setText(f"{rate:.2f}%"); self.lbl_rate.setStyleSheet(f"color: {color};")
        self.draw_orderbook()

    def draw_orderbook(self):
        if self.curr_price == 0: return
        start_price = self.curr_price + (7 * 5)
        for i in range(15):
            price = start_price - (i * 5)
            item_ask = QTableWidgetItem(); item_price = QTableWidgetItem(f"{price:,}"); item_bid = QTableWidgetItem()
            item_price.setTextAlignment(Qt.AlignCenter)
            if i < 7: item_ask.setBackground(QColor(0,0,255,30)); item_price.setForeground(QColor("#8888ff"))
            else: item_bid.setBackground(QColor(255,0,0,30)); item_price.setForeground(QColor("#ff8888"))
            if price == self.curr_price: item_price.setForeground(QColor("white")); item_price.setBackground(QColor("#555")); item_price.setFont(FONT_NUM)
            self.table.setItem(i, 0, item_ask); self.table.setItem(i, 1, item_price); self.table.setItem(i, 2, item_bid)
# ==========================================================================
# [메인 트레이더]
# ==========================================================================
class SolabTraderV13(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = KiwoomRESTClient()
        self.logger = TradeLogger()
        self.engine = InternalSignalEngine()

       

        self.total_capital = TOTAL_CAPITAL
        self.current_cash = TOTAL_CAPITAL
        self.total_realized_profit = 0

       

        # [중요] 시장 데이터 컨테이너
        self.market_data = {

            'kospi200': 0.0,

            'futures': 0.0,

            'lev_price': 0,

            'inv_price': 0,

            'basis': 0.0
        }
        self.last_signal_time = 0
      
        self.initUI()
        QTimer.singleShot(1000, self.async_init)

    def initUI(self):
        self.setWindowTitle("SOLAB Trader - Institutional Strategy Edition")
        self.setGeometry(100, 100, 1100, 950)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_FG};")

        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)


        # Top Info
        top_frame = QFrame(); top_frame.setStyleSheet("background-color: #222; border-bottom: 2px solid #555;")
        t_layout = QHBoxLayout(top_frame)
        
        # ▼▼▼ 여기 1: '운용자산' -> '잔고' 로 수정 ▼▼▼
        self.lbl_cap = QLabel(f"잔고: {self.total_capital:,}원"); self.lbl_cap.setFont(FONT_TITLE); t_layout.addWidget(self.lbl_cap)
        
        self.lbl_cash = QLabel(f"가용현금: {self.total_capital:,}원"); self.lbl_cash.setFont(FONT_TITLE); self.lbl_cash.setStyleSheet("color: #ffff00;"); t_layout.addWidget(self.lbl_cash)
        
        # ▼▼▼ 여기 2: 'Basis' -> 'Real Basis' 로 수정 ▼▼▼
        self.lbl_basis_info = QLabel("Real Basis: 0.00"); self.lbl_basis_info.setFont(FONT_TITLE); self.lbl_basis_info.setStyleSheet("color: #00ff00;"); t_layout.addWidget(self.lbl_basis_info)
        
        layout.addWidget(top_frame)

        # Signal Display
        self.signal_frame = QFrame(); self.signal_frame.setStyleSheet(f"background-color: {COLOR_SIGNAL_BG}; border-radius: 5px; border: 2px solid #555;")
        s_layout = QVBoxLayout(self.signal_frame)
        self.lbl_signal = QLabel("SYSTEM READY"); self.lbl_signal.setAlignment(Qt.AlignCenter); self.lbl_signal.setFont(FONT_SIGNAL); self.lbl_signal.setStyleSheet(f"color: #aaa;")
        s_layout.addWidget(self.lbl_signal)
        layout.addWidget(self.signal_frame)

        # Order Panels
        splitter = QSplitter(Qt.Horizontal)
        self.panel_lev = OrderPanel(self, "122630", "KODEX 레버리지")
        self.panel_inv = OrderPanel(self, "252670", "KODEX 선물인버스2X")
        splitter.addWidget(self.panel_lev); splitter.addWidget(self.panel_inv)
        layout.addWidget(splitter, 1)

        # Key Guide & Log
        bot_frame = QFrame(); bot_layout = QVBoxLayout(bot_frame)
        lbl_guide = QLabel("🔴 F1/F2: 레버리지 매수   🔵 F3/F4: 인버스 매수   🟢 F5/Space: 전량 청산")
        lbl_guide.setAlignment(Qt.AlignCenter); lbl_guide.setFont(QFont("Malgun Gothic", 12, QFont.Bold))
        lbl_guide.setStyleSheet("color: #fff; background-color: #444; padding: 10px; border-radius: 5px;")
        bot_layout.addWidget(lbl_guide)
        self.log_view = QTableWidget(0, 1); self.log_view.horizontalHeader().hide(); self.log_view.verticalHeader().hide(); self.log_view.horizontalHeader().setStretchLastSection(True); self.log_view.setStyleSheet("background-color: #111; color: #00ff00; font-family: Consolas;")
        bot_layout.addWidget(self.log_view); layout.addWidget(bot_frame)

        self.timer = QTimer(self); self.timer.timeout.connect(self.core_loop); self.timer.start(200)

    # ------------------------------------------------------------------
    # [핵심] 4대 데이터 동시 수신 및 Basis 계산
    # ------------------------------------------------------------------
    def _safe_float(self, val):
        if not val: return 0.0
        try: return float(str(val).replace(',', '').replace('+', '').replace('=', '').strip())
        except: return 0.0

    def _safe_int(self, val):
        return int(self._safe_float(val))
    async def _fetch_real_data(self):
        try:
            # -----------------------------------------------------------
            # 1. [유지] 실계좌 잔고 및 보유수량 조회 (기존 로직 동일)
            # -----------------------------------------------------------
            balance_data = await self.kiwoom.get_account_balance()
            if balance_data:
                # 자산 파싱
                raw_total = balance_data.get('tot_asst_amt') or balance_data.get('tot_eval_amt') or "0"
                raw_cash = balance_data.get('dbst_bal') or balance_data.get('dnca_tot_amt') or "0"
                
                # 시뮬레이션이 아닐 때만 실제 잔고 적용
                if not IS_SIMULATION:
                    self.total_capital = self._safe_int(raw_total)
                    self.current_cash = self._safe_int(raw_cash)

                # 보유수량 파싱
                stock_list = balance_data.get('day_bal_rt', [])
                if not stock_list and 'output' in balance_data:
                    stock_list = balance_data['output'].get('day_bal_rt', [])

                # 잔고 초기화 후 갱신
                self.panel_lev.holding_qty = 0
                self.panel_inv.holding_qty = 0

                for stock in stock_list:
                    code = str(stock.get('stk_cd', '')).strip().replace('A', '')
                    qty = self._safe_int(stock.get('rmnd_qty', 0))
                    avg = self._safe_int(stock.get('buy_uv', 0))
                    
                    if code == self.panel_lev.code:
                        self.panel_lev.holding_qty = qty
                        self.panel_lev.avg_price = avg
                    elif code == self.panel_inv.code:
                        self.panel_inv.holding_qty = qty
                        self.panel_inv.avg_price = avg

            # -----------------------------------------------------------
            # 2. [수정] 선물/지수 제외하고 'ETF 2종'만 시세 요청
            # -----------------------------------------------------------
            tasks = [
                self.kiwoom.get_current_price(self.panel_lev.code), # 레버리지
                self.kiwoom.get_current_price(self.panel_inv.code)  # 인버스
            ]
            
            # 병렬 요청 실행
            res_lev, res_inv = await asyncio.gather(*tasks, return_exceptions=True)

            # 가격 파싱 함수 (내부 헬퍼)
            def parse_price(res):
                if not isinstance(res, dict): return 0
                data = res.get('output', res)
                # 호가/체결가 등 가능한 키값 모두 검사
                candidates = ['stck_prpr', 'cur_prc', 'now_prc', 'sel_fpr_bid', 'buy_fpr_bid']
                for key in candidates:
                    if key in data:
                        val = self._safe_float(data[key])
                        if abs(val) > 0: return abs(val)
                return 0

            # ETF 가격 업데이트
            lev_p = parse_price(res_lev)
            inv_p = parse_price(res_inv)

            if lev_p > 0: self.market_data['lev_price'] = int(lev_p)
            if inv_p > 0: self.market_data['inv_price'] = int(inv_p)

            # -----------------------------------------------------------
            # 3. [전략 대체] Basis 계산 불가 -> ETF 가격 모니터링 모드
            # -----------------------------------------------------------
            if lev_p > 0 and inv_p > 0:
                # 선물 데이터가 없으므로 Real Basis는 0.00으로 처리
                real_basis = 0.00
                self.market_data['basis'] = real_basis
                
                # [로그] 데이터 수신 확인용
                print(f"-> [시세수신] 레버리지: {int(lev_p):,}원 | 인버스: {int(inv_p):,}원")
                
                # 엔진에는 0.0을 던져서 'HOLD(관망)' 상태로 유지 (자동매매 오작동 방지)
                decision = self.engine.analyze(0.0)
                
                # 단, UI 신호창에는 '수동 매매 모드'임을 표시
                decision['msg'] = "⚡ [ETF 모드] F키로 수동 매매하세요"
                decision['color'] = "#ffff00"
                decision['border'] = "yellow"
                
                self._update_signal_ui(decision)
                
            else:
                # 데이터가 아직 안 들어왔을 때
                print(f"⚠️ [대기중] 레버리지: {lev_p} / 인버스: {inv_p}")
                decision = self.engine.analyze(0.0)
                self._update_signal_ui(decision)

            # -----------------------------------------------------------
            # 4. UI 최종 갱신
            # -----------------------------------------------------------
            # 잔고/예수금 표시
            self.lbl_cap.setText(f"잔고: {self.total_capital:,}원")
            self.lbl_cash.setText(f"가용현금: {self.current_cash:,}원")
            
            # Basis는 0.00으로 고정 표시
            self.lbl_basis_info.setText(f"Real Basis: 0.00")
            self.lbl_basis_info.setStyleSheet("color: #888888;") # 회색 처리
            
            # 패널(호가창/수익률) 업데이트
            self.panel_lev.update_ui(self.market_data['lev_price'], self.panel_lev.holding_qty, self.panel_lev.avg_price)
            self.panel_inv.update_ui(self.market_data['inv_price'], self.panel_inv.holding_qty, self.panel_inv.avg_price)

        except Exception as e:
            print(f"!!! 데이터 처리 에러: {e}")
            print(traceback.format_exc())
            
            # 2. [기관급 데이터 수신] 4개 시세 동시 요청
            # - ETF: 122630, 252670
            # - INDEX: KOSPI 200 (200)
            # - FUTURES: KOSPI 200 선물 (101...)
          

            tasks = [
                self.kiwoom.get_current_price(self.panel_lev.code),
                self.kiwoom.get_current_price(self.panel_inv.code),
                self.kiwoom.get_current_price(INDEX_CODE),   # 지수 요청
                self.kiwoom.get_current_price(FUTURES_CODE)  # 선물 요청
            ]

           

            # 병렬 요청으로 지연시간(Latency) 최소화
            res_lev, res_inv, res_idx, res_fut = await asyncio.gather(*tasks, return_exceptions=True)

            # 가격 파싱 헬퍼
            def parse_price(res, is_index=False):
                if not isinstance(res, dict): return 0
                data = res.get('output', res)

               

                # 지수/선물은 키값이 다를 수 있음 (curr_prc, clpr, now_prc 등)
                candidates = ['stck_prpr', 'cur_prc', 'now_prc', 'clpr', 'sel_fpr_bid', 'buy_fpr_bid']
                for key in candidates:
                    if key in data:
                        val = self._safe_float(data[key])
                        if abs(val) > 0: return abs(val) # 무조건 양수 반환
                return 0


            # 데이터 업데이트

            lev_p = parse_price(res_lev)
            inv_p = parse_price(res_inv)
            idx_p = parse_price(res_idx, is_index=True)
            fut_p = parse_price(res_fut, is_index=True)

            if lev_p > 0: self.market_data['lev_price'] = int(lev_p)
            if inv_p > 0: self.market_data['inv_price'] = int(inv_p)
            if idx_p > 0: self.market_data['kospi200'] = idx_p
            if fut_p > 0: self.market_data['futures'] = fut_p

            # 3. [Real Basis 계산]
            # Basis = 선물현재가 - KOSPI200지수
            if self.market_data['futures'] > 0 and self.market_data['kospi200'] > 0:
                real_basis = self.market_data['futures'] - self.market_data['kospi200']
                self.market_data['basis'] = real_basis
              
                # 로그 출력 (중요: 데이터 들어오는지 확인용)
                print(f"-> [Real Basis] 현물: {self.market_data['kospi200']:.2f} | 선물: {self.market_data['futures']:.2f} | Basis: {real_basis:.2f}")
            else:
                # 데이터 수신 전이면 0.00
                print(f"⚠️ [데이터 대기중] 현물: {self.market_data['kospi200']} / 선물: {self.market_data['futures']}")
                real_basis = 0.00

            # 4. 화면 및 신호 갱신
            
            # ▼▼▼ 여기 3: '운용자산' -> '잔고' 로 수정 ▼▼▼
            self.lbl_cap.setText(f"잔고: {self.total_capital:,}원")
            
            self.lbl_cash.setText(f"가용현금: {self.current_cash:,}원")
            
            # Basis 색상 처리 (Contango: 빨강, Backwardation: 파랑)
            basis_color = "#ff5555" if real_basis > 0 else "#5555ff"
            # (참고: 여기는 이미 Real Basis로 되어 있어서 수정 안 해도 됩니다)
            self.lbl_basis_info.setText(f"Real Basis: {real_basis:.2f}")
          

            # 전략 분석 및 신호 발생
            decision = self.engine.analyze(real_basis)
            self._update_signal_ui(decision)
            self.panel_lev.update_ui(self.market_data['lev_price'], self.panel_lev.holding_qty, self.panel_lev.avg_price)
            self.panel_inv.update_ui(self.market_data['inv_price'], self.panel_inv.holding_qty, self.panel_inv.avg_price)
        except Exception as e:
            print(f"!!! 데이터 처리 에러: {e}")
            print(traceback.format_exc())

    def _update_signal_ui(self, decision):
        if time.time() - self.last_signal_time < 2.0: return # 깜빡임 방지
        if decision['action'] != "HOLD":
            self.lbl_signal.setText(decision['msg'])
            self.lbl_signal.setStyleSheet(f"background-color: #222; color: {decision['color']}; border: 4px solid {decision['border']};")
            self.last_signal_time = time.time()
          

            # [자동 매매 연결 가능 지점]
            # if decision['action'] == "BUY_LEVERAGE": self.buy_percent("LEV", 0.1)
        else:
            self.lbl_signal.setText(decision['msg'])
            self.lbl_signal.setStyleSheet(f"background-color: {COLOR_SIGNAL_BG}; color: #555; border: none;")
    def core_loop(self):
        asyncio.create_task(self._process())
    async def _process(self):
        if IS_SIMULATION: pass
        else: await self._fetch_real_data()
    def keyPressEvent(self, event):
        key = event.key()
        
        # --- [상승 배팅] 레버리지 ---
        if key == Qt.Key_F1:
            self.log("⌨️ [Key F1] 레버리지 10% 매수 요청")
            self.buy_percent("LEV", 0.10)
            
        elif key == Qt.Key_F2:
            self.log("⌨️ [Key F2] 레버리지 50% 매수 요청 (물타기/불타기)")
            self.buy_percent("LEV", 0.50)

        # --- [하락 배팅] 인버스 ---
        elif key == Qt.Key_F3:
            self.log("⌨️ [Key F3] 인버스 10% 매수 요청")
            self.buy_percent("INV", 0.10)
            
        elif key == Qt.Key_F4:
            self.log("⌨️ [Key F4] 인버스 50% 매수 요청")
            self.buy_percent("INV", 0.50)

        # --- [청산] ---
        elif key == Qt.Key_F5 or key == Qt.Key_Space:
            self.log("⌨️ [Key Space/F5] 긴급 전량 청산")
            self.sell_all()
            
        # --- [디버깅] 데이터 강제 갱신 ---
        elif key == Qt.Key_F12:
            self.log("🔄 데이터 강제 새로고침")
            self.async_init()
    def buy_percent(self, target_type, percent):
        """
        target_type: "LEV" (레버리지) or "INV" (인버스)
        percent: 0.1 (10%), 0.2 (20%) ...
        """
        # 1. 타겟 설정
        if target_type == "LEV":
            target_panel = self.panel_lev
            opp_panel = self.panel_inv
            target_name = "🔴 레버리지"
        else:
            target_panel = self.panel_inv
            opp_panel = self.panel_lev
            target_name = "🔵 인버스"

        # 2. [검증] 스위칭 로직 (반대 포지션 보유 시 전량 매도)
        if opp_panel.holding_qty > 0:
            self.log(f"⚡ [스위칭 감지] {opp_panel.name} 전량 청산 후 {target_name} 진입 시도")
            
            # 반대 포지션 매도 실행
            # (주의: 실제 API 전송은 비동기지만, 로직상 현금 계산을 위해 즉시 처리)
            self.execute_sell(opp_panel, opp_panel.holding_qty)
            
            # API 딜레이를 고려하여 약간의 로그 텀을 둠 (실제 sleep은 안함)
            self.log(f"   -> 반대 포지션 청산 주문 완료.")

        # 3. 매수 금액 계산
        # 현재 가용 현금(스위칭 매도 금액 포함됨) * 비중
        invest_amount = int(self.current_cash * percent)
        
        # 최소 주문 금액 안전장치 (예: 10만원 미만은 주문 X)
        if invest_amount < 100000:
            self.log(f"⚠️ [주문 불가] 매수 금액 부족 ({invest_amount:,}원)")
            return

        # 4. 수량 계산 및 매수
        if target_panel.curr_price > 0:
            qty = int(invest_amount / target_panel.curr_price)
            if qty > 0:
                self.execute_buy(target_panel, qty)
                self.log(f"✅ [{target_name}] 자산의 {int(percent*100)}% 매수 완료 ({qty:,}주)")
            else:
                self.log(f"⚠️ 가격 데이터 오류 또는 잔고 부족")
        else:
            self.log(f"⚠️ 현재가 수신 대기 중...")

    def sell_all(self):
        self.log("💰 [전량 청산]")
        if self.panel_lev.holding_qty > 0: self.execute_sell(self.panel_lev, self.panel_lev.holding_qty)
        if self.panel_inv.holding_qty > 0: self.execute_sell(self.panel_inv, self.panel_inv.holding_qty)

    def execute_buy(self, panel, qty):
        self.log(f"🚀 {panel.name} 매수: {qty:,}주")
        if not IS_SIMULATION: asyncio.create_task(self.kiwoom.send_order(panel.code, qty, "buy", 0))
        cost = qty * panel.curr_price; self.current_cash -= cost
        total = (panel.holding_qty * panel.avg_price) + cost
        panel.holding_qty += qty; panel.avg_price = total / panel.holding_qty
    def execute_sell(self, panel, qty):
        if qty <= 0: return
        self.log(f"💰 {panel.name} 매도: {qty:,}주")
        if not IS_SIMULATION: asyncio.create_task(self.kiwoom.send_order(panel.code, qty, "sell", 0))
        revenue = qty * panel.curr_price; profit = (panel.curr_price - panel.avg_price) * qty
        self.current_cash += revenue; self.total_realized_profit += profit
        panel.holding_qty -= qty;
        if panel.holding_qty <= 0: panel.holding_qty = 0; panel.avg_price = 0
    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_view.insertRow(0); self.log_view.setItem(0, 0, QTableWidgetItem(f"[{t}] {msg}"))
    def async_init(self):
        if not IS_SIMULATION: asyncio.create_task(self.init_kiwoom())
        else: self.log("🧪 [SIMULATION MODE] 가상 데이터 구동 중...")
    async def init_kiwoom(self):
        try:
            import aiohttp
            if not self.kiwoom.session: self.kiwoom.session = aiohttp.ClientSession()
            await self.kiwoom._ensure_token()
            self.log("✅ 키움증권 서버 연결 성공. 기관급 전략 엔진 시동...")
        except: self.log("❌ 서버 연결 실패")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    trader = SolabTraderV13()
    trader.show()
    with loop: loop.run_forever()