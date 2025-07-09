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
git clone <repository-url>
cd etf-auto-trader
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