"""用户画像存储层：8 类画像字段的 CRUD，JSON 文件持久化。

MVP 阶段每个用户一个 JSON 文件，无需外部数据库。
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("profile_store")

# 8 类画像字段定义
PROFILE_CATEGORIES = {
    "basic_info": "基本情况",
    "stage_goal": "阶段目标",
    "knowledge_level": "知识储备水平",
    "interest_preference": "兴趣偏好",
    "expression_habit": "表达习惯",
    "emotion_trait": "情绪变化特征",
    "core_problem": "核心待解决问题",
    "authorization_boundary": "信息授权边界",
}

CATEGORY_ORDER = list(PROFILE_CATEGORIES.keys())


class ProfileStore:
    """管理用户画像的增删改查，按用户 ID 分文件存储。"""

    def __init__(self, storage_dir: Path | None = None):
        if storage_dir is None:
            storage_dir = Path(__file__).resolve().parent.parent / "data" / "profiles"
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def get_profiles(self, user_id: str) -> list[dict]:
        """获取指定用户的所有画像条目。"""
        return self._read_user(user_id)

    def get_categories(self) -> list[dict]:
        """返回 8 类画像字段的定义。"""
        return [
            {"key": key, "label": label}
            for key, label in zip(CATEGORY_ORDER, [PROFILE_CATEGORIES[k] for k in CATEGORY_ORDER])
        ]

    def create_profile(self, user_id: str, entry: dict) -> dict:
        """新增一条画像条目。

        entry 需包含: profile_key, profile_value, evidence(可选), confidence(可选),
                     authorization_status(可选), scope(可选)
        """
        if entry.get("profile_key") not in PROFILE_CATEGORIES:
            raise ValueError(f"无效的画像类别「{entry.get('profile_key')}」")

        now = datetime.now(timezone.utc).isoformat()
        profile = {
            "id": uuid.uuid4().hex[:12],
            "user_id": user_id,
            "profile_key": entry["profile_key"],
            "profile_value": entry.get("profile_value", ""),
            "evidence": entry.get("evidence", ""),
            "confidence": entry.get("confidence", 0.5),
            "authorization_status": entry.get("authorization_status", "confirmed"),
            "scope": entry.get("scope", "learning_context"),
            "created_at": now,
            "updated_at": now,
        }

        profiles = self._read_user(user_id)
        profiles.append(profile)
        self._write_user(user_id, profiles)
        logger.info("画像已添加: user=%s key=%s", user_id, profile["profile_key"])
        return profile

    def update_profile(self, user_id: str, profile_id: str, updates: dict) -> dict | None:
        """更新指定画像条目，返回更新后的条目，不存在时返回 None。"""
        profiles = self._read_user(user_id)
        for p in profiles:
            if p["id"] == profile_id:
                # 只允许更新特定字段
                allowed = {
                    "profile_value", "profile_key", "evidence", "confidence",
                    "authorization_status", "scope",
                }
                for key in allowed:
                    if key in updates:
                        p[key] = updates[key]
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._write_user(user_id, profiles)
                logger.info("画像已更新: user=%s profile=%s", user_id, profile_id)
                return p

        return None

    def delete_profile(self, user_id: str, profile_id: str) -> bool:
        """删除指定画像条目，成功返回 True。"""
        profiles = self._read_user(user_id)
        new_profiles = [p for p in profiles if p["id"] != profile_id]
        if len(new_profiles) == len(profiles):
            return False
        self._write_user(user_id, new_profiles)
        logger.info("画像已删除: user=%s profile=%s", user_id, profile_id)
        return True

    def seed_demo_profiles(self, user_id: str, entries: list[dict]) -> list[dict]:
        """批量写入演示画像（覆盖已有）。"""
        now = datetime.now(timezone.utc).isoformat()
        profiles = []
        for entry in entries:
            profile = {
                "id": uuid.uuid4().hex[:12],
                "user_id": user_id,
                "profile_key": entry["profile_key"],
                "profile_value": entry["profile_value"],
                "evidence": entry.get("evidence", "演示种子数据"),
                "confidence": entry.get("confidence", 0.9),
                "authorization_status": entry.get("authorization_status", "confirmed"),
                "scope": entry.get("scope", "learning_context"),
                "created_at": now,
                "updated_at": now,
            }
            profiles.append(profile)
        self._write_user(user_id, profiles)
        logger.info("种子画像已写入: user=%s count=%d", user_id, len(profiles))
        return profiles

    # ------------------------------------------------------------------
    # 文件读写
    # ------------------------------------------------------------------

    def _user_path(self, user_id: str) -> Path:
        return self.storage_dir / f"{user_id}.json"

    def _read_user(self, user_id: str) -> list[dict]:
        path = self._user_path(user_id)
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_user(self, user_id: str, profiles: list[dict]):
        path = self._user_path(user_id)
        path.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8"
        )
