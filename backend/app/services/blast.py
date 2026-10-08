
# ==========================================
# IDENTITY: The Megaphone / Blast Protocol
# FILEPATH: backend/app/services/blast.py
# COMPONENT: WebSocket Manager
# ROLE: Blasts real-time syncs to Ubuntu & Android.
# VIBE: "WAKE UP, YOUR STOP LOSS JUST GOT HIT!" 🚨🔊
# ==========================================

from fastapi import WebSocket
import logging
import json

logger = logging.getLogger("Blast-Protocol")

class BlastManager:
    """
    Manages dual-device sync. When the VM updates something, 
    this class makes sure your laptop and phone know instantly.
    """
    def __init__(self):
        self.active_devices: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_devices.append(websocket)
        logger.info(f"Device locked in. Total devices: {len(self.active_devices)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_devices:
            self.active_devices.remove(websocket)
            logger.info("Device disconnected. Hope they didn't rage quit.")

    async def blast_event(self, event_type: str, payload: dict):
        """
        The main artery. Sends a JSON payload to all connected devices.
        Used for Forex SL/TP alerts, Task reminders, etc.
        """
        message = {
            "type": event_type,
            "data": payload
        }
        dead_connections = []
        for device in self.active_devices:
            try:
                await device.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to blast device: {e}")
                dead_connections.append(device)
                
        # Clean up connections that ghosted us
        for dead in dead_connections:
            self.disconnect(dead)

# Global instance to be imported across the app (like in forex.py)
blast_engine = BlastManager()

