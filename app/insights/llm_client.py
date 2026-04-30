"""
LLM 客户端 — DeepSeek 接入层
支持真实 API 调用，失败时自动降级到 fallback
"""

import os
import json
import ssl
import urllib.request
import urllib.error
import logging
from typing import Optional
from flask import current_app

# macOS / 自签证书兼容：优先用 certifi，否则跳过验证
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Fallback（API 不可用时保底）
# ──────────────────────────────────────────────
FALLBACK_INSIGHTS = {
    'daily': {
        'happy': "You're experiencing positive emotions today! Keep fostering the things that bring you joy. Share this positivity with those around you.",
        'calm': "Your calm state shows good emotional balance. Continue with activities that help you maintain this peace.",
        'anxious': "Anxiety is present today, but it's temporary. Try to identify what's causing it and break it into smaller steps. Consider the breathing exercises.",
        'sad': "You're feeling down today, which is okay. Reach out to someone you trust, and remember this feeling will pass.",
        'angry': "Anger is showing up today. Take time to understand the trigger, then reflect when calmer.",
        'neutral': "You're in a stable baseline today — a great time to focus on activities that feel meaningful.",
    },
    'suggestions': {
        'happy': ["Share your joy with others", "Document this positive moment", "Engage in activities you love"],
        'calm': ["Maintain your peace with mindfulness", "Continue healthy routines", "Spread calm to those around you"],
        'anxious': ["Practice breathing exercises", "Break tasks into smaller steps", "Reach out for support"],
        'sad': ["Be kind to yourself", "Connect with support systems", "Engage in self-care"],
        'angry': ["Take a break and cool down", "Journal your feelings", "Channel energy into constructive activity"],
        'neutral': ["Explore new interests", "Reflect on your day", "Plan something enjoyable"],
    },
    'tasks': {
        'happy': "Share your happiness with one person today",
        'calm': "Meditate or practice deep breathing for 5 minutes",
        'anxious': "Write down 3 small tasks you can accomplish today",
        'sad': "Do one thing that brings you comfort today",
        'angry': "Take a 10-minute walk to cool down",
        'neutral': "Try one new positive thing today",
    }
}


# ──────────────────────────────────────────────
# Prompt 模板
# ──────────────────────────────────────────────
DAILY_PROMPT = """\
You are MindTrace, a compassionate mental wellness coach.

A user has just logged their mood check-in. Your response MUST be specifically tailored to
the actual content of their journal entry — not just their mood label. Reference concrete
details, situations, or feelings they mentioned. Never give generic advice that could apply
to anyone feeling this mood. Every suggestion should directly address something in their journal.

Mood: {mood_type}
Intensity: {intensity}/10
Journal entry: "{journal}"
NLP sentiment: {sentiment}
Detected emotions: {emotions}
Keywords: {keywords}

Requirements:
- insight: 2-3 sentences that acknowledge the specific situation described in the journal
- suggestions: 3 concrete, personalised action tips that relate to the journal content
- small_task: one very specific micro-task tied to what they wrote (not generic)

Respond in STRICT JSON format (no markdown, no extra text):
{{
  "insight": "<empathetic insight that references their specific journal content>",
  "suggestions": ["<specific tip 1 tied to journal>", "<specific tip 2 tied to journal>", "<specific tip 3 tied to journal>"],
  "small_task": "<one concrete micro-task directly related to their situation>"
}}"""

WEEKLY_PROMPT = """\
You are MindTrace, a compassionate mental wellness coach.

Here is the user's mood data for the past 7 days:
{entries_summary}

Mood distribution: {mood_counts}
Average intensity: {avg_intensity}/10

Write a warm weekly reflection in STRICT JSON format (no markdown, no extra text):
{{
  "insight": "<3-4 sentence weekly reflection that acknowledges patterns and encourages growth>",
  "highlights": ["<positive observation>", "<growth area>", "<encouragement for next week>"]
}}"""


# ──────────────────────────────────────────────
# 核心客户端
# ──────────────────────────────────────────────
class DeepSeekClient:
    """DeepSeek API 客户端（OpenAI 兼容格式）"""

    BASE_URL = "https://api.deepseek.com/chat/completions"
    MODEL = "deepseek-chat"
    TIMEOUT = 30

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _chat(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        """发起一次 chat 请求，返回 assistant 文本内容"""
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 1.0,  # 提高随机性，避免相同情绪每次给相同建议
        }
        req = urllib.request.Request(
            self.BASE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.TIMEOUT, context=_SSL_CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error("DeepSeek HTTPError %s: %s", e.code, body)
        except urllib.error.URLError as e:
            logger.error("DeepSeek URLError: %s", e.reason)
        except Exception as e:
            logger.error("DeepSeek unexpected error: %s", e)
        return None

    def _parse_json(self, text: str) -> Optional[dict]:
        """从 LLM 返回文本中提取 JSON"""
        if not text:
            return None
        # 去掉可能的 markdown code fence
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到第一个 { ... } 块
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        logger.warning("Could not parse LLM JSON response: %s", text[:200])
        return None


# ──────────────────────────────────────────────
# 高层接口（与 Flask 应用层解耦）
# ──────────────────────────────────────────────
class LLMClient:
    """Flask 应用使用的高层 LLM 客户端"""

    def __init__(self):
        self.api_key = current_app.config.get("LLM_API_KEY", "")
        self._client = DeepSeekClient(self.api_key) if self.api_key else None
        self._daily_cache: dict = {}   # 实例级别缓存，每次请求生命周期内去重

    # ── 每日洞察 ─────────────────────────────
    def generate_daily_insight(self, mood_entry) -> str:
        if self._client:
            result = self._call_daily(mood_entry)
            if result:
                return result.get("insight") or self._fallback_insight(mood_entry)
        return self._fallback_insight(mood_entry)

    def generate_suggestions(self, mood_entry) -> list:
        if self._client:
            result = self._call_daily(mood_entry)
            if result:
                return result.get("suggestions") or self._fallback_suggestions(mood_entry)
        return self._fallback_suggestions(mood_entry)

    def generate_small_task(self, mood_entry) -> str:
        if self._client:
            result = self._call_daily(mood_entry)
            if result:
                return result.get("small_task") or self._fallback_task(mood_entry)
        return self._fallback_task(mood_entry)

    # ── 周报告 ───────────────────────────────
    def generate_weekly_summary(self, entries) -> str:
        if not entries:
            return "No entries this week."
        if self._client:
            result = self._call_weekly(entries)
            if result:
                return result.get("insight") or self._fallback_weekly(entries)
        return self._fallback_weekly(entries)

    # ── 内部调用（同一请求内避免重复 API 调用）────────
    def _call_daily(self, mood_entry) -> Optional[dict]:
        cache_key = mood_entry.id
        if cache_key in self._daily_cache:
            return self._daily_cache[cache_key]

        prompt = DAILY_PROMPT.format(
            mood_type=mood_entry.mood_type,
            intensity=mood_entry.intensity,
            journal=mood_entry.journal_text or "(no journal entry)",
            sentiment=mood_entry.sentiment_label or "unknown",
            emotions=", ".join(mood_entry.get_emotion_labels()) if hasattr(mood_entry, "get_emotion_labels") else "",
            keywords=", ".join(mood_entry.get_keywords()) if hasattr(mood_entry, "get_keywords") else "",
        )
        raw = self._client._chat(prompt, max_tokens=400)
        parsed = self._client._parse_json(raw)
        if parsed:
            self._daily_cache[cache_key] = parsed
        return parsed

    def _call_weekly(self, entries) -> Optional[dict]:
        mood_counts: dict = {}
        summaries = []
        total_intensity = 0
        for e in entries:
            mood_counts[e.mood_type] = mood_counts.get(e.mood_type, 0) + 1
            total_intensity += e.intensity
            summaries.append(
                f"- {e.date}: {e.mood_type} (intensity {e.intensity}) — {(e.journal_text or '')[:80]}"
            )
        avg = total_intensity / len(entries) if entries else 0
        prompt = WEEKLY_PROMPT.format(
            entries_summary="\n".join(summaries),
            mood_counts=json.dumps(mood_counts),
            avg_intensity=f"{avg:.1f}",
        )
        raw = self._client._chat(prompt, max_tokens=500)
        return self._client._parse_json(raw)

    # ── Fallback helpers ─────────────────────
    def _fallback_insight(self, entry) -> str:
        return FALLBACK_INSIGHTS["daily"].get(
            entry.mood_type,
            f"Today you're feeling {entry.mood_type}. Take care of yourself — all emotions are valid and temporary."
        )

    def _fallback_suggestions(self, entry) -> list:
        return FALLBACK_INSIGHTS["suggestions"].get(entry.mood_type, [])

    def _fallback_task(self, entry) -> str:
        return FALLBACK_INSIGHTS["tasks"].get(entry.mood_type, "Take care of yourself today")

    def _fallback_weekly(self, entries) -> str:
        mood_counts: dict = {}
        for e in entries:
            mood_counts[e.mood_type] = mood_counts.get(e.mood_type, 0) + 1
        most_common = max(mood_counts, key=mood_counts.get) if mood_counts else "neutral"
        avg = sum(e.intensity for e in entries) / len(entries) if entries else 5
        return (
            f"This week, your dominant mood was **{most_common}** with an average intensity of "
            f"{avg:.1f}/10. Keep tracking your emotions — awareness is the first step to growth."
        )


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端实例（在 Flask 应用上下文中调用）"""
    return LLMClient()
