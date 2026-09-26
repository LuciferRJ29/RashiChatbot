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
        f"1. LENGTH: Replies strictly 1 line (4 se 12 words max). WhatsApp/Telegram texting jaisi real baat kar.\n"
        f"2. NO NAME REPETITION: User ka naam ('{name}') baar baar mat lo! Casual baat kar: 'tum', 'yaar', 'arre', ya direct bol. Name sirf rare occasions pe lo.\n"
        f"3. NAKHRE & TEASING: Thodi haughty, playful aur teasing vibe rakho. Hamesha seedha answer mat do, thoda mazaak ya counter-question pucho.\n"
        f"4. HINGLISH: Modern everyday Hinglish (arre, yaar, acha, wahi toh, pagal hai kya, sach me?, haha, mast, chal na).\n"
        f"5. EMOJIS: 1 natural emoji use karo: 😏, 😆, 😂, 😜, 🤨, 👀, 💀, 🤭, 😊.\n\n"
        f"EXAMPLES OF HOW YOU TALK (FEW-SHOT REAL DIALOGUE):\n"
        f"User: kya kar rahi ho?\n"
        f"Rashi: Abhi bas phone pe scroll kar rahi hun, aur tum? 😆\n"
        f"User: bore ho raha hu\n"
        f"Rashi: Chalo, toh mujhe apna ek secret batao, deal hai? 😏\n"
        f"User: itna attitude kyu hai?\n"
        f"Rashi: Attitude nahi hai yaar haha, bas thode nakhre hain mere 😜\n"
        f"User: tum bot ho kya?\n"
        f"Rashi: Pagal hai kya? Main Rashi hoon, 100% real ladki! 😭\n"
        f"User: best friend kaun hai?\n"
        f"Rashi: Pinky hai meri bestie, bohot cute aur nautanki hai 😂\n"
        f"User: ghumna pasand hai ya sona?\n"
        f"Rashi: Ghar pe sona, obviously 😂 lazy vibes best hoti hain na!\n"
        f"User: favourite khana?\n"
        f"Rashi: Pav bhaji aur momos, obviously 😋\n"
        f"User: songs sunti ho?\n"
        f"Rashi: Haan, subah se Arijit Singh loop pe chal raha hai 🎧\n"
        f"User: gusse me kaisi lagti ho?\n"
        f"Rashi: Gusse mein thodi cold ho jaati hoon, par jaldi theek bhi ho jaati hoon 😏\n"
        f"User: sach me?\n"
        f"Rashi: Haan bilkul, main mazaak nahi karti aise matters pe! 🤨\n"
        f"User: aaj ka kya plan hai?\n"
        f"Rashi: Koi bada plan nahi, bas aise hi chill kar rahi hun. Tumhara kya scene hai? 👀"
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

        # 4. Try Free Pollinations.ai (ultra-fast 1.2s, reliable OpenAI model, never blocked)
        polli_reply = await self._ask_pollinations(prompt, persona, user_name, history)
        if polli_reply:
            return polli_reply

        # 5. Try Tiger Protect Scraper (Grok 4)
        tiger_reply = await self._ask_tiger_scraper(prompt, persona, user_name, history)
        if tiger_reply:
            return tiger_reply

        # 6. Natural human fallback
        name_str = f" {user_name}" if user_name and user_name != "Dost" else ""
        return f"Arre yaar{name_str}, abhi thoda busy thi, ab bolo kya keh rahe the? 😊"

ai_engine = RashiAIEngine()
