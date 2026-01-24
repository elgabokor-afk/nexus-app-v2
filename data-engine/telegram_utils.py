import requests
import os
import logging

class TelegramAlerts:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token or not self.chat_id:
            logging.warning("⚠️ Telegram Bot Token or Chat ID missing. Alerts disabled.")

    def send_signal(self, symbol, signal_type, price, confidence, stop_loss=None, take_profit=None, 
                    imbalance=None, spread_pct=None, depth_score=None, ema_200=None):
        if not self.token or not self.chat_id:
            return

        emoji = "🚀 BUY" if signal_type == "BUY" else "🔻 SELL"
        color_dot = "🟢" if signal_type == "BUY" else "🔴"
        
        message = (
            f"<b>{emoji} SIGNAL DETECTED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>Asset:</b> {symbol}\n"
            f"💰 <b>Price:</b> ${price:,.2f}\n"
            f"🎯 <b>Confidence:</b> {confidence}%\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        # Add V4 Quant Metrics Section
        if imbalance is not None:
             # Interpret Imbalance
             imb_str = "Neutral"
             if imbalance > 0.2: imb_str = "Bullish 🐂"
             elif imbalance < -0.2: imb_str = "Bearish 🐻"
             
             message += (
                 f"📊 <b>Quant Analysis:</b>\n"
                 f"• Imbalance: {imb_str} ({imbalance:+.2f})\n"
                 f"• Spread: {spread_pct:.2f}%\n"
                 f"• Depth Quality: {depth_score}/100 🌊\n\n"
             )
        
        if stop_loss:
            message += f"🛑 <b>Stop Loss:</b> ${stop_loss:,.2f}\n"
        if take_profit:
            message += f"✅ <b>Take Profit:</b> ${take_profit:,.2f}\n"
            
        message += "\n🔗 <a href='https://nexus-app-v2.vercel.app/dashboard'>Open Nexus Terminal</a>"

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            logging.info(f"✅ Telegram alert sent for {symbol}")
        except Exception as e:
            logging.error(f"❌ Failed to send Telegram alert: {e}")

    def send_error(self, message):
        if not self.token or not self.chat_id:
            return
            
        payload = {
            "chat_id": self.chat_id,
            "text": f"⚠️ <b>NEXUS SYSTEM ERROR:</b>\n\n<code>{message}</code>",
            "parse_mode": "HTML"
        }
        requests.post(f"{self.base_url}/sendMessage", json=payload)
