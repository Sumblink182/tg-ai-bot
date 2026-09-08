import logging
from collections import defaultdict
from typing import Optional
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
import config

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self._init_client()
        # 内存中保存每个 chat_id 的历史对话：[{"role": "user"|"assistant", "content": "..."}]
        self.histories = defaultdict(list)

    def _init_client(self):
        if not config.OPENAI_API_KEY:
            self.client = None
            return
        try:
            self.client = AsyncOpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
            logger.info(f"OpenAI 兼容备用 AI 引擎初始化成功 (模型: {config.FALLBACK_MODEL})")
        except Exception as e:
            logger.error(f"初始化 OpenAI 客户端失败: {e}")
            self.client = None

    def is_available(self) -> bool:
        """检查备用 AI 服务是否已配置且可用"""
        return bool(config.ENABLE_FALLBACK and config.OPENAI_API_KEY and self.client)

    def reload_client(self):
        """重新读取配置并初始化 client"""
        self._init_client()

    def clear_history(self, chat_id: int) -> int:
        """清空指定 chat_id 的对话历史，返回清空的条数"""
        count = len(self.histories[chat_id])
        self.histories[chat_id] = []
        return count

    def get_history_count(self, chat_id: int) -> int:
        """获取当前上下文中的消息条数"""
        return len(self.histories.get(chat_id, []))

    async def ask_ai(self, chat_id: int, prompt: str) -> str:
        """向备用 AI 发送提问并返回回答（带上下文记忆）"""
        if not self.is_available():
            if not self.client and config.OPENAI_API_KEY:
                self._init_client()
            if not self.is_available():
                return "❌ 尚未配置有效的 OPENAI_API_KEY，备用 AI 兜底不可用。"

        # 构建本轮消息列表
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        # 加入历史对话
        messages.extend(self.histories[chat_id])
        # 加入当前用户提问
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=config.FALLBACK_MODEL,
                messages=messages
            )
            reply = response.choices[0].message.content or ""
            reply = reply.strip()

            if not reply:
                reply = "（模型返回了空消息）"

            # 成功后写入上下文历史
            self.histories[chat_id].append({"role": "user", "content": prompt})
            self.histories[chat_id].append({"role": "assistant", "content": reply})

            # 滑动窗口截断：保留最近 MAX_HISTORY_ROUNDS 轮（一轮 = 1条user + 1条assistant）
            max_messages = config.MAX_HISTORY_ROUNDS * 2
            if len(self.histories[chat_id]) > max_messages:
                self.histories[chat_id] = self.histories[chat_id][-max_messages:]

            return reply

        except AuthenticationError:
            logger.error("备用 API Key 无效或未授权。")
            return "❌ 备用 API Key 无效或未授权，请检查 .env 中的 OPENAI_API_KEY 与 OPENAI_BASE_URL。"
        except RateLimitError:
            logger.error("备用 API 额度超限或请求频次过高。")
            return "⚠️ 备用 API 额度已用尽或请求过于频繁，请稍后再试。"
        except APIError as e:
            logger.error(f"备用 API 调用出错: {e}")
            return f"❌ 备用 AI 服务返回错误: {getattr(e, 'message', str(e))}"
        except Exception as e:
            logger.exception("备用 AI 发生未捕获异常")
            return f"❌ 备用 AI 处理请求时出现异常: {str(e)}"

# 单例实例
ai_service = AIService()

