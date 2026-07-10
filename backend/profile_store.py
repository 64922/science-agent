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
    # 授权管理 (Issue 12)
    # ------------------------------------------------------------------

    def revoke_profile(self, user_id: str, profile_id: str) -> dict | None:
        """撤回单条画像授权，状态设为 revoked。"""
        profiles = self._read_user(user_id)
        for p in profiles:
            if p["id"] == profile_id:
                prev_status = p.get("authorization_status", "confirmed")
                p["authorization_status"] = "revoked"
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._write_user(user_id, profiles)
                self._write_audit_entry(user_id, {
                    "action": "revoke_single",
                    "target": profile_id,
                    "previous_state": prev_status,
                    "new_state": "revoked",
                })
                logger.info("画像已撤回: user=%s profile=%s", user_id, profile_id)
                return p
        return None

    def revoke_category(self, user_id: str, category_key: str) -> int:
        """撤回某类画像的全部授权，返回撤回数量。"""
        if category_key not in PROFILE_CATEGORIES:
            raise ValueError(f"无效的画像类别「{category_key}」")
        profiles = self._read_user(user_id)
        count = 0
        for p in profiles:
            if p["profile_key"] == category_key and p.get("authorization_status") != "revoked":
                p["authorization_status"] = "revoked"
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
                count += 1
        if count > 0:
            self._write_user(user_id, profiles)
            self._write_audit_entry(user_id, {
                "action": "revoke_category",
                "target": category_key,
                "count": count,
                "new_state": "revoked",
            })
            logger.info("类别已撤回: user=%s category=%s count=%d", user_id, category_key, count)
        return count

    def set_memory_pause(self, user_id: str, paused: bool) -> dict:
        """暂停或恢复全部记忆。"""
        path = self._memory_state_path(user_id)
        now = datetime.now(timezone.utc).isoformat()
        if path.exists():
            state = json.loads(path.read_text(encoding="utf-8"))
        else:
            state = {"paused": False, "paused_at": None, "resumed_at": None}

        prev_paused = state.get("paused", False)
        if prev_paused == paused:
            return state

        state["paused"] = paused
        if paused:
            state["paused_at"] = now
        else:
            state["resumed_at"] = now

        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_audit_entry(user_id, {
            "action": "pause_memory" if paused else "resume_memory",
            "target": "all",
            "previous_state": "paused" if prev_paused else "active",
            "new_state": "paused" if paused else "active",
        })
        logger.info("记忆%s: user=%s", "已暂停" if paused else "已恢复", user_id)
        return state

    def get_memory_status(self, user_id: str) -> dict:
        """获取用户的记忆暂停状态。"""
        path = self._memory_state_path(user_id)
        if not path.exists():
            return {"paused": False, "paused_at": None, "resumed_at": None}
        return json.loads(path.read_text(encoding="utf-8"))

    def get_audit_log(self, user_id: str) -> list[dict]:
        """获取用户的授权变更操作记录。"""
        path = self._audit_log_path(user_id)
        if not path.exists():
            return []
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return list(reversed(entries))

    def get_authorized_profiles(self, user_id: str) -> tuple[list[dict], list[dict]]:
        """返回 (已授权画像列表, 被跳过的画像列表)。"""
        memory_status = self.get_memory_status(user_id)
        all_profiles = self._read_user(user_id)
        authorized = []
        skipped = []
        for p in all_profiles:
            status = p.get("authorization_status", "confirmed")
            if memory_status.get("paused"):
                skipped.append({"profile": p, "reason": "记忆已暂停"})
            elif status in ("revoked", "denied"):
                skipped.append({"profile": p, "reason": f"画像未授权（{status}）"})
            else:
                authorized.append(p)
        return authorized, skipped

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

    def _memory_state_path(self, user_id: str) -> Path:
        return self.storage_dir / f"{user_id}_memory.json"

    def _audit_log_path(self, user_id: str) -> Path:
        return self.storage_dir / f"{user_id}_audit.jsonl"

    def _write_user(self, user_id: str, profiles: list[dict]):
        path = self._user_path(user_id)
        path.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _write_audit_entry(self, user_id: str, entry: dict):
        entry["id"] = uuid.uuid4().hex[:12]
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        path = self._audit_log_path(user_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
