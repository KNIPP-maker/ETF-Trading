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