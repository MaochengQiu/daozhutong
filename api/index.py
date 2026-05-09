import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WECHAT_SYSTEM_DIR = PROJECT_ROOT / "wechat-system"
sys.path.insert(0, str(WECHAT_SYSTEM_DIR))

from app.main import app

