import logging

# V2301: NEUTRONIZED TELEGRAM
# The user requested TOTAL removal of Telegram functionality.
# This entire class is now a dummy shell that does nothing.

class TelegramAlerts:
    def __init__(self):
        # Do not even load environment variables. Total Silence.
        self.token = None 
        self.chat_id = None
        logging.info("🔇 Telegram Module is DISABLED (Neutronized Mode).")

    def send_signal(self, symbol, signal_type, price, confidence, stop_loss=None, take_profit=None, 
                    imbalance=None, spread_pct=None, depth_score=None, ema_200=None):
        # Do nothing.
        return

    def send_error(self, message):
        # Do nothing.
        return
