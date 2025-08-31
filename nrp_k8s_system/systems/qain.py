from __future__ import annotations
"""
INFOGENT (fresh build): lightweight, dependency-minimal scaffold
----------------------------------------------------------------
A small, self-contained implementation inspired by INFOGENT's logic:
Navigator (planner) → Extractor (scraper) → Aggregator (feedback/coverage).

Run (example):
  python main.py "Who was FuboTV's CPO in 2020 and who was on the management team?"

Notes
- Search provider is pluggable. The default uses DuckDuckGo HTML (no API key),
  but you can swap in Serper/Bing/Google easily (see SearchProvider).
- Scraper is polite: robots.txt check (best-effort), timeout, basic Readability-like
  text extraction (BeautifulSoup), and per-domain fetch cap.
- Aggregator performs naive slot coverage via keyword scaffolding and deduped
  fact snippets. Replace with your IE template/LLM later.

Dependencies (pip):
  requests, beautifulsoup4, tldextract, pydantic, urllib3
"""

import os
serper_key = os.getenv("SERPER_API_KEY")
bing_key = os.getenv("BING_SEARCH_KEY")
import argparse
import re
import time
import json
import html
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import tldextract
from pydantic import BaseModel

# ----------------------- Config & Logging -----------------------

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("infogent-fresh")
logger.info(f"SERPER set? {bool(serper_key)} | BING set? {bool(bing_key)}")


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"}

# ----------------------- Schemas -----------------------
class Query(BaseModel):
    id: str
    text: str
    mode: str = "direct_api"  # "visual" reserved for future use
    steps: int = 10
    time_budget_s: int = 180
    domains_allow: List[str] = []
    domains_deny: List[str] = []

class NavigatorAction(BaseModel):
    type: str  # SEARCH | AGGREGATE | HALT
    args: Dict

class ExtractedPayload(BaseModel):
    url: str
    title: str
    content_text: str
    meta: Dict = {}

class Feedback(BaseModel):
    text: str
    needs: List[str]
    stop: bool = False

@dataclass
class AggregatorState:
    facts: List[Dict]
    sources: List[Dict]
    coverage: Dict[str, float]
    seen_urls: set

# ----------------------- Utilities -----------------------
def domain_of(url: str) -> str:
    ext = tldextract.extract(url)
    return ".".join([p for p in [ext.domain, ext.suffix] if p])

# very light robots.txt checker (best-effort)
def allowed_by_robots(base: str, path: str = "/") -> bool:
    try:
        from urllib.parse import urljoin
        robots = requests.get(urljoin(base, "/robots.txt"), headers=DEFAULT_HEADERS, timeout=4)
        if robots.status_code != 200:
            return True
        disallows = []
        ua = None
        for line in robots.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if line.lower().startswith("user-agent:"):
                ua = line.split(":",1)[1].strip()
            if ua in ("*", USER_AGENT) and line.lower().startswith("disallow:"):
                rule = line.split(":",1)[1].strip()
                disallows.append(rule)
        for rule in disallows:
            if rule and path.startswith(rule):
                return False
        return True
    except Exception:
        return True

# ----------------------- Search Provider -----------------------
class SearchProvider:
    """Abstract search provider. Implement search(query)->List[dict(title,url,snippet)]."""
    def search(self, query: str, k: int = 8) -> List[Dict[str, str]]:
        raise NotImplementedError

class DuckDuckGoHTML(SearchProvider):
    DDG_URL = "https://duckduckgo.com/html/"
    def search(self, query: str, k: int = 8) -> List[Dict[str, str]]:
        # DuckDuckGo HTML results page (no JS)
        params = {"q": query}
        try:
            r = requests.post(self.DDG_URL, data=params, headers=DEFAULT_HEADERS, timeout=10)
            r.raise_for_status()
        except Exception as e:
            logger.info(f"DDG HTML failed: {e}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        # Try multiple selector patterns (DDG layout varies)
        selectors = [
            ("div.result__body", "a.result__a", "a.result__snippet, div.result__snippet"),
            ("div.web-result", "a.result__a", "div.result__snippet"),
        ]
        for body_sel, a_sel, sn_sel in selectors:
            for res in soup.select(body_sel):
                a = res.select_one(a_sel)
                if not a: continue
                url = a.get("href")
                title = html.unescape(a.get_text(strip=True))
                snippet_el = res.select_one(sn_sel)
                snip = html.unescape(snippet_el.get_text(" ", strip=True)) if snippet_el else ""
                if url and url.startswith("http"):
                    out.append({"title": title, "url": url, "snippet": snip})
                if len(out) >= k: break
            if out: break
        return out

class SerperSearch(SearchProvider):
    """Uses Serper (Google JSON) if SERPER_API_KEY is set."""
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.endpoint = "https://google.serper.dev/search"
    def search(self, query: str, k: int = 8) -> List[Dict[str, str]]:
        if not self.api_key:
            return []
        try:
            payload = {"q": query, "num": k}
            r = requests.post(self.endpoint, headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"}, json=payload, timeout=12)
            r.raise_for_status()
            data = r.json()
            out = []
            for item in (data.get("organic", []) or [])[:k]:
                out.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return out
        except Exception as e:
            logger.info(f"Serper failed: {e}")
            return []

class BingSearch(SearchProvider):
    """Uses Bing Web Search v7 if BING_SEARCH_KEY is set."""
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"
    def search(self, query: str, k: int = 8) -> List[Dict[str, str]]:
        if not self.api_key:
            return []
        try:
            params = {"q": query, "count": k}
            r = requests.get(self.endpoint, params=params, headers={"Ocp-Apim-Subscription-Key": self.api_key, **DEFAULT_HEADERS}, timeout=12)
            r.raise_for_status()
            data = r.json()
            out = []
            for item in (data.get("webPages", {}).get("value", []) or [])[:k]:
                out.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                })
            return out
        except Exception as e:
            logger.info(f"Bing failed: {e}")
            return []

# ----------------------- Extractor (Scraper) -----------------------
class Extractor:
    def __init__(self, per_domain_cap: int = 3):
        self.per_domain_cap = per_domain_cap
        self.domain_counts: Dict[str, int] = {}

    def scrape(self, url: str) -> Optional[ExtractedPayload]:
        try:
            from urllib.parse import urlparse
            u = urlparse(url)
            base = f"{u.scheme}://{u.netloc}"
            if not allowed_by_robots(base, u.path):
                logger.info(f"robots.txt blocks: {url}")
                return None

            dom = domain_of(url)
            cnt = self.domain_counts.get(dom, 0)
            if cnt >= self.per_domain_cap:
                logger.info(f"domain cap reached for {dom}")
                return None

            r = requests.get(url, headers=DEFAULT_HEADERS, timeout=12)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""):
                return None
            self.domain_counts[dom] = cnt + 1

            soup = BeautifulSoup(r.text, "html.parser")
            for s in soup(["script","style","noscript"]) : s.decompose()
            title = soup.title.get_text(strip=True) if soup.title else ""
            texts = [t.get_text(" ", strip=True) for t in soup.select("article, main, p, li")]
            content = re.sub(r"\s+", " ", " ".join(texts))
            content = content[:100_000]
            return ExtractedPayload(url=url, title=title, content_text=content, meta={})
        except Exception as e:
            logger.debug(f"scrape error: {e}")
            return None

# ----------------------- Aggregator -----------------------
class Aggregator:
    def __init__(self, query_text: str):
        self.query_text = query_text
        self.required_slots = self._derive_slots(query_text)

    def _derive_slots(self, text: str) -> List[str]:
        # naive slot derivation: nouns/keywords from the query
        words = re.findall(r"[A-Za-z][A-Za-z0-9\-']+", text.lower())
        stop = set("the a an what who where when why how by for of in on to with from and or is are was were be been being list show find give".split())
        keywords = [w for w in words if w not in stop and len(w) > 2]
        uniq = []
        for w in keywords:
            if w not in uniq:
                uniq.append(w)
        return uniq[:8]  # cap slots

    def merge(self, S: AggregatorState, payload: ExtractedPayload) -> AggregatorState:
        if payload.url in S.seen_urls:
            return S
        S.seen_urls.add(payload.url)

        text = payload.content_text.lower()
        # collect snippets around slot hits
        new_facts = []
        for slot in self.required_slots:
            for m in re.finditer(re.escape(slot), text):
                start = max(0, m.start() - 120)
                end = min(len(text), m.end() + 160)
                snippet = text[start:end]
                new_facts.append({
                    "slot": slot,
                    "snippet": snippet,
                    "url": payload.url,
                    "title": payload.title,
                })
        # dedupe by (slot, url, snippet)
        seen = {(f["slot"], f["url"], f["snippet"]) for f in S.facts}
        for f in new_facts:
            key = (f["slot"], f["url"], f["snippet"]) 
            if key not in seen:
                S.facts.append(f)
                seen.add(key)
        S.sources.append({"url": payload.url, "title": payload.title})

        # update coverage: fraction of slots that appeared at least once
        covered = {slot: 0.0 for slot in self.required_slots}
        for f in S.facts:
            covered[f["slot"]] = 1.0
        S.coverage = covered
        return S

    def make_feedback(self, S: AggregatorState) -> Feedback:
        missing = [s for s,v in S.coverage.items() if v < 1.0]
        if not missing:
            return Feedback(text="All slots covered (naive).", needs=[], stop=True)
        # craft sub-queries focusing on missing slots and authoritative hints
        last_src = S.sources[-1]["url"] if S.sources else ""
        dq = f"{self.query_text} {missing[0]} site:.gov OR site:.org"
        text = (
            f"Missing coverage for: {', '.join(missing[:3])}. "
            f"Try authoritative sources. Last source seen: {last_src}"
        )
        return Feedback(text=text, needs=[dq], stop=False)

    def finalize(self, S: AggregatorState) -> Dict:
        # provide a compact answer: top snippets per slot + sources
        per_slot: Dict[str, List[Dict]] = {}
        for f in S.facts:
            per_slot.setdefault(f["slot"], []).append({"snippet": f["snippet"], "url": f["url"]})
        answer = {s: (per_slot.get(s, [])[:2]) for s in self.required_slots}
        return {
            "answer": answer,
            "coverage": S.coverage,
            "sources": S.sources,
        }

# ----------------------- Navigator (Planner) -----------------------
class Navigator:
    def __init__(self, search: SearchProvider):
        self.search = search
        self._result_cache: List[Dict[str,str]] = []
        self._cursor = 0

    def plan(self, user_query: str, feedback: Feedback) -> NavigatorAction:
        # If we have unused search results, aggregate next URL
        if self._cursor < len(self._result_cache):
            url = self._result_cache[self._cursor]["url"]
            self._cursor += 1
            logger.info(f"AGGREGATE → {url}")
            return NavigatorAction(type="AGGREGATE", args={"url": url})
        # Else, we need to search. Use last feedback.need or initial query, try a couple rewrites
        candidates = []
        base_q = (feedback.needs[0] if feedback.needs else user_query).strip()
        candidates.append(base_q)
        # heuristic rewrite: remove quotes, add site bias if not present
        candidates.append(re.sub(r'"', '', base_q))
        if " site:" not in base_q.lower():
            candidates.append(base_q + " site:.gov OR site:.org")
        for q in candidates:
            logger.info(f"SEARCH → '{q}'")
            results = self.search.search(q, k=8)
            if results:
                self._result_cache = results
                self._cursor = 0
                url = results[0]["url"]
                logger.info(f"AGGREGATE → {url}")
                return NavigatorAction(type="AGGREGATE", args={"url": url})
        return NavigatorAction(type="HALT", args={"reason": "no_results"})

# ----------------------- Controller (Loop) -----------------------
class Controller:
    def __init__(self, search: SearchProvider | None = None):
        if search is None:
            # auto-pick provider by env vars
            import os
            serper_key = os.getenv("SERPER_API_KEY")
            bing_key = os.getenv("BING_SEARCH_KEY")
            if serper_key:
                logger.info("Using Serper search provider")
                search = SerperSearch(serper_key)
            elif bing_key:
                logger.info("Using Bing search provider")
                search = BingSearch(bing_key)
            else:
                logger.info("Using DuckDuckGo HTML search provider (no key)")
                search = DuckDuckGoHTML()
        self.navigator = Navigator(search)
        self.extractor = Extractor()
        self._start_ts = time.time()

    def run(self, query: Query) -> Dict:
        S = AggregatorState(facts=[], sources=[], coverage={}, seen_urls=set())
        aggr = Aggregator(query.text)
        F = Feedback(text="start", needs=[query.text], stop=False)
        steps = 0
        while not F.stop and steps < query.steps:
            if (time.time() - self._start_ts) > query.time_budget_s:
                logger.info("Time budget exceeded, halting.")
                break
            action = self.navigator.plan(query.text, F)
            if action.type == "HALT":
                logger.info(f"Navigator halted: {action.args}")
                break
            if action.type == "AGGREGATE":
                url = action.args["url"]
                # domain policy gates
                d = domain_of(url)
                if query.domains_allow and d not in query.domains_allow:
                    logger.info(f"Skip (not in allow list): {url}")
                elif d in set(query.domains_deny):
                    logger.info(f"Skip (deny list): {url}")
                else:
                    payload = self.extractor.scrape(url)
                    if payload:
                        S = aggr.merge(S, payload)
                        F = aggr.make_feedback(S)
                    else:
                        F = Feedback(text="scrape failed; refine search", needs=[query.text], stop=False)
            else:
                # (visual mode actions would go here)
                pass
            steps += 1
        return aggr.finalize(S)

# ----------------------- CLI -----------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("question", help="information-seeking query", type=str)
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--time", type=int, default=120)
    p.add_argument("--allow", nargs="*", default=[], help="allowed domains (e.g., sec.gov wikipedia.org)")
    p.add_argument("--deny", nargs="*", default=[], help="denied domains")
    args = p.parse_args()

    q = Query(id="q-1", text=args.question, steps=args.steps, time_budget_s=args.time,
              domains_allow=args.allow, domains_deny=args.deny)
    ctl = Controller()
    out = ctl.run(q)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
