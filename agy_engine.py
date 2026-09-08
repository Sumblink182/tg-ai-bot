import asyncio
from collections import defaultdict
import json
import logging
import os
import re
from typing import Dict, Optional, Any
import config

logger = logging.getLogger(__name__)

SESSION_FILE = os.path.join(os.path.dirname(__file__), "sessions.json")

# 精确匹配 agy 会话失效的警告/错误模式（避免把用户正常输出中的 "not found" 误判为会话失效）
CONVERSATION_EXPIRED_PATTERN = re.compile(
    r'(?:warning:\s+)?conversation\s+["\']?[a-zA-Z0-9_-]+["\']?\s+(?:not\s+found|expired|invalid)',
    re.IGNORECASE
)

class AgyEngine:
    def __init__(self):
        self.conversations: Dict[int, str] = {}
        self.modes: Dict[int, str] = {}
        # 活跃子进程字典: chat_id -> Process
        self.active_processes: Dict[int, asyncio.subprocess.Process] = {}
        # Per-chat 独占锁，防止同一用户并发发送导致会话错乱和竞态
        self._chat_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        # 全局最大并发信号量，防止高并发打爆 VPS 内存与 CPU
        self._global_semaphore = asyncio.Semaphore(max(1, config.MAX_CONCURRENT_TASKS))
        self._load_sessions()

    def _load_sessions(self):
        """从本地文件恢复 session 与 mode 映射关系"""
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
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

    def is_chat_busy(self, chat_id: int) -> bool:
        """检查该 chat 当前是否有任务正在执行"""
        return self._chat_locks[chat_id].locked()

    def cancel_task(self, chat_id: int) -> bool:
        """强制终止指定 chat 正在运行的 agy 任务"""
        proc = self.active_processes.get(chat_id)
        if proc and proc.returncode is None:
            logger.info(f"正在终止 chat_id={chat_id} 的活跃进程 (PID: {proc.pid})")
            try:
                proc.terminate()
                return True
            except Exception as e:
                logger.error(f"终止进程失败: {e}")
                try:
                    proc.kill()
                    return True
                except Exception:
                    pass
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

    async def _run_agy_process(self, chat_id: int, prompt: str, conv_id: Optional[str], current_mode: str) -> tuple[int, str, str]:
        """封装底层 agy CLI 执行与超时/取消处理"""
        cmd = [
            config.AGY_BIN_PATH,
            "-p", prompt,
            "--model", config.MODEL_NAME,
            "--output-format", "json"
        ]

        if conv_id:
            cmd.extend(["--conversation", conv_id])

        if current_mode == "agent":
            cmd.append("--dangerously-skip-permissions")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.active_processes[chat_id] = process

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=config.TIMEOUT_SECONDS
            )
            stdout_str = stdout_data.decode("utf-8", errors="replace")
            stderr_str = stderr_data.decode("utf-8", errors="replace")
            return process.returncode or 0, stdout_str, stderr_str
        finally:
            self.active_processes.pop(chat_id, None)

    async def ask(self, chat_id: int, prompt: str) -> Dict[str, Any]:
        """调用 agy CLI 执行提问，内置 per-chat 锁、全局并发限额与会话自愈机制"""
        if not os.path.exists(config.AGY_BIN_PATH):
            return {
                "ok": False,
                "error": f"❌ 未找到 Antigravity CLI 二进制文件 ({config.AGY_BIN_PATH})"
            }

        async with self._chat_locks[chat_id]:
            async with self._global_semaphore:
                return await self._ask_locked(chat_id, prompt)

    async def _ask_locked(self, chat_id: int, prompt: str) -> Dict[str, Any]:
        """在持有锁的前提下执行调用，支持一次会话失效自动自愈重试"""
        conv_id = self.conversations.get(chat_id)
        current_mode = self.get_mode(chat_id)

        logger.info(f"正在调用 agy (chat_id={chat_id}, conv_id={conv_id}, mode={current_mode})")

        try:
            returncode, stdout_str, stderr_str = await self._run_agy_process(
                chat_id=chat_id,
                prompt=prompt,
                conv_id=conv_id,
                current_mode=current_mode
            )
        except asyncio.TimeoutError:
            self.cancel_task(chat_id)
            return {
                "ok": False,
                "error": f"⏳ 请求超时（超过 {config.TIMEOUT_SECONDS} 秒），已终止该操作。"
            }
        except asyncio.CancelledError:
            self.cancel_task(chat_id)
            return {
                "ok": False,
                "error": "🛑 任务已被用户主动取消。"
            }
        except Exception as e:
            logger.exception(f"调用 agy 时抛出未捕获异常: {e}")
            return {
                "ok": False,
                "error": f"❌ 内部调用发生异常: {str(e)}"
            }

        # 检查是否为会话过期
        if conv_id and CONVERSATION_EXPIRED_PATTERN.search(stderr_str):
            logger.warning(f"检测到 chat_id={chat_id} 历史会话 {conv_id} 已过期失效，自动重置并自愈重试...")
            self.clear(chat_id)
            try:
                # 重新作为新会话发起调用
                returncode, stdout_str, stderr_str = await self._run_agy_process(
                    chat_id=chat_id,
                    prompt=prompt,
                    conv_id=None,
                    current_mode=current_mode
                )
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"❌ 自愈重试失败: {str(e)}"
                }

        if returncode != 0:
            logger.error(f"agy 执行失败 (code={returncode}):\nSTDOUT: {stdout_str}\nSTDERR: {stderr_str}")
            return {
                "ok": False,
                "error": f"❌ agy 执行出错 (code {returncode}): {stderr_str.strip() or stdout_str.strip()}"
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

# 单例实例
agy_engine = AgyEngine()

