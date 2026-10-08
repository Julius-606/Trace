
################################################################################
# FILE: backend/app/routers/terminal_pilot.py
# VERSION: 3.0.0 | SYSTEM: Orbit Decentralized Cluster Workspace
# IDENTITY: Real OS detection, multi-command procedure suggestions, and VS Code terminal sync.
################################################################################

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import json
import sqlite3
import platform
import asyncio
from google import genai
from google.genai import types
from app.core.config import settings
from app.core.nodes import cluster_manager

router = APIRouter(prefix="/terminal", tags=["Terminal Pilot"])

# Initialize Gemini Async Client
async_client = None
if settings.GEMINI_API_KEY:
    try:
        async_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        pass

class TerminalManager:
    def __init__(self):
        self.db_path = "vault.db"
        self._init_vault()
        self.os_type = "windows" if os.name == "nt" else "linux"
        self.cwd = os.getcwd()
        self.log_buffer = f"Orbit Terminal Deck [System: {platform.system()} {platform.release()}]\nConnected to cluster node.\n{self.get_prompt()}\n"

    def _init_vault(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS commands (id INTEGER PRIMARY KEY, name TEXT, cmd TEXT, category TEXT)")
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_prompt(self, cwd: Optional[str] = None) -> str:
        active_cwd = cwd or self.cwd
        if self.os_type == "windows":
            return f"{active_cwd}> "
        else:
            folder = os.path.basename(active_cwd.rstrip("/\\")) or "/"
            return f"orbit@{platform.node()}:{folder}$ "

    def save_command(self, name, cmd, category="General"):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO commands (name, cmd, category) VALUES (?, ?, ?)", (name, cmd, category))
        conn.commit()
        conn.close()

    def get_vault_commands(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT id, name, cmd, category FROM commands")
            rows = cursor.fetchall()
            conn.close()
            return [{"id": r[0], "name": r[1], "cmd": r[2], "category": r[3]} for r in rows]
        except Exception:
            return []

manager = TerminalManager()

class CommandRequest(BaseModel):
    command: str

class SuggestionRequest(BaseModel):
    user_goal: str

class SuggestedStep(BaseModel):
    step: int
    title: str
    cmd: str

class SuggestionResponse(BaseModel):
    explanation: str
    command: str
    commands: Optional[List[SuggestedStep]] = []

class VaultSaveRequest(BaseModel):
    name: str
    cmd: str
    category: Optional[str] = "General"

class ConnectNodeRequest(BaseModel):
    name: str
    host: str
    port: int = 8888

class SelectNodeRequest(BaseModel):
    name: str

@router.get("/status")
async def get_status():
    node = cluster_manager.get_active()
    status_data = await node.get_status()
    telemetry = status_data.get("telemetry", {})
    cwd = telemetry.get("cwd", os.getcwd())
    manager.cwd = cwd
    
    return {
        "active_node": cluster_manager.active_node_name,
        "nodes": list(cluster_manager.nodes.keys()),
        "telemetry": {
            "cpu": telemetry.get("cpu", 0),
            "ram": telemetry.get("ram", 0),
            "disk": telemetry.get("disk", 0),
            "cwd": cwd,
            "os": manager.os_type,
            "shell": "powershell" if manager.os_type == "windows" else "bash"
        },
        "output": manager.log_buffer,
        "os": manager.os_type,
        "prompt": manager.get_prompt(cwd)
    }

@router.post("/execute")
async def execute_command(req: CommandRequest):
    node = cluster_manager.get_active()
    current_prompt = manager.get_prompt()
    manager.log_buffer += f"{current_prompt}{req.command}\n"

    output = await node.execute(req.command)
    manager.log_buffer += output
    if not manager.log_buffer.endswith("\n"):
        manager.log_buffer += "\n"

    # Refresh status to get new cwd if changed (e.g. after cd)
    status_data = await node.get_status()
    new_cwd = status_data.get("telemetry", {}).get("cwd", manager.cwd)
    manager.cwd = new_cwd
    new_prompt = manager.get_prompt(new_cwd)
    manager.log_buffer += new_prompt

    return {
        "status": "success",
        "message": "Command executed",
        "output": output,
        "cwd": new_cwd,
        "prompt": new_prompt
    }

@router.post("/suggest")
async def suggest_command(req: SuggestionRequest):
    os_name = "Windows (PowerShell)" if manager.os_type == "windows" else "Linux/Unix (bash)"
    cwd = manager.cwd

    if async_client:
        try:
            prompt = (
                f"You are an expert DevOps and Systems Administrator in a VS Code terminal environment.\n"
                f"Operating System: {os_name}\n"
                f"Current Working Directory: {cwd}\n"
                f"User Goal: {req.user_goal}\n\n"
                f"Generate a concise, safe procedure to accomplish this goal. You may provide a single command "
                f"or a sequence of procedure steps (up to 4 steps) if the task involves multiple steps (e.g. git, docker, setup).\n"
                f"Return strictly valid JSON with this structure:\n"
                f"{{\n"
                f"  \"explanation\": \"Brief explanation of what this procedure does\",\n"
                f"  \"command\": \"The primary command or one-liner\",\n"
                f"  \"commands\": [\n"
                f"    {{\"step\": 1, \"title\": \"Step description\", \"cmd\": \"exact command\"}},\n"
                f"    {{\"step\": 2, \"title\": \"Step description\", \"cmd\": \"exact command\"}}\n"
                f"  ]\n"
                f"}}"
            )

            response = await async_client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            data = json.loads(response.text)
            commands_list = data.get("commands", [])
            primary_cmd = data.get("command") or (commands_list[0]["cmd"] if commands_list else "ls")
            return {
                "explanation": data.get("explanation", "Recommended command procedure"),
                "command": primary_cmd,
                "commands": commands_list
            }
        except Exception as e:
            pass

    # Heuristic fallback if API key is absent or network fails
    goal_lower = req.user_goal.lower()
    if "git" in goal_lower or "commit" in goal_lower or "push" in goal_lower:
        return {
            "explanation": "Git repository synchronization procedure: check status, stage changes, commit, and push.",
            "command": "git status && git add . && git commit -m 'update' && git push",
            "commands": [
                {"step": 1, "title": "Check repository status", "cmd": "git status"},
                {"step": 2, "title": "Stage all changes", "cmd": "git add ."},
                {"step": 3, "title": "Commit with descriptive message", "cmd": "git commit -m 'chore: update changes'"},
                {"step": 4, "title": "Push to remote repository", "cmd": "git push"}
            ]
        }
    elif "docker" in goal_lower:
        return {
            "explanation": "Docker inspection and build procedure.",
            "command": "docker ps -a",
            "commands": [
                {"step": 1, "title": "List running containers", "cmd": "docker ps"},
                {"step": 2, "title": "List all container images", "cmd": "docker images"},
                {"step": 3, "title": "View container system stats", "cmd": "docker stats --no-stream"}
            ]
        }
    elif "disk" in goal_lower or "space" in goal_lower or "memory" in goal_lower or "ram" in goal_lower:
        if manager.os_type == "windows":
            return {
                "explanation": "Check Windows memory and disk utilization.",
                "command": "Get-PSDrive -PSProvider FileSystem; Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5",
                "commands": [
                    {"step": 1, "title": "Check storage space", "cmd": "Get-PSDrive -PSProvider FileSystem"},
                    {"step": 2, "title": "Top RAM-consuming processes", "cmd": "Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5"}
                ]
            }
        else:
            return {
                "explanation": "Check Linux storage and RAM status.",
                "command": "df -h; free -m",
                "commands": [
                    {"step": 1, "title": "Disk space utilization", "cmd": "df -h"},
                    {"step": 2, "title": "Memory / RAM metrics", "cmd": "free -h"},
                    {"step": 3, "title": "Top CPU processes", "cmd": "ps aux --sort=-%cpu | head -n 6"}
                ]
            }
    else:
        default_cmd = "dir" if manager.os_type == "windows" else "ls -la"
        return {
            "explanation": f"Inspect current directory contents in {os_name}.",
            "command": default_cmd,
            "commands": [
                {"step": 1, "title": "List directory entries", "cmd": default_cmd}
            ]
        }

@router.get("/vault")
async def get_vault():
    return {"commands": manager.get_vault_commands()}

@router.post("/vault/save")
async def save_to_vault(req: VaultSaveRequest):
    manager.save_command(req.name, req.cmd, req.category or "General")
    return {"status": "success", "message": "Command saved to vault"}

@router.post("/nodes/connect")
async def connect_node(req: ConnectNodeRequest):
    cluster_manager.add_node(req.name, req.host, req.port)
    return {"status": "success", "message": f"Node {req.name} attached"}

@router.post("/nodes/select")
async def select_node(req: SelectNodeRequest):
    cluster_manager.select_node(req.name)
    return {"status": "success", "selected": cluster_manager.active_node_name}

@router.post("/clear")
async def clear_terminal():
    prompt = manager.get_prompt()
    manager.log_buffer = prompt
    return {"status": "success", "prompt": prompt}



