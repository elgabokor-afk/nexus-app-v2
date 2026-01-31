import os
import pusher
import logging

logger = logging.getLogger(__name__)

class PusherClient:
    def __init__(self):
        self.app_id = os.getenv("PUSHER_APP_ID")
        self.key = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
        self.secret = os.getenv("PUSHER_SECRET")
        self.cluster = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")
        
        if not all([self.app_id, self.key, self.secret, self.cluster]):
            logger.warning("Pusher credentials missing. Realtime features disabled.")
            self.client = None
        else:
            try:
                self.client = pusher.Pusher(
                    app_id=self.app_id,
                    key=self.key,
                    secret=self.secret,
                    cluster=self.cluster,
                    ssl=True
                )
                logger.info("Pusher Client Initialized.")
            except Exception as e:
                logger.error(f"Failed to init Pusher: {e}")
                self.client = None

    def trigger(self, channel, event, data):
        """Safe trigger that catches errors"""
        if not self.client:
            return
        
        try:
            self.client.trigger(channel, event, data)
            logger.info(f"   >>> [PUSHER] Event '{event}' sent to '{channel}'")
        except Exception as e:
            logger.error(f"Pusher Trigger Error: {e}")

# Global Instance
pusher_client = PusherClient()
