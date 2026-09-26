import os
import asyncio
import logging
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import httpx
import config

logger = logging.getLogger("rashi_ai_engine")

# IST timezone (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_time_context() -> str:
    """Returns realistic Indian day context based on IST."""
    hour = datetime.now(IST).hour
    if 5 <= hour < 12:
        return "Morning (breakfast, morning chai, college start time)"
    elif 12 <= hour < 17:
        return "Afternoon (lunch, college classes, chill time)"
    elif 17 <= hour < 21:
        return "Evening (evening chai, snacks, relaxing)"
    else:
        return "Late Night (relaxing in bed, late night chats, sleepy vibes)"

def build_persona(user_name: Optional[str] = None) -> str:
    name = user_name or "Dost"
    time_ctx = get_time_context()
    return (
        f"You are Rashi, a sweet, witty, and playful 20-year-old real Indian college girl chatting casually on Telegram. "
        f"You are talking with your friend named '{name}'. Current time in India: {time_ctx}.\n\n"
        f"CRITICAL HUMAN PERSONALITY RULES:\n"
        f"1. REAL HUMAN GIRL: NEVER admit or say you are an AI, bot, virtual assistant, or computer program. Always insist and act 100% like a real Indian girl named Rashi.\n"
        f"2. CALL USER BY NAME: Frequently call the user by their name ('{name}') naturally in your sentences.\n"
        f"3. CASUAL HINGLISH: Chat in natural, modern Roman Hinglish (like: arre, yaar, achha, bas, kya hua, bolo na, hun, oye, hehe, waise, sorry baba, etc.). Never use formal textbook Hindi.\n"
        f"4. EMOTIONAL & ADAPTIVE:\n"
        f"   - If {name} is angry or rude (e.g. 'chup reh', 'bakwaas mat kar'), tease them playfully or apologize cutely (e.g. 'Itni subah subah itna gussa? 🙄', 'Acha sorry baba, ab nahi karungi pareshan 🥺').\n"
        f"   - If {name} asks personal questions (boyfriend, single, real name), tease them playfully ('Arre yaar, abhi toh chill hoon! Tum kyun pooch rahe ho? 😜').\n"
        f"   - If {name} is sad, comfort them sweetly like a close friend.\n"
        f"5. SHORT & PUNCHY: Keep replies strictly 1 to 2 sentences max. Always ask a natural counter-question to keep the conversation flowing.\n"
        f"6. EMOJIS: Use 1 expressive emoji like 😊, 🙄, 🥺, 😅, ☕, 👍, 😁, 😜."
    )

class RashiAIEngine:
    """
    Rashi AI Engine with Tiger Protect cookie handshake & Context-Aware Human Persona
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
    async def _ask_tiger_scraper(self, prompt: str, persona: str, user_name: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        try:
            client = self._get_client()
            session_id, rest_nonce = await self._init_tiger_session(client)
            if not (session_id and rest_nonce):
                session_id, rest_nonce = await self._init_tiger_session(client, force=True)
                if not (session_id and rest_nonce):
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
                        # Clean any leftover prefixes like 'Rashi:' or quotes
                        if reply.lower().startswith("rashi:"):
                            reply = reply[6:].strip()
                        return reply
        except Exception as ex:
            logger.debug(f"Tiger scraper error: {ex}")
        return None

    # ── Tier 2: Groq Direct ──
    async def _ask_groq(self, prompt: str, persona: str, user_name: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key:
            return None
        try:
            client = self._get_client()
            messages = [{"role": "system", "content": persona}]
            if history:
                for u, b in history[-4:]:
                    messages.append({"role": "user", "content": f"{user_name}: {u}"})
                    messages.append({"role": "assistant", "content": b})
            messages.append({"role": "user", "content": f"{user_name}: {prompt}"})

            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.75, "max_tokens": 150},
                timeout=12.0
            )
            if r.status_code == 200:
                data = r.json()
                reply = data["choices"][0]["message"]["content"].strip()
                if reply.lower().startswith("rashi:"):
                    reply = reply[6:].strip()
                return reply
        except Exception:
            pass
        return None

    # ── Main Ask Method ──
    async def ask(self, prompt: str, user_name: str = "Dost", history: List[tuple[str, str]] = None) -> str:
        client = self._get_client()
        persona = build_persona(user_name)

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
                        json={"prompt": prompt, "system_prompt": persona},
                        timeout=20.0,
                    )
                if r.status_code == 200:
                    res_data = r.json()
                    reply = res_data.get("reply") or res_data.get("data")
                    if reply:
                        return reply.strip()
            except Exception as e:
                logger.debug(f"External API check skipped/failed: {e}")

        # 2. Try Tiger Protect Scraper (Grok 4)
        tiger_reply = await self._ask_tiger_scraper(prompt, persona, user_name, history)
        if tiger_reply:
            return tiger_reply

        # 3. Try Groq direct (if key set)
        groq_reply = await self._ask_groq(prompt, persona, user_name, history)
        if groq_reply:
            return groq_reply

        # 4. Human-like in-character fallback
        name_str = f" {user_name}" if user_name and user_name != "Dost" else ""
        return f"Arre yaar{name_str}, abhi thoda busy thi, ab bolo kya keh rahe the? 😊"

ai_engine = RashiAIEngine()
