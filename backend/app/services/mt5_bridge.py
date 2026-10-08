
################################################################################
#FILE: backend/app/services/mt5_bridge.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import MetaTrader5 as mt5
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings
import logging
import pandas as pd

logger = logging.getLogger("MT5-Bridge")

class MT5Engine:
    def __init__(self):
        self.connected = False

    def connect(self):
        if not mt5.initialize():
            logger.error(f"MT5 Init failed. Error code: {mt5.last_error()}")
            return False

        authorized = mt5.login(
            settings.MT5_LOGIN,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER
        )

        if authorized:
            self.connected = True
            logger.info(f"MT5 Connected successfully to {settings.MT5_SERVER}. Let's get this bread.")
            return True
        else:
            logger.error(f"Failed to connect to MT5. Did you blow the account? Code: {mt5.last_error()}")
            return False

    def check_exposure(self):
        if not self.connected:
            self.connect()

        account_info = mt5.account_info()
        if account_info is None:
            return {"status": "error", "message": "Could not retrieve account info."}

        margin_level = account_info.margin_level
        equity = account_info.equity

        if margin_level > 0 and margin_level < 300.0:
            return {"status": "DANGER", "message": "Margin Level critically low. Close some positions bro!"}

        return {"status": "CHILL", "equity": equity, "margin_level": margin_level}

mt5_engine = MT5Engine()

