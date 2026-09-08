import logging
from collections import defaultdict
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
import config

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None
        self._init_client()
        # 内存中保存每个 chat_id 的历史对话：[{"role": "user"|"assistant", "content": "..."}]
        self.histories = defaultdict(list)

    def _init_client(self):
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY 未配置，AI 请求将无法正常调用。")
            return
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        )

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
        """向 AI 发送提问并返回回答（带上下文记忆）"""
        if not self.client:
            self._init_client()
            if not self.client:
                return "❌ 尚未配置 OPENAI_API_KEY，请在 .env 文件中配置后重启 Bot。"

        # 构建本轮消息列表
        messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
        # 加入历史对话
        messages.extend(self.histories[chat_id])
        # 加入当前用户提问
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=config.MODEL_NAME,
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
            logger.error("API Key 无效或未授权。")
            return "❌ API Key 无效或未授权，请检查 .env 中的 OPENAI_API_KEY 与 OPENAI_BASE_URL。"
        except RateLimitError:
            logger.error("API 额度超限或请求频次过高。")
            return "⚠️ API 额度已用尽或请求过于频繁，请稍后再试。"
        except APIError as e:
            logger.error(f"API 调用出错: {e}")
            return f"❌ AI 服务返回错误: {e.message if hasattr(e, 'message') else str(e)}"
        except Exception as e:
            logger.exception("未知错误")
            return f"❌ 处理请求时出现异常: {str(e)}"

# 单例实例
ai_service = AIService()
