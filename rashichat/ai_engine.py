import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, List
import httpx
import config

logger = logging.getLogger("rashi_ai_engine")

RASHI_PERSONA = (
    "Act as Rashi, a sweet, smart and friendly Indian girl chatting with friends on Telegram. "
    "Reply naturally in Hinglish/Hindi/English mix like a real person. "
    "Keep replies short, warm and charming (1-2 sentences max). "
)

class RashiAIEngine:
    """
    Rashi AI Engine:
    1. Tries querying configured external RashiChatbot-API endpoint (config.API).
    2. If external API is unreachable, directly falls back to built-in free-ai-online.com scraper.
    """
    BASE_URL = "https://www.free-ai-online.com"
    START_URL = f"{BASE_URL}/wp-json/mwai/v1/start_session"
    SUBMIT_URL = f"{BASE_URL}/wp-json/mwai-ui/v1/chats/submit"

    def __init__(self):
        self.session_id: Optional[str] = None
        self.rest_nonce: Optional[str] = None
        self.lock = asyncio.Lock()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": f"{self.BASE_URL}/free-ai-no-login-unlimited/",
            "Origin": self.BASE_URL,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=15, max_connections=30),
            )
        return self.client

    async def _init_scraper_session(self, force: bool = False):
        async with self.lock:
            if not force and self.session_id and self.rest_nonce:
                return self.session_id, self.rest_nonce

            client = self._get_client()
            r = await client.post(self.START_URL, headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                self.session_id = data.get("sessionId")
                self.rest_nonce = data.get("restNonce")
                return self.session_id, self.rest_nonce
            raise RuntimeError(f"Free-AI-Online session failed: {r.status_code}")

    async def _ask_direct_scraper(self, prompt: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        client = self._get_client()
        session_id, rest_nonce = await self._init_scraper_session()

        formatted_messages = []
        if history:
            for user_msg, bot_msg in history[-6:]:
                formatted_messages.append({"role": "user", "content": user_msg})
                formatted_messages.append({"role": "assistant", "content": bot_msg})

        full_prompt = f"{RASHI_PERSONA}\n\nUser: {prompt}"

        payload = {
            "botId": "default",
            "customId": None,
            "session": session_id,
            "chatId": str(uuid.uuid4())[:8],
            "contextId": 2121,
            "messages": formatted_messages,
            "newMessage": full_prompt,
            "stream": False,
        }

        req_headers = self.headers.copy()
        req_headers["X-WP-Nonce"] = rest_nonce

        r = await client.post(self.SUBMIT_URL, headers=req_headers, json=payload)
        if r.status_code in [401, 403]:
            session_id, rest_nonce = await self._init_scraper_session(force=True)
            payload["session"] = session_id
            req_headers["X-WP-Nonce"] = rest_nonce
            r = await client.post(self.SUBMIT_URL, headers=req_headers, json=payload)

        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data.get("reply", "").strip()
        return None

    async def ask(self, prompt: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        """
        Unified AI generation method:
        1. Tries config.API (if configured & accessible)
        2. Falls back to direct free-ai-online scraping engine
        """
        client = self._get_client()

        # 1. Try external API if configured
        if config.API and config.API.startswith("http"):
            try:
                # If API endpoint is a query-based URL e.g. "http://localhost:8000/api/chat?query="
                if "query=" in config.API:
                    api_url = config.API + httpx.URL(config.API).params.get("query", "") + prompt
                    r = await client.get(api_url, timeout=12.0)
                else:
                    r = await client.post(
                        config.API,
                        json={"prompt": prompt, "system_prompt": RASHI_PERSONA},
                        timeout=15.0,
                    )

                if r.status_code == 200:
                    res_data = r.json()
                    reply = res_data.get("reply") or res_data.get("data")
                    if reply:
                        return reply.strip()
            except Exception as e:
                logger.debug(f"External API check skipped/failed ({e}), falling back to direct scraper...")

        # 2. Direct free-ai-online scraper engine
        try:
            return await self._ask_direct_scraper(prompt, history=history)
        except Exception as ex:
            logger.error(f"Direct scraper error: {ex}")
            return None


ai_engine = RashiAIEngine()
