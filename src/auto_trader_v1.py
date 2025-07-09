from strategy.auto_strategy_v1 import AutoStrategyV1

if __name__ == "__main__":
    strategy = AutoStrategyV1(desired_amount=10, interval_sec=2)
    strategy.run() 