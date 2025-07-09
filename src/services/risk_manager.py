def check_exit(market_data, entry_price=None):
    """
    시장 데이터와 진입가에 따라 전량 매도(청산) 신호를 판단합니다.
    예시: 무작위 True/False 반환
    """
    import random
    return random.choice([True, False]) 