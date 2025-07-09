from strategy.single_entry_exit_mvp import SingleEntryExitMVP

if __name__ == "__main__":
    strategy = SingleEntryExitMVP(desired_amount=10, interval_sec=2)
    strategy.run() 