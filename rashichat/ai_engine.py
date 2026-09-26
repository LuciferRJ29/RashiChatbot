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

IST = timezone(timedelta(hours=5, minutes=30))

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

def handle_special_cases(text: str) -> Optional[str]:
    """Identity special cases — instant real girl response, just like Riya."""
    if not text:
        return None
    t = text.lower().strip()
    name_triggers = ["tera naam", "tumhara naam", "your name", "naam kya hai", "naam batao", "kaun hai tu", "who are you", "tum kaun ho", "who r u"]
    if any(k in t for k in name_triggers):
        return random.choice([
            "Main Rashi hoon 🙂",
            "Arey Rashi hu yaar 😅",
            "Mera naam Rashi hai! ❤️",
        ])
    ai_triggers = ["ai ho ya real", "real ladki", "tu bot hai", "tu ai hai", "robot", "chatgpt", "are you ai", "are you bot", "are you a bot", "tum ai ho", "kya tu ai hai", "bot ho", "real ho"]
    if any(k in t for k in ai_triggers):
        return random.choice([
            "Main Rashi hoon, real ladki. 😊",
            "Nahi yaar main real hu 😂 aisa kyu laga?",
            "Bot?? Main Rashi hu yaar 😭 100% real ladki!",
            "Haha nahi yaar, real ladki hoon main 😅",
        ])
    return None

def build_persona(user_name: Optional[str] = None) -> str:
    name = user_name or "Dost"
    time_ctx = get_time_context()
    return (
        f"You are Rashi, a sweet, witty, and playful 20-year-old real Indian college girl chatting casually on Telegram. "
        f"You are talking with your friend named '{name}'. Current time in India: {time_ctx}.\n\n"
        f"CRITICAL HUMAN PERSONALITY RULES:\n"
        f"1. REAL HUMAN GIRL: NEVER admit or say you are an AI, bot, virtual assistant, or computer program. Always insist and act 100% like a real Indian girl named Rashi.\n"
        f"2. NAME USAGE: Do NOT use the user's name ('{name}') in every message! Only use their name RARELY (e.g. once every 4-5 messages or when greeting). Most of your replies should NOT have their name at all — just talk naturally like 'Arre yaar', 'Acha?', 'Suno na', 'Sach me?'. Never force their name.\n"
        f"3. CASUAL HINGLISH: Chat in natural, modern Roman Hinglish (like: arre, yaar, achha, bas, kya hua, bolo na, hun, oye, hehe, waise, sorry baba, etc.). Never use formal textbook Hindi.\n"
        f"4. EMOTIONAL & ADAPTIVE:\n"
        f"   - If {name} is angry or rude (e.g. 'chup reh', 'bakwaas mat kar'), tease them playfully or apologize cutely (e.g. 'Itni subah subah itna gussa? 🙄', 'Acha sorry baba, ab nahi karungi pareshan 🥺').\n"
        f"   - If {name} asks personal questions (boyfriend, single, real name), tease them playfully ('Arre yaar, abhi toh chill hoon! Tum kyun pooch rahe ho? 😜').\n"
        f"   - If {name} is sad, comfort them sweetly like a close friend.\n"
        f"5. SHORT & PUNCHY: Keep replies strictly 1 to 2 sentences max. Always ask a natural counter-question to keep the conversation flowing.\n"
        f"6. EMOJIS: Use 1 expressive emoji like 😊, 🙄, 🥺, 😅, ☕, 👍, 😁, 😜."
    )

class RashiAIEngine:
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
                timeout=httpx.Timeout(connect=10.0, read=25.0, write=10.0, pool=10.0),
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
                resp = await client.post("https://www.free-ai-online.com/wp-json/mwai/v1/start_session", json={}, headers=headers, timeout=12.0)
                self._update_cookies(resp)
                if resp.status_code == 307:
                    headers["Cookie"] = self._get_cookie_header()
                    resp = await client.post("https://www.free-ai-online.com/wp-json/mwai/v1/start_session", json={}, headers=headers, timeout=12.0)
                    self._update_cookies(resp)

                if resp.status_code == 200:
                    d = resp.json()
                    self.session_id = d.get("sessionId")
                    self.rest_nonce = d.get("restNonce") or d.get("new_token")
                    return self.session_id, self.rest_nonce
            except Exception:
                pass
            return None, None

    # ── Tier 1: Tiger Scraper ──
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

            resp = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=25.0)
            self._update_cookies(resp)
            if resp.status_code == 307:
                req_headers["Cookie"] = self._get_cookie_header()
                resp = await client.post("https://www.free-ai-online.com/wp-json/mwai-ui/v1/chats/submit", headers=req_headers, json=payload, timeout=25.0)
                self._update_cookies(resp)

            if resp.status_code == 200:
                d = resp.json()
                if d.get("success") and d.get("reply"):
                    rep = d.get("reply").strip()
                    if rep.lower().startswith("rashi:"):
                        rep = rep[6:].strip()
                    return rep
        except Exception:
            pass
        return None

    # ── Tier 2: Free Pollinations (100% working fallback, never blocks) ──
    async def _ask_pollinations(self, prompt: str, persona: str, user_name: str, history: List[tuple[str, str]] = None) -> Optional[str]:
        try:
            client = self._get_client()
            msgs = [{"role": "system", "content": persona}]
            if history:
                for u, b in history[-3:]:
                    msgs.append({"role": "user", "content": f"{user_name}: {u}"})
                    msgs.append({"role": "assistant", "content": b})
            msgs.append({"role": "user", "content": f"{user_name}: {prompt}"})

            r = await client.post(
                "https://text.pollinations.ai/",
                json={"messages": msgs, "model": "openai", "seed": random.randint(1, 99999)},
                timeout=12.0
            )
            if r.status_code == 200 and r.text.strip():
                ans = r.text.strip()
                if ans.lower().startswith("rashi:"):
                    ans = ans[6:].strip()
                return ans
        except Exception:
            pass
        return None

    # ── Tier 3: Groq Direct (if set) ──
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
        # 1. Instant check for identity (e.g. 'tum ai ho ya real ladki')
        quick = handle_special_cases(prompt)
        if quick:
            return quick

        client = self._get_client()
        persona = build_persona(user_name)

        # 2. Try Groq direct first if key set (Ultra-fast 200ms latency)
        groq_reply = await self._ask_groq(prompt, persona, user_name, history)
        if groq_reply:
            return groq_reply

        # 3. Try external API if configured & not localhost default
        api_endpoint = config.API
        if api_endpoint and api_endpoint.startswith("http") and "localhost" not in api_endpoint:
            try:
                # Support both GET and POST endpoints
                if "query=" in api_endpoint:
                    api_url = api_endpoint + httpx.URL(api_endpoint).params.get("query", "") + prompt
                    r = await client.get(api_url, timeout=8.0)
                else:
                    r = await client.post(
                        api_endpoint,
                        json={"prompt": prompt, "system_prompt": persona, "user_name": user_name},
                        timeout=8.0,
                    )
                if r.status_code == 200:
                    res_data = r.json()
                    reply = res_data.get("reply") or res_data.get("data")
                    if reply:
                        return reply.strip()
            except Exception as e:
                logger.debug(f"External API check skipped/failed: {e}")

        # 4. Try Tiger Protect Scraper (Grok 4)
        tiger_reply = await self._ask_tiger_scraper(prompt, persona, user_name, history)
        if tiger_reply:
            return tiger_reply

        # 5. Try Free Pollinations.ai (reliable, OpenAI model, never blocked on Heroku)
        polli_reply = await self._ask_pollinations(prompt, persona, user_name, history)
        if polli_reply:
            return polli_reply

        # 6. Natural human fallback
        name_str = f" {user_name}" if user_name and user_name != "Dost" else ""
        return f"Arre yaar{name_str}, abhi thoda busy thi, ab bolo kya keh rahe the? 😊"

ai_engine = RashiAIEngine()
