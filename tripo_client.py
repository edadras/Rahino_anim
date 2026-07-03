"""Minimal client for the Tripo3D Open API (https://platform.tripo3d.ai).

Reads the API key from the TRIPO_API_KEY environment variable, or from a
local .env file next to this module.
"""

import os
import time
from pathlib import Path

import requests

BASE_URL = "https://api.tripo3d.ai/v2/openapi"
TERMINAL_STATUSES = {"success", "failed", "cancelled", "banned", "expired"}


def _load_dotenv():
    env_file = Path(__file__).with_name(".env")
    if not env_file.is_file():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


class TripoError(RuntimeError):
    pass


class TripoClient:
    def __init__(self, api_key: str | None = None):
        if api_key is None:
            _load_dotenv()
            api_key = os.environ.get("TRIPO_API_KEY")
        if not api_key:
            raise TripoError(
                "No API key. Set TRIPO_API_KEY (or put it in .env, see .env.example)."
            )
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {api_key}"

    def _request(self, method: str, path: str, **kwargs):
        resp = self.session.request(method, f"{BASE_URL}{path}", timeout=60, **kwargs)
        try:
            payload = resp.json()
        except ValueError:
            resp.raise_for_status()
            raise TripoError(f"Non-JSON response from {path}: {resp.text[:200]}")
        if payload.get("code") != 0:
            raise TripoError(f"API error on {path}: {payload}")
        return payload["data"]

    # --- account -----------------------------------------------------------

    def balance(self) -> dict:
        return self._request("GET", "/user/balance")

    # --- tasks -------------------------------------------------------------

    def create_task(self, task: dict) -> str:
        """Submit a raw task payload, return the task_id."""
        return self._request("POST", "/task", json=task)["task_id"]

    def get_task(self, task_id: str) -> dict:
        return self._request("GET", f"/task/{task_id}")

    def wait_for_task(self, task_id: str, poll_seconds: float = 5.0) -> dict:
        while True:
            task = self.get_task(task_id)
            status = task.get("status")
            progress = task.get("progress", 0)
            print(f"  task {task_id}: {status} ({progress}%)", flush=True)
            if status in TERMINAL_STATUSES:
                if status != "success":
                    raise TripoError(f"Task {task_id} ended with status {status}: {task}")
                return task
            time.sleep(poll_seconds)

    # --- convenience wrappers ----------------------------------------------

    def text_to_model(self, prompt: str, **extra) -> str:
        return self.create_task({"type": "text_to_model", "prompt": prompt, **extra})

    def upload_image(self, path: str) -> str:
        """Upload a local image, return its file token."""
        file_path = Path(path)
        with file_path.open("rb") as fh:
            data = self._request("POST", "/upload", files={"file": (file_path.name, fh)})
        return data["image_token"]

    def image_to_model(self, image_path: str, **extra) -> str:
        token = self.upload_image(image_path)
        suffix = Path(image_path).suffix.lstrip(".").lower() or "jpg"
        return self.create_task(
            {"type": "image_to_model", "file": {"type": suffix, "file_token": token}, **extra}
        )

    def rig(self, model_task_id: str, out_format: str = "glb", **extra) -> str:
        return self.create_task(
            {
                "type": "animate_rig",
                "original_model_task_id": model_task_id,
                "out_format": out_format,
                **extra,
            }
        )

    def animate(self, rig_task_id: str, animation: str, out_format: str = "glb", **extra) -> str:
        """Retarget a preset animation (e.g. 'preset:run') onto a rigged model."""
        return self.create_task(
            {
                "type": "animate_retarget",
                "original_model_task_id": rig_task_id,
                "animation": animation,
                "out_format": out_format,
                **extra,
            }
        )

    # --- outputs -----------------------------------------------------------

    def download_outputs(self, task: dict, out_dir: str = "outputs") -> list[Path]:
        """Download every URL in the task output (model, textures, preview)."""
        task_id = task["task_id"]
        target = Path(out_dir) / task_id
        target.mkdir(parents=True, exist_ok=True)
        saved = []
        for name, url in (task.get("output") or {}).items():
            if not isinstance(url, str) or not url.startswith("http"):
                continue
            ext = Path(url.split("?", 1)[0]).suffix or ".bin"
            dest = target / f"{name}{ext}"
            with self.session.get(url, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                with dest.open("wb") as fh:
                    for chunk in resp.iter_content(1 << 16):
                        fh.write(chunk)
            print(f"  saved {dest}")
            saved.append(dest)
        return saved
