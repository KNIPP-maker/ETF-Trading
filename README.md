# ETF Auto Trader

ETF 자동매매 프로그램입니다.

## 기능

- ETF 가격 모니터링
- 자동 매매 실행
- 포트폴리오 관리
- 백테스팅
- 실시간 알림

## 설치

1. 저장소 클론
```bash
git clone https://github.com/solaris-offidum/auto-trading-bot.git
cd auto-trading-bot
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정을 입력
```

## 실행

```bash
python src/main.py
```

## 프로젝트 구조

```
etf-auto-trader/
├── src/
│   ├── __init__.py
│   ├── main.py              # 메인 애플리케이션
│   ├── config/              # 설정 파일들
│   ├── models/              # 데이터 모델
│   ├── services/            # 비즈니스 로직
│   └── utils/               # 유틸리티 함수들
├── tests/                   # 테스트 파일들
├── requirements.txt         # Python 의존성
├── README.md               # 프로젝트 문서
└── .env.example            # 환경변수 예시
```

## 라이센스

MIT License 

---

# [부록] 현재까지 확정된 로직/상태머신/팩터 정의 (임시, DESIGN.md로 이동 예정)

## 1. 상태머신 및 진입/청산 로직 (MidasQuantumTrader)

```python
class MidasQuantumTrader:
    def __init__(self):
        self.position = None  # 'LEVERAGE', 'INVERSE', or None
        self.entry_prices = []
        self.trade_log = []
        self.max_entry_count = 2
        self.entry_count = 0
        self.log_file = "trade_log.txt"
        self.json_file = "trade_log.json"
        self.initial_balance = 10000000  # 1천만원 가정
        self.balance = self.initial_balance
        self.position_size = 0
        self.position_type = None
        self.report_dir = "report"

    def should_enter(self, kospi_futures, kospi_spot, foreign_flow):
        gap = (kospi_futures - kospi_spot) / kospi_spot * 100
        if self.entry_count < self.max_entry_count:
            if gap >= 0.3 and foreign_flow > 0:
                return 'LEVERAGE'
            elif gap <= -0.3 and foreign_flow < 0:
                return 'INVERSE'
        return None

    def should_exit(self, current_price):
        if not self.entry_prices:
            return False
        avg_entry = sum(self.entry_prices) / len(self.entry_prices)
        profit_ratio = (current_price - avg_entry) / avg_entry * 100 if self.position == 'LEVERAGE' else (avg_entry - current_price) / avg_entry * 100
        if profit_ratio >= 1.0 or profit_ratio <= -0.6:
            return True
        return False

    def step(self, market_data):
        kospi_futures = market_data['futures']
        kospi_spot = market_data['spot']
        foreign_flow = market_data['foreign_net']
        current_price = market_data['etf_price']
        if self.position:
            if self.should_exit(current_price):
                self.exit_position(current_price)
        else:
            entry_signal = self.should_enter(kospi_futures, kospi_spot, foreign_flow)
            if entry_signal:
                self.enter_position(entry_signal, current_price)
```

- **상태**: `self.position` (`None`, `'LEVERAGE'`, `'INVERSE'`)
- **진입 조건**: 선물-현물 괴리율(gap)이 +0.3% 이상 & 외국인 순매수 → 레버리지, -0.3% 이하 & 외국인 순매도 → 인버스
- **청산 조건**: 진입 후 +1% 이상 수익 or -0.6% 이상 손실 시 청산
- **최대 진입 횟수**: 2회

## 2. 신호 엔진(팩터) 예시 (kospi_signal_engine)

```python
def kospi_signal_engine(market_data):
    """
    시장 데이터를 받아서 매수/매도 신호를 반환합니다.
    예시 신호: 'BUY_LEVERAGE', 'BUY_INVERSE', None
    """
    # TODO: 실제 전략 로직 구현
    # 예시: 단순 무작위 신호
    import random
    signals = ["BUY_LEVERAGE", "BUY_INVERSE", None]
    return random.choice(signals)
```

- 실제 전략에서는 괴리율, 외국인 수급 등 다양한 팩터를 조합하여 신호 생성 예정

## 3. 단순화 MVP 상태머신 (SingleEntryExitMVP)

```python
class SingleEntryExitMVP:
    def __init__(self, desired_amount=10, interval_sec=2):
        self.position = None  # None, "LEVERAGE", "INVERSE"
        self.entry_price = None
        self.desired_amount = desired_amount
        self.interval_sec = interval_sec
        self.running = False

    def run(self):
        while self.running:
            market_data = fetch_market_data()
            signal = kospi_signal_engine(market_data)
            price = market_data.get("price")
            if self.position is None:
                if signal == "BUY_LEVERAGE":
                    execute_trade("KODEX 레버리지", "BUY", amount=self.desired_amount)
                    self.position = "LEVERAGE"
                    self.entry_price = price
                elif signal == "BUY_INVERSE":
                    execute_trade("KODEX 200선물인버스2X", "BUY", amount=self.desired_amount)
                    self.position = "INVERSE"
                    self.entry_price = price
            else:
                if check_exit(market_data, self.entry_price):
                    execute_trade("ALL", "SELL")
                    self.position = None
                    self.entry_price = None
            time.sleep(self.interval_sec)
```

---

※ 본 내용은 추후 `docs/DESIGN.md`로 이동 예정입니다. 

네, `tests/` 디렉터리에는 Cursor의 **Ctrl + K** ("Write unit test for function X") 명령으로 자동 생성된 **Stub 테스트**(기본 골격/자동 생성 테스트 코드)가 포함되어 있습니다.

이런 Stub 테스트는 다음과 같은 특징이 있습니다:

- 함수/클래스 시그니처와 기본적인 호출 구조만 포함
- 실제 검증 로직(assert, mock 등)은 최소화되어 있거나, `TODO` 주석이 남아 있음
- 예시:
    ```python
    # tests/test_data_service.py
    def test_fetch_market_data():
        # TODO: implement test
        assert True
    ```
- 실제 동작 검증을 위해서는 수동으로 테스트 케이스를 보강해야 함

**정리:**  
`tests/` 폴더에는 Cursor의 자동화 기능으로 생성된 Stub 테스트가 들어 있으며,  
실제 프로젝트 품질 확보를 위해서는 이 테스트들을 구체적으로 작성(입력/출력/예외 등 검증)하는 추가 작업이 필요합니다.

필요하다면,  
- Stub 테스트 자동 생성 예시  
- 실제 테스트 보강 방법  
- PyTest 활용법  
등도 안내해드릴 수 있습니다! 