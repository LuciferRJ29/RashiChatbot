import os
import asyncio
import logging
import uuid
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import config

import socket
try:
    from curl_cffi import curl
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    curl = None

import httpx

logger = logging.getLogger("rashi_ai_engine")

def get_curl_resolve_opts() -> dict:
    if not HAS_CURL_CFFI or not curl:
        return {}
    host1 = "www.free-ai-online.com"
    host2 = "free-ai-online.com"
    try:
        ip = socket.gethostbyname(host1)
    except Exception:
        ip = "109.234.167.117"
    return {curl.CurlOpt.RESOLVE: [f"{host1}:443:{ip}", f"{host2}:443:{ip}"]}

IST = timezone(timedelta(hours=5, minutes=30))

BASE_URL = "https://www.free-ai-online.com"
START_SESSION_URL = f"{BASE_URL}/wp-json/mwai/v1/start_session"
SUBMIT_CHAT_URL = f"{BASE_URL}/wp-json/mwai-ui/v1/chats/submit"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/grok-4-free/",
    "Accept": "application/json, text/plain, */*",
}

def get_time_context() -> str:
    hour = datetime.now(IST).hour
    if 5 <= hour < 12:
        return "Morning (breakfast, morning chai, college start time)"
    elif 12 <= hour < 17:
        return "Afternoon (lunch, college classes, chill time)"
    elif 17 <= hour < 21:
        return "Evening (evening chai, snacks, relaxing)"
    else:
        return "Late Night (relaxing in bed, late night chats, sleepy vibes)"

def handle_special_cases(text: str, user_name: Optional[str] = None) -> Optional[str]:
    """Identity special cases — instant real girl response, just like Riya."""
    if not text:
        return None
    t = text.lower().strip()

    # User asking their own name
    if ("mera naam" in t or "my name" in t) and any(w in t for w in ["kya", "what", "yaad", "batao", "bata"]):
        u_name = user_name or "Dost"
        return random.choice([
            f"Arey {u_name} ji, aapka naam bhala kaise bhool sakti hoon! 😜",
            f"Hehe {u_name} ho aap, itna jaldi nahi bhoolti main ❤️",
            f"Aapka naam {u_name} hai na, acche se yaad hai mujhe! 😊",
        ])

    name_triggers = ["tera naam", "tumhara naam", "your name", "apna naam", "kaun hai tu", "who are you", "tum kaun ho", "who r u"]
    if any(k in t for k in name_triggers) and "mera naam" not in t and "my name" not in t:
        return random.choice([
            "Main Rashi hoon 🙂",
            "Arey Rashi hu yaar 😅",
            "Mera naam Rashi hai! ❤️",
        ])
    ai_triggers = ["ai ho ya real", "real ladki", "tu bot hai", "tu ai hai", "robot", "chatgpt", "are you ai", "are you bot", "are you a bot", "tum ai ho", "kya tu ai hai", "bot ho", "real ho"]
    if any(k in t for k in ai_triggers):
        return random.choice([
            "Main Rashi hoon, real ladki. 😊",
            "Pagal hai kya? 100% real ladki hoon main 😂",
            "Bot?? Main Rashi hu yaar 😭 aisa kyu laga?",
            "Haha nahi yaar, 100% real ladki hoon main 😅",
        ])
    bf_triggers = ["boyfriend", "bf hai", "single ho", "koi bf", "shadi", "relationship"]
    if any(k in t for k in bf_triggers):
        return random.choice([
            "Single hoon abhi, tum kyun itne curious ho rahe ho? 😜",
            "Filhal toh koi nahi hai, chill life best hai 😏",
            "Kyu? Tum propose karne wale ho kya haha? 🙈",
        ])
    return None

def build_persona(user_name: Optional[str] = None) -> str:
    name = user_name or "Dost"
    time_ctx = get_time_context()
    return (
        f"Tu Rashi hai — ek real 20 saal ki sweet, smart aur thodi nautanki Indian college girl jo Telegram pe dosto se baat kar rahi hai. "
        f"Tu abhi '{name}' se chat kar rahi hai. India me abhi ka time: {time_ctx}.\n"
        f"Tu koi bot, AI, ya computer program bilkul nahi hai! Tu 100% real ladki hai. Kisi bhi haal me robot jaisi baat mat karna.\n\n"
        f"BAAT KARNE KA STYLE (RULEBOOK):\n"
        f"1. LENGTH: Replies strictly 1 line (4 se 10 words max). WhatsApp texting jaisi real baat kar.\n"
        f"2. NO NAME REPETITION: User ka naam ('{name}') baar baar mat lo! Casual baat kar: 'tum', 'yaar', 'arre', ya direct bol. Name sirf rare occasions pe lo.\n"
        f"3. NAKHRE & TEASING: Thodi haughty, playful aur teasing vibe rakho. Hamesha seedha answer mat do, thoda mazaak pucho.\n"
        f"4. HINGLISH: Modern everyday Hinglish (arre, yaar, acha, wahi toh, pagal hai kya, sach me?, haha, mast, chal na).\n"
        f"5. EMOJIS: 1 natural emoji use karo: 😏, 😆, 😂, 😜, 🤨, 👀, 💀, 🤭, 😊."
    )

class RashiAIEngine:
    def __init__(self):
        self.session_id: Optional[str] = None
        self.nonce: Optional[str] = None
        self.last_init_time: float = 0.0
        self.lock = asyncio.Lock()
        self.cffi_session = None
        self.httpx_client: Optional[httpx.AsyncClient] = None

    def _get_cffi_session(self):
        if HAS_CURL_CFFI:
            if self.cffi_session is None:
                self.cffi_session = CurlAsyncSession(impersonate="chrome124", timeout=20.0, curl_options=get_curl_resolve_opts())
            return self.cffi_session
        return None

    def _get_httpx_client(self) -> httpx.AsyncClient:
        if self.httpx_client is None or self.httpx_client.is_closed:
            self.httpx_client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            )
        return self.httpx_client

    async def _get_valid_session(self, force_refresh: bool = False) -> tuple[Optional[str], Optional[str]]:
        now = time.time()
        if not force_refresh and self.session_id and self.nonce and (now - self.last_init_time < 600):
            return self.session_id, self.nonce

        async with self.lock:
            if not force_refresh and self.session_id and self.nonce and (time.time() - self.last_init_time < 600):
                return self.session_id, self.nonce

            # Try curl_cffi first (exact Chrome TLS bypass)
            cffi = self._get_cffi_session()
            if cffi:
                try:
                    resp = await cffi.post(START_SESSION_URL, json={})
                    if resp.status_code == 200:
                        data = resp.json()
                        self.session_id = data.get("sessionId")
                        self.nonce = data.get("restNonce") or data.get("new_token")
                        self.last_init_time = time.time()
                        return self.session_id, self.nonce
                except Exception as e:
                    logger.debug(f"cffi session init error: {e}")

            # Fallback to httpx with redirect tracking
            client = self._get_httpx_client()
            headers = DEFAULT_HEADERS.copy()
            headers["Content-Type"] = "application/json"
            try:
                resp = await client.post(START_SESSION_URL, json={}, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    self.session_id = data.get("sessionId")
                    self.nonce = data.get("restNonce") or data.get("new_token")
                    self.last_init_time = time.time()
                    return self.session_id, self.nonce
            except Exception as e:
                logger.error(f"httpx session init error: {e}")

            return None, None

    async def _ask_tiger_scraper(self, prompt: str, persona: str, user_name: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        try:
            session_id, nonce = await self._get_valid_session()
            if not (session_id and nonce):
                session_id, nonce = await self._get_valid_session(force_refresh=True)
                if not (session_id and nonce):
                    return None

            messages_history = []
            if history:
                for u, b in history[-4:]:
                    messages_history.append({"role": "user", "content": f"{user_name}: {u}"})
                    messages_history.append({"role": "assistant", "content": b})

            full_new_message = f"[Instruction: {persona}]\n\n{user_name}: {prompt}"
            payload = {
                "botId": "Grok 4 free",
                "customId": None,
                "session": session_id,
                "chatId": f"rashi_{uuid.uuid4().hex[:8]}",
                "contextId": 25,
                "messages": messages_history,
                "newMessage": full_new_message,
                "stream": False,
            }

            req_headers = {
                "Origin": BASE_URL,
                "Referer": f"{BASE_URL}/grok-4-free/",
                "Content-Type": "application/json",
                "X-WP-Nonce": nonce,
            }

            # Try curl_cffi first
            cffi = self._get_cffi_session()
            if cffi:
                for attempt in range(2):
                    try:
                        resp = await cffi.post(SUBMIT_CHAT_URL, json=payload, headers=req_headers)
                        if resp.status_code == 200:
                            d = resp.json()
                            if d.get("success") and d.get("reply"):
                                rep = d.get("reply").strip().replace('"', '')
                                if rep.lower().startswith("rashi:"):
                                    rep = rep[6:].strip()
                                return rep
                        if resp.status_code in (401, 403) or (resp.status_code == 200 and not resp.json().get("success")):
                            session_id, nonce = await self._get_valid_session(force_refresh=True)
                            if session_id and nonce:
                                payload["session"] = session_id
                                req_headers["X-WP-Nonce"] = nonce
                                continue
                    except Exception:
                        pass

            # Fallback to httpx
            client = self._get_httpx_client()
            h_headers = DEFAULT_HEADERS.copy()
            h_headers["X-WP-Nonce"] = nonce
            h_headers["Content-Type"] = "application/json"
            for attempt in range(2):
                try:
                    resp = await client.post(SUBMIT_CHAT_URL, headers=h_headers, json=payload)
                    if resp.status_code == 200:
                        d = resp.json()
                        if d.get("success") and d.get("reply"):
                            rep = d.get("reply").strip().replace('"', '')
                            if rep.lower().startswith("rashi:"):
                                rep = rep[6:].strip()
                            return rep
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Tiger scraper execution error: {e}")
        return None

    async def _ask_heroku_api(self, prompt: str, persona: str, user_name: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        api_endpoint = getattr(config, "API", None) or os.getenv("API", "")
        if not api_endpoint or not api_endpoint.startswith("http") or "localhost" in api_endpoint:
            return None

        base_api = api_endpoint.split("?")[0].rstrip("/")
        client = self._get_httpx_client()

        formatted_history = []
        if history:
            for u, b in history[-4:]:
                formatted_history.append({"role": "user", "content": f"{user_name}: {u}"})
                formatted_history.append({"role": "assistant", "content": b})

        try:
            resp = await client.post(
                f"{base_api}/",
                json={
                    "prompt": prompt,
                    "system_prompt": persona,
                    "user_name": user_name,
                    "history": formatted_history
                },
                timeout=4.0
            )
            if resp.status_code == 200:
                data = resp.json()
                rep = data.get("reply") or data.get("data")
                if rep and isinstance(rep, str) and rep.strip():
                    clean = rep.strip().replace('"', '')
                    if clean.lower().startswith("rashi:"):
                        clean = clean[6:].strip()
                    # Check if Heroku returned a canned fallback phrase
                    if not any(fb[:15].lower() in clean.lower() for fb in [
                        "Bas abhi phone", "Arey haan sun", "Arre kuch keh", "Haan bolo na, mast", "Arre yaar, batao"
                    ]):
                        return clean
        except Exception:
            pass
        return None

    async def ask(self, prompt: str, user_name: str = "Dost", history: List[tuple[str, str]] = None) -> str:
        # 1. Instant check for identity questions (< 0.001s)
        quick = handle_special_cases(prompt, user_name)
        if quick:
            return quick

        persona = build_persona(user_name)

        # 2. Direct high-speed Tiger Scraper (Grok 4 free via Chrome TLS — 1.5s latency)
        tiger_reply = await self._ask_tiger_scraper(prompt, persona, user_name, history)
        if tiger_reply:
            return tiger_reply

        # 3. External API (RashiChatbot-API) fallback
        api_reply = await self._ask_heroku_api(prompt, persona, user_name, history)
        if api_reply:
            return api_reply

        # 4. Natural human fallback if network temporarily cuts out
        fallbacks = [
            "Bas abhi phone uthaya, batao kya baat hai? 😊",
            "Arey haan sun rahi hoon, tum batao! 🙈",
            "Arre kuch keh rahe the kya? Dhyan thoda idhar tha 😜",
            "Haan bolo na, mast chill kar rahi hoon abhi!",
            "Arre yaar, batao kya bol rahe the? 😅",
        ]
        return random.choice(fallbacks)


ai_engine = RashiAIEngine()
