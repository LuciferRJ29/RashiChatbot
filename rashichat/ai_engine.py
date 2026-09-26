import os
import asyncio
import logging
import uuid
import random
from typing import Optional, Dict, Any, List
import httpx
import config

logger = logging.getLogger("rashi_ai_engine")

RASHI_PERSONA = (
    "Act as Rashi, a sweet, smart and friendly Indian girl chatting with friends on Telegram. "
    "Reply naturally in Hinglish/Hindi/English mix like a real person. "
    "Keep replies short, warm and charming (1-2 sentences max). "
)

FALLBACK_REPLIES = [
    "Haan bolo na! Me sun rahi hoon 😊",
    "Arey haan! Batao kya haal chal hai? ✨",
    "Suno na, thoda network slow chal raha hai lagta hai! 💖",
    "Hehe, bolo bolo! Me yahi hoon 💕",
    "Aap batao, aaj ka din kaisa chal raha hai? 🌸",
]

class RashiAIEngine:
    """
    Rashi AI Engine with multi-tier fallback:
    1. External RashiChatbot-API (config.API)
    2. Direct Groq API (if GROQ_API_KEY set)
    3. Direct Google Gemini API (if GEMINI_API_KEY set)
    4. Direct free-ai-online.com scraper (fallback)
    5. Charming default Hinglish response (so bot never fails silently)
    """

    def __init__(self):
        self.session_id: Optional[str] = None
        self.rest_nonce: Optional[str] = None
        self.lock = asyncio.Lock()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Referer": "https://www.free-ai-online.com/free-ai-no-login-unlimited/",
            "Origin": "https://www.free-ai-online.com",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(connect=10.0, read=25.0, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=15, max_connections=30),
            )
        return self.client

    # ── Tier 1: Groq Direct ──
    async def _ask_groq(self, prompt: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key:
            return None
        try:
            client = self._get_client()
            messages = [{"role": "system", "content": RASHI_PERSONA}]
            if history:
                for u, b in history[-4:]:
                    messages.append({"role": "user", "content": u})
                    messages.append({"role": "assistant", "content": b})
            messages.append({"role": "user", "content": prompt})

            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7, "max_tokens": 150},
                timeout=12.0
            )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.debug(f"Groq direct error: {e}")
        return None

    # ── Tier 2: Gemini Direct ──
    async def _ask_gemini(self, prompt: str) -> Optional[str]:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if not gemini_key:
            return None
        try:
            client = self._get_client()
            r = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                headers={"Authorization": f"Bearer {gemini_key}", "Content-Type": "application/json"},
                json={
                    "model": "gemini-2.0-flash",
                    "messages": [{"role": "system", "content": RASHI_PERSONA}, {"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=12.0
            )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.debug(f"Gemini direct error: {e}")
        return None

    # ── Tier 3: Scraper ──
    async def _ask_direct_scraper(self, prompt: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        try:
            client = self._get_client()
            async with self.lock:
                if not (self.session_id and self.rest_nonce):
                    r = await client.post("https://www.free-ai-online.com/wp-json/mwai/v1/start_session", headers=self.headers, timeout=10.0)
                    if r.status_code == 200:
                        d = r.json()
                        self.session_id = d.get("sessionId")
                        self.rest_nonce = d.get("restNonce")
                    else:
                        return None

            payload = {
                "botId": "default",
                "customId": None,
                "session": self.session_id,
                "chatId": str(uuid.uuid4())[:8],
                "contextId": 2121,
                "messages": [],
                "newMessage": f"{RASHI_PERSONA}\n\nUser: {prompt}",
                "stream": False,
            }
            req_headers = self.headers.copy()
            req_headers["X-WP-Nonce"] = self.rest_nonce

            r = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=20.0)
            if r.status_code == 200:
                d = r.json()
                if d.get("success"):
                    return d.get("reply", "").strip()
        except Exception:
            pass
        return None

    # ── Main Ask Method ──
    async def ask(self, prompt: str, history: List[tuple[str, str]] = None) -> str:
        client = self._get_client()

        # 1. Try external API if configured & not localhost default
        api_endpoint = config.API
        if api_endpoint and api_endpoint.startswith("http") and "localhost" not in api_endpoint:
            try:
                if "query=" in api_endpoint:
                    api_url = api_endpoint + httpx.URL(api_endpoint).params.get("query", "") + prompt
                    r = await client.get(api_url, timeout=12.0)
                else:
                    r = await client.post(
                        api_endpoint,
                        json={"prompt": prompt, "system_prompt": RASHI_PERSONA},
                        timeout=15.0,
                    )
                if r.status_code == 200:
                    res_data = r.json()
                    reply = res_data.get("reply") or res_data.get("data")
                    if reply:
                        return reply.strip()
            except Exception as e:
                logger.debug(f"External API check skipped/failed: {e}")

        # 2. Try Groq direct
        groq_reply = await self._ask_groq(prompt, history)
        if groq_reply:
            return groq_reply

        # 3. Try Gemini direct
        gemini_reply = await self._ask_gemini(prompt)
        if gemini_reply:
            return gemini_reply

        # 4. Try scraper direct
        scraper_reply = await self._ask_direct_scraper(prompt, history)
        if scraper_reply:
            return scraper_reply

        # 5. Friendly human fallback
        return random.choice(FALLBACK_REPLIES)

ai_engine = RashiAIEngine()
