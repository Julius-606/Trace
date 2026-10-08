
################################################################################
# FILE: backend/app/core/nodes.py
# VERSION: 1.1.0 | SYSTEM: Orbit Decentralized Node Framework
# IDENTITY: Multi-node workstation routing with Local Subprocess support
################################################################################

import os
import httpx
import logging
import subprocess
import threading
import queue
import psutil

logger = logging.getLogger("OrbitNodes")

class BaseNode:
    def __init__(self, name: str, node_type: str = "remote"):
        self.name = name
        self.node_type = node_type

    async def get_status(self) -> dict:
        raise NotImplementedError

    async def execute(self, command: str) -> str:
        raise NotImplementedError

class LocalNode(BaseNode):
    """The node running on the current machine (e.g., the HuggingFace Space itself)."""
    def __init__(self, name: str):
        super().__init__(name, "local")
        shell = 'powershell.exe' if os.name == 'nt' else 'bash'
        self.proc = subprocess.Popen(
            [shell, '-NoExit', '-Command', '-'] if os.name == 'nt' else [shell],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        self.out_queue = queue.Queue()
        threading.Thread(target=self._read_stream, args=(self.proc.stdout,), daemon=True).start()
        threading.Thread(target=self._read_stream, args=(self.proc.stderr,), daemon=True).start()

    def _read_stream(self, stream):
        try:
            for line in iter(stream.readline, ""):
                self.out_queue.put(line)
        except:
            pass

    async def get_status(self) -> dict:
        cwd = os.getcwd()
        try:
            p = psutil.Process(self.proc.pid)
            cwd = p.cwd()
        except:
            pass
        return {
            "status": "healthy",
            "telemetry": {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent,
                "cwd": str(cwd)
            }
        }

    async def execute(self, command: str) -> str:
        if self.proc.poll() is None:
            self.proc.stdin.write(command + "\n")
            self.proc.stdin.flush()
            # Give it a moment to produce output
            import asyncio
            await asyncio.sleep(0.5)
            output = ""
            while not self.out_queue.empty():
                output += self.out_queue.get()
            return output
        return "Local terminal process is dead."

class RemoteAgentNode(BaseNode):
    def __init__(self, name: str, host: str, port: int = 8888):
        super().__init__(name, "agent")
        self.host = host
        self.port = port

    async def get_status(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"http://{self.host}:{self.port}/status")
                return resp.json()
        except:
            return {"status": "offline", "telemetry": {"cpu": 0, "ram": 0, "disk": 0, "cwd": "unknown"}}

    async def execute(self, command: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"http://{self.host}:{self.port}/execute", json={"command": command})
                data = resp.json()
                return data.get("output", data.get("message", "Command executed (no output)"))
        except Exception as e:
            return f"Remote error: {str(e)}"

class NodeClusterManager:
    def __init__(self):
        # The primary node is the local HF Space / Server
        self.nodes = {
            "HF_Space_Node": LocalNode("HF_Space_Node")
        }
        self.active_node_name = "HF_Space_Node"

    def add_node(self, name: str, host: str, port: int = 8888):
        self.nodes[name] = RemoteAgentNode(name, host, port)

    def select_node(self, name: str):
        if name in self.nodes:
            self.active_node_name = name

    def get_active(self) -> BaseNode:
        return self.nodes[self.active_node_name]

cluster_manager = NodeClusterManager()


