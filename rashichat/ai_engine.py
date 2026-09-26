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
    Rashi AI Engine with Tiger Protect cookie handshake:
    1. External RashiChatbot-API (config.API)
    2. Direct Tiger Protect scraper (free-ai-online.com Groq/ChatGPT)
    3. Direct Groq API (if GROQ_API_KEY set)
    4. Direct Google Gemini API (if GEMINI_API_KEY set)
    5. Charming human fallback (never silent)
    """

    def __init__(self):
        self.session_id: Optional[str] = None
        self.rest_nonce: Optional[str] = None
        self.cookies: Dict[str, str] = {}
        self.lock = asyncio.Lock()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.free-ai-online.com/grok-4-free/",
            "Origin": "https://www.free-ai-online.com",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        self.client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(connect=10.0, read=35.0, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=15, max_connections=30),
            )
        return self.client

    def _update_cookies(self, resp: httpx.Response):
        try:
            for part in resp.headers.get_list("set-cookie"):
                pair = part.split(";")[0].strip()
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    self.cookies[k.strip()] = v.strip()
        except Exception:
            pass

    def _get_cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    async def _init_tiger_session(self, client: httpx.AsyncClient, force: bool = False):
        async with self.lock:
            if not force and self.session_id and self.rest_nonce and self.cookies:
                return self.session_id, self.rest_nonce

            headers = self.headers.copy()
            if self.cookies:
                headers["Cookie"] = self._get_cookie_header()

            try:
                resp = await client.post("https://www.free-ai-online.com/wp-json/mwai/v1/start_session", json={}, headers=headers, timeout=15.0)
                self._update_cookies(resp)

                if resp.status_code == 307:
                    headers["Cookie"] = self._get_cookie_header()
                    resp = await client.post("https://www.free-ai-online.com/wp-json/mwai/v1/start_session", json={}, headers=headers, timeout=15.0)
                    self._update_cookies(resp)

                if resp.status_code == 200:
                    d = resp.json()
                    self.session_id = d.get("sessionId")
                    self.rest_nonce = d.get("restNonce") or d.get("new_token")
                    return self.session_id, self.rest_nonce
            except Exception as e:
                logger.debug(f"Tiger Protect init exception: {e}")
            return None, None

    # ── Tier 1: Direct Tiger Protect Scraper (Grok 4) ──
    async def _ask_tiger_scraper(self, prompt: str) -> Optional[str]:
        try:
            client = self._get_client()
            session_id, rest_nonce = await self._init_tiger_session(client)
            if not (session_id and rest_nonce):
                return None

            payload = {
                "botId": "Grok 4 free",
                "customId": None,
                "session": session_id,
                "chatId": f"rashi_{uuid.uuid4().hex[:8]}",
                "contextId": 25,
                "messages": [],
                "newMessage": f"[Instruction: {RASHI_PERSONA}]\n\n{prompt}",
                "stream": False,
            }
            req_headers = self.headers.copy()
            req_headers["X-WP-Nonce"] = rest_nonce
            if self.cookies:
                req_headers["Cookie"] = self._get_cookie_header()

            resp = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=30.0)
            self._update_cookies(resp)

            if resp.status_code == 307:
                req_headers["Cookie"] = self._get_cookie_header()
                resp = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=30.0)
                self._update_cookies(resp)

            if resp.status_code in [401, 403, 500] or (resp.status_code == 200 and not resp.json().get("success", True)):
                session_id, rest_nonce = await self._init_tiger_session(client, force=True)
                if session_id and rest_nonce:
                    payload["session"] = session_id
                    req_headers["X-WP-Nonce"] = rest_nonce
                    req_headers["Cookie"] = self._get_cookie_header()
                    resp = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=30.0)
                    self._update_cookies(resp)

            if resp.status_code == 200:
                d = resp.json()
                if d.get("success"):
                    reply = d.get("reply", "").strip()
                    if reply:
                        return reply
        except Exception as ex:
            logger.debug(f"Tiger scraper error: {ex}")
        return None

    # ── Tier 2: Groq Direct (if set) ──
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
                    r = await client.get(api_url, timeout=15.0)
                else:
                    r = await client.post(
                        api_endpoint,
                        json={"prompt": prompt, "system_prompt": RASHI_PERSONA},
                        timeout=20.0,
                    )
                if r.status_code == 200:
                    res_data = r.json()
                    reply = res_data.get("reply") or res_data.get("data")
                    if reply:
                        return reply.strip()
            except Exception as e:
                logger.debug(f"External API check skipped/failed: {e}")

        # 2. Try Tiger Protect Scraper (free-ai-online.com)
        tiger_reply = await self._ask_tiger_scraper(prompt)
        if tiger_reply:
            return tiger_reply

        # 3. Try Groq direct (if key set)
        groq_reply = await self._ask_groq(prompt, history)
        if groq_reply:
            return groq_reply

        # 4. Friendly human fallback
        return random.choice(FALLBACK_REPLIES)

ai_engine = RashiAIEngine()
