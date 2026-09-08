import asyncio
import json
import logging
import os
import re
from typing import Dict, Optional, Any
import config

logger = logging.getLogger(__name__)

SESSION_FILE = os.path.join(os.path.dirname(__file__), "sessions.json")

class AgyEngine:
    def __init__(self):
        self.conversations: Dict[int, str] = {}
        self.modes: Dict[int, str] = {}
        self._load_sessions()

    def _load_sessions(self):
        """从本地文件恢复 session 与 mode 映射关系"""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 兼容新旧格式
                    if "conversations" in data:
                        self.conversations = {int(k): v for k, v in data.get("conversations", {}).items()}
                        self.modes = {int(k): v for k, v in data.get("modes", {}).items()}
                    else:
                        self.conversations = {int(k): v for k, v in data.items()}
                        self.modes = {}
                logger.info(f"已恢复 {len(self.conversations)} 个用户的会话记忆。")
            except Exception as e:
                logger.error(f"加载 sessions.json 失败: {e}")
                self.conversations = {}
                self.modes = {}

    def _save_sessions(self):
        """持久化保存会话与模式映射"""
        try:
            payload = {
                "conversations": self.conversations,
                "modes": self.modes
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 sessions.json 失败: {e}")

    def clear(self, chat_id: int) -> bool:
        """重置指定 chat_id 的会话"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]
            self._save_sessions()
            return True
        return False

    def get_conversation_id(self, chat_id: int) -> Optional[str]:
        return self.conversations.get(chat_id)

    def get_mode(self, chat_id: int) -> str:
        """获取用户当前的运行模式，默认为全局配置的 AGENT_MODE"""
        return self.modes.get(chat_id, config.AGENT_MODE)

    def set_mode(self, chat_id: int, mode: str) -> bool:
        """设置用户的运行模式 (chat 或 agent)"""
        mode = mode.lower().strip()
        if mode in ("chat", "agent"):
            self.modes[chat_id] = mode
            self._save_sessions()
            logger.info(f"chat_id={chat_id} 切换模式为: {mode}")
            return True
        return False

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """从进程输出中提取 JSON 数据"""
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        matches = re.findall(r'(\{[\s\S]*\})', text)
        for candidate in reversed(matches):
            try:
                return json.loads(candidate)
            except Exception:
                continue
        return None

    async def ask(self, chat_id: int, prompt: str) -> Dict[str, Any]:
        """调用 agy CLI 执行提问并返回结构化结果"""
        conv_id = self.conversations.get(chat_id)
        current_mode = self.get_mode(chat_id)

        cmd = [
            config.AGY_BIN_PATH,
            "-p", prompt,
            "--model", config.MODEL_NAME,
            "--output-format", "json"
        ]

        if conv_id:
            cmd.extend(["--conversation", conv_id])

        # 如果当前用户处于 agent 模式，开启全功能宿主机操作权
        if current_mode == "agent":
            cmd.append("--dangerously-skip-permissions")

        logger.info(f"正在调用 agy (chat_id={chat_id}, conv_id={conv_id}, mode={current_mode})")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return {
                    "ok": False,
                    "error": f"⏳ 请求超时（超过 {config.TIMEOUT_SECONDS} 秒），已终止该操作。"
                }

            stdout_str = stdout_data.decode("utf-8", errors="replace")
            stderr_str = stderr_data.decode("utf-8", errors="replace")

            if process.returncode != 0:
                logger.error(f"agy 执行失败 (code={process.returncode}):\nSTDOUT: {stdout_str}\nSTDERR: {stderr_str}")
                if "not found" in stderr_str or "not found" in stdout_str:
                    logger.warning("检测到会话失效，自动清理并提示重试...")
                    self.clear(chat_id)
                    return {
                        "ok": False,
                        "error": "⚠️ 上一条历史会话已在服务端过期，已自动为你重置会话，请重新发送你的消息！"
                    }
                return {
                    "ok": False,
                    "error": f"❌ agy 执行出错 (code {process.returncode}): {stderr_str or stdout_str}"
                }

            data = self._extract_json(stdout_str)
            if not data:
                logger.warning(f"未能解析出 JSON，原始输出: {stdout_str}")
                response_text = stdout_str.strip() or stderr_str.strip()
                return {
                    "ok": True,
                    "response": response_text or "（无输出返回）",
                    "conversation_id": None
                }

            response_text = data.get("response", "").strip()
            new_conv_id = data.get("conversation_id")

            if new_conv_id:
                self.conversations[chat_id] = new_conv_id
                self._save_sessions()

            duration = data.get("duration_seconds", 0)
            usage = data.get("usage", {})

            return {
                "ok": True,
                "response": response_text,
                "conversation_id": new_conv_id,
                "duration": duration,
                "usage": usage,
                "mode": current_mode
            }

        except Exception as e:
            logger.exception(f"调用 agy 时抛出未捕获异常: {e}")
            return {
                "ok": False,
                "error": f"❌ 内部调用发生异常: {str(e)}"
            }

# 单例实例
agy_engine = AgyEngine()
