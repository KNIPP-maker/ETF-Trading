from pykiwoom.kiwoom import Kiwoom
from PyQt5.QtWidgets import QApplication
import sys
import os
from dotenv import load_dotenv

class KiwoomManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.app = QApplication(sys.argv)
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)
        load_dotenv()
        self.account_no = os.getenv("ACCOUNT_NO")
        if not self.account_no:
            accounts = self.kiwoom.GetLoginInfo("ACCNO")
            if accounts:
                self.account_no = accounts.split(';')[0]
        self._initialized = True

    def get_kiwoom(self):
        return self.kiwoom

    def get_account_no(self):
        return self.account_no 