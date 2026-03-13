"""
CRIPTO BRASIL INTEL — Backend v6
==================================
66 fontes RSS · Engine editorial · Publisher · Scheduler integrado
Deploy: Railway / Render / Fly.io / Docker

Variáveis de ambiente:
  PORT=8000               porta do servidor (obrigatório no Render/Railway)
  IG_ACCESS_TOKEN=...     token da API do Instagram
  IG_USER_ID=...          ID do perfil do Instagram
  AUTO_APPROVE=false      publica direto sem aprovação manual
  CACHE_TTL=900           segundos entre refreshes de RSS (padrão 15min)
  MAX_ARTICLES=32         máximo de artigos por request (padrão 32)
  ENVIRONMENT=production  development ativa reload

Rodar local:
  pip install -r requirements.txt
  python server.py

Deploy Railway:
  railway up

Deploy Render:
  Conecta repo no Render → Web Service → Start Command: python server.py

Endpoints:
  GET  /                         → info + status
  GET  /api/news?limit=24&cripto=12&macro=8&geo=6
  GET  /api/queue                → fila de publicação
  POST /api/queue/approve        → {hash: str}
  POST /api/queue/reject         → {hash: str}
  POST /api/queue/build          → gera fila agora
  GET  /api/sources              → status de cada fonte RSS
  GET  /api/sources/stats        → estatísticas por fonte
  GET  /api/editorial_formats    → 7 formatos editoriais
  GET  /api/health               → health check
  GET  /docs                     → Swagger UI
"""

import asyncio, hashlib, json, logging, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

try:
    from editorial_engine import enrich_article, detect_format, FORMATS
except ImportError:
    logging.warning("editorial_engine.py nao encontrado — modo basico")
    FORMATS = {}
    def enrich_article(a): return a
    def detect_format(a): return "EDUCATIVO_CONTEXTO"

# ── CONFIG ────────────────────────────────────────────────────────────────────
PORT       = int(os.getenv("PORT", 8000))
CACHE_TTL  = int(os.getenv("CACHE_TTL", 900))
MAX_ART    = int(os.getenv("MAX_ARTICLES", 32))
IG_TOKEN   = os.getenv("IG_ACCESS_TOKEN", "")
IG_USER    = os.getenv("IG_USER_ID", "")
AUTO_APPR  = os.getenv("AUTO_APPROVE", "false").lower() == "true"
QUEUE_FILE = Path(os.getenv("QUEUE_FILE", "publisher_queue.json"))
ENV        = os.getenv("ENVIRONMENT", "production")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cripto-intel")

app = FastAPI(
    title="Cripto Brasil Intel API v6",
    description="66 fontes RSS · Engine editorial · Carrosseis automaticos · 100 fontes referência",
    version="5.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 55 FONTES RSS ─────────────────────────────────────────────────────────────
FEEDS = [
    # ── CRIPTO BR (13) ─────────────────────────────────────────────────────────
    {"url":"https://livecoins.com.br/feed/",
     "name":"Livecoins","src":"t-lv","cat":"cripto","br":True,"weight":1.5},
    {"url":"https://criptofacil.com/feed/",
     "name":"CriptoFacil","src":"t-cf","cat":"cripto","br":True,"weight":1.4},
    {"url":"https://www.cointimes.com.br/feed/",
     "name":"Cointimes","src":"t-ct2","cat":"cripto","br":True,"weight":1.3},
    {"url":"https://portaldobitcoin.uol.com.br/feed/",
     "name":"Portal Bitcoin","src":"t-pb","cat":"cripto","br":True,"weight":1.2},
    {"url":"https://www.infomoney.com.br/guias/bitcoin/feed/",
     "name":"InfoMoney Cripto","src":"t-im","cat":"cripto","br":True,"weight":1.3},
    {"url":"https://www.beincrypto.com.br/feed/",
     "name":"BeInCrypto BR","src":"t-bic","cat":"cripto","br":True,"weight":1.2},
    {"url":"https://br.cointelegraph.com/rss",
     "name":"Cointelegraph BR","src":"t-ctbr","cat":"cripto","br":True,"weight":1.4},
    {"url":"https://exame.com/cripto/feed/",
     "name":"Exame Cripto","src":"t-ex","cat":"cripto","br":True,"weight":1.3},
    {"url":"https://www.moneytimes.com.br/feed/",
     "name":"MoneyTimes","src":"t-mt","cat":"cripto","br":True,"weight":1.1},
    {"url":"https://coinext.com.br/blog/feed",
     "name":"Coinext Blog","src":"t-cx","cat":"cripto","br":True,"weight":1.0},
    {"url":"https://blocknews.com.br/feed/",
     "name":"Blocknews","src":"t-bn","cat":"cripto","br":True,"weight":1.1},
    {"url":"https://www.cnnbrasil.com.br/economia/mercados/feed/",
     "name":"CNN Brasil Cripto","src":"t-cnn","cat":"cripto","br":True,"weight":1.2},
    {"url":"https://abcripto.com.br/feed/",
     "name":"ABcripto","src":"t-abc","cat":"cripto","br":True,"weight":1.2},

    # ── CRIPTO GLOBAL (18) ─────────────────────────────────────────────────────
    {"url":"https://cointelegraph.com/rss",
     "name":"Cointelegraph","src":"t-ct","cat":"cripto","br":False,"weight":1.4},
    {"url":"https://www.coindesk.com/arc/outboundfeeds/rss/",
     "name":"CoinDesk","src":"t-cd","cat":"cripto","br":False,"weight":1.5},
    {"url":"https://decrypt.co/feed",
     "name":"Decrypt","src":"t-dc","cat":"cripto","br":False,"weight":1.2},
    {"url":"https://www.theblock.co/rss.xml",
     "name":"The Block","src":"t-tb","cat":"cripto","br":False,"weight":1.3},
    {"url":"https://blockworks.co/feed",
     "name":"Blockworks","src":"t-bk","cat":"cripto","br":False,"weight":1.2},
    {"url":"https://www.cryptoslate.com/feed/",
     "name":"CryptoSlate","src":"t-cs","cat":"cripto","br":False,"weight":1.1},
    {"url":"https://ambcrypto.com/feed/",
     "name":"AMBCrypto","src":"t-amb","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://bitcoinmagazine.com/.rss/full/",
     "name":"Bitcoin Magazine","src":"t-bm","cat":"cripto","br":False,"weight":1.4},
    {"url":"https://beincrypto.com/feed/",
     "name":"BeInCrypto","src":"t-bic2","cat":"cripto","br":False,"weight":1.1},
    {"url":"https://cryptobriefing.com/feed/",
     "name":"Crypto Briefing","src":"t-cb","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://www.coinbureau.com/feed/",
     "name":"Coin Bureau","src":"t-cbu","cat":"cripto","br":False,"weight":1.1},
    {"url":"https://unchainedcrypto.com/feed/",
     "name":"Unchained Crypto","src":"t-uc","cat":"cripto","br":False,"weight":1.2},
    {"url":"https://coingape.com/feed/",
     "name":"CoinGape","src":"t-cg","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://watcher.guru/news/feed",
     "name":"Watcher.Guru","src":"t-wg","cat":"cripto","br":False,"weight":1.1},
    {"url":"https://cryptonews.com/news/feed/",
     "name":"CryptoNews","src":"t-cn","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://www.newsbtc.com/feed/",
     "name":"NewsBTC","src":"t-nb","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://u.today/rss",
     "name":"U.Today","src":"t-ut","cat":"cripto","br":False,"weight":1.0},
    {"url":"https://thedefiant.io/feed",
     "name":"The Defiant","src":"t-def","cat":"cripto","br":False,"weight":1.2},

    # ── NOVAS FONTES 99 e 100 ──────────────────────────────────────────────────
    {"url":"https://coinmarketcap.com/rss/news.xml",
     "name":"CoinMarketCap News","src":"t-cmc","cat":"cripto","br":False,"weight":1.3},
    {"url":"https://dlnews.com/rss.xml",
     "name":"DL News","src":"t-dln","cat":"cripto","br":False,"weight":1.2},

    # ── MACRO EUA (10) ─────────────────────────────────────────────────────────
    {"url":"https://feeds.reuters.com/reuters/businessNews",
     "name":"Reuters Business","src":"t-rt","cat":"macro","br":False,"weight":1.6},
    {"url":"https://www.cnbc.com/id/20910258/device/rss/rss.html",
     "name":"CNBC Economy","src":"t-cnbc","cat":"macro","br":False,"weight":1.5},
    {"url":"https://www.cnbc.com/id/10000664/device/rss/rss.html",
     "name":"CNBC Markets","src":"t-cnbc2","cat":"macro","br":False,"weight":1.4},
    {"url":"https://feeds.marketwatch.com/marketwatch/topstories/",
     "name":"MarketWatch","src":"t-mw","cat":"macro","br":False,"weight":1.3},
    {"url":"https://apnews.com/rss/business",
     "name":"AP Business","src":"t-ap","cat":"macro","br":False,"weight":1.3},
    {"url":"https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
     "name":"WSJ Markets","src":"t-wsj","cat":"macro","br":False,"weight":1.5},
    {"url":"https://www.ft.com/rss/home/us",
     "name":"Financial Times","src":"t-ft","cat":"macro","br":False,"weight":1.5},
    {"url":"https://thehill.com/business/feed/",
     "name":"The Hill Biz","src":"t-thb","cat":"macro","br":False,"weight":1.1},
    {"url":"https://www.economist.com/finance-and-economics/rss.xml",
     "name":"The Economist","src":"t-eco","cat":"macro","br":False,"weight":1.4},
    {"url":"https://www.bloomberg.com/feed/podcast/etf-iq.xml",
     "name":"Bloomberg ETF","src":"t-bl","cat":"macro","br":False,"weight":1.3},

    # ── ECONOMIA BR (8) ────────────────────────────────────────────────────────
    {"url":"https://valor.globo.com/rss/ultimas-noticias",
     "name":"Valor Economico","src":"t-ve","cat":"macro","br":True,"weight":1.5},
    {"url":"https://g1.globo.com/rss/g1/economia/",
     "name":"G1 Economia","src":"t-g1","cat":"macro","br":True,"weight":1.4},
    {"url":"https://economia.estadao.com.br/rss/",
     "name":"Estadao Eco","src":"t-est","cat":"macro","br":True,"weight":1.3},
    {"url":"https://www.uol.com.br/economia/rss.xml",
     "name":"UOL Economia","src":"t-uol","cat":"macro","br":True,"weight":1.1},
    {"url":"https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
     "name":"Agencia Brasil","src":"t-agb","cat":"macro","br":True,"weight":1.2},
    {"url":"https://exame.com/economia/feed/",
     "name":"Exame Economia","src":"t-exe","cat":"macro","br":True,"weight":1.3},
    {"url":"https://www.infomoney.com.br/mercados/feed/",
     "name":"InfoMoney Mercados","src":"t-imm","cat":"macro","br":True,"weight":1.3},
    {"url":"https://braziljournal.com/feed",
     "name":"Brazil Journal","src":"t-bj","cat":"macro","br":True,"weight":1.4},

    # ── GEOPOLÍTICA (15) ───────────────────────────────────────────────────────
    {"url":"https://feeds.reuters.com/reuters/worldNews",
     "name":"Reuters World","src":"t-rtw","cat":"geo","br":False,"weight":1.7},
    {"url":"https://apnews.com/rss/world-news",
     "name":"AP World","src":"t-apw","cat":"geo","br":False,"weight":1.6},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml",
     "name":"Al Jazeera","src":"t-aj","cat":"geo","br":False,"weight":1.4},
    {"url":"https://foreignpolicy.com/feed/",
     "name":"Foreign Policy","src":"t-fp","cat":"geo","br":False,"weight":1.5},
    {"url":"https://rss.politico.com/politics-news.xml",
     "name":"Politico","src":"t-po","cat":"geo","br":False,"weight":1.4},
    {"url":"https://thehill.com/news/feed/",
     "name":"The Hill","src":"t-th","cat":"geo","br":False,"weight":1.2},
    {"url":"https://www.defenseone.com/rss/all/",
     "name":"Defense One","src":"t-d1","cat":"geo","br":False,"weight":1.5},
    {"url":"https://feeds.washingtonpost.com/rss/world",
     "name":"Washington Post","src":"t-wp","cat":"geo","br":False,"weight":1.5},
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
     "name":"NYT World","src":"t-nyt","cat":"geo","br":False,"weight":1.5},
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
     "name":"NYT US","src":"t-nytu","cat":"geo","br":False,"weight":1.4},
    {"url":"https://feeds.bbci.co.uk/news/world/rss.xml",
     "name":"BBC World","src":"t-bbc","cat":"geo","br":False,"weight":1.5},
    {"url":"https://www.theguardian.com/world/rss",
     "name":"The Guardian","src":"t-grd","cat":"geo","br":False,"weight":1.4},
    {"url":"https://www.economist.com/international/rss.xml",
     "name":"Economist World","src":"t-ecow","cat":"geo","br":False,"weight":1.4},
    {"url":"https://rss.dw.com/rss/en-all",
     "name":"Deutsche Welle","src":"t-dw","cat":"geo","br":False,"weight":1.2},
    {"url":"https://feeds.a.dj.com/rss/RSSWorldNews.xml",
     "name":"WSJ World","src":"t-wsjw","cat":"geo","br":False,"weight":1.4},
]

# ── KEYWORDS ──────────────────────────────────────────────────────────────────
CRYPTO_KW = [
    "bitcoin","btc","ethereum","eth","crypto","cripto","blockchain","defi","nft",
    "stablecoin","altcoin","web3","satoshi","halving","wallet","exchange","binance",
    "coinbase","kraken","solana","xrp","ripple","cardano","token","mining","mineracao",
    "hodl","bull","bear","lightning","taproot","ordinals","rune","layer2","protocol",
    "dao","yield","liquidity","strategy","microstrategy","saylor","etf","spot",
    "futures","derivative","options","onchain","on-chain","mvrv","hash rate"
]
MACRO_KW = [
    "fed","federal reserve","interest rate","taxa de juros","inflation","inflacao",
    "gdp","pib","recession","recessao","treasury","tesouro","dollar","dolar",
    "monetary","jerome powell","cpi","pce","nasdaq","s&p","dow jones","ibovespa",
    "selic","bacen","banco central","tariff","tarifa","trade war","oil","petroleo",
    "commodity","unemployment","payroll","debt","divida","fiscal","bond","rate cut",
    "rate hike","wall street","ipo","earnings","imf","fmi","world bank","brics",
    "g7","g20","moody","fitch","credit rating"
]
GEO_KW = [
    "war","guerra","conflict","conflito","attack","ataque","missile","missil",
    "military","militar","nato","otan","ukraine","ucrania","russia","iran",
    "israel","gaza","hamas","sanctions","sancoes","nuclear","troops","tropas",
    "pentagon","kremlin","zelensky","putin","trump","tariff","china","taiwan",
    "north korea","coreia","middle east","oriente medio","coup","golpe","drone",
    "election","eleicao","protest","manifestacao","submarine","hypersonic"
]

# ── CACHE ─────────────────────────────────────────────────────────────────────
_cache: dict = {}
_source_stats: dict = {}

def _cache_valid() -> bool:
    if "ts" not in _cache:
        return False
    return (datetime.now(timezone.utc) - _cache["ts"]).seconds < CACHE_TTL

# ── RSS FETCH ─────────────────────────────────────────────────────────────────
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "media":   "http://search.yahoo.com/mrss/",
}

async def fetch_feed(client: httpx.AsyncClient, feed: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CriptoBrasilIntel/5.0; RSS reader)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        r = await client.get(feed["url"], timeout=12, follow_redirects=True, headers=headers)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = root.findall(".//item")
        articles = []
        for item in items[:8]:
            title   = (item.findtext("title") or "").strip()
            link    = (item.findtext("link") or "").strip()
            desc    = (item.findtext("description") or "").strip()
            pub     = (item.findtext("pubDate") or
                       item.findtext("dc:date", namespaces=NS) or "").strip()
            content = (item.findtext("content:encoded", namespaces=NS) or desc).strip()
            if not title or not link:
                continue
            desc_clean = re.sub(r"<[^>]+>", " ", desc)
            desc_clean = re.sub(r"\s+", " ", desc_clean).strip()[:400]
            articles.append({
                "title":   title,
                "link":    link,
                "desc":    desc_clean,
                "pub":     pub,
                "src":     feed["name"],
                "src_key": feed["src"],
                "cat":     feed["cat"],
                "br":      feed["br"],
                "weight":  feed["weight"],
                "content": re.sub(r"<[^>]+>", "", content)[:800],
            })
        stat = _source_stats.get(feed["name"], {"ok": 0, "err": 0})
        _source_stats[feed["name"]] = {
            "ok": stat["ok"] + 1, "err": stat["err"],
            "last": datetime.now(timezone.utc).isoformat(), "count": len(articles)
        }
        return articles
    except Exception as e:
        stat = _source_stats.get(feed["name"], {"ok": 0, "err": 0})
        _source_stats[feed["name"]] = {
            "ok": stat["ok"], "err": stat["err"] + 1,
            "last": datetime.now(timezone.utc).isoformat(),
            "count": 0, "error": str(e)[:120]
        }
        log.warning(f"Feed [{feed['name']}]: {str(e)[:80]}")
        return []

# ── SCORING & CLASSIFY ────────────────────────────────────────────────────────
def score_article(a: dict) -> int:
    text  = (a["title"] + " " + a["desc"]).lower()
    score = int(a["weight"] * 50)
    kw_map = {"cripto": CRYPTO_KW, "macro": MACRO_KW, "geo": GEO_KW}
    for kw in kw_map.get(a["cat"], []):
        if kw in text:
            score += 4
    if a["br"]:
        score += 10
    today = datetime.now().strftime("%d %b %Y")
    if today in a.get("pub", ""):
        score += 20
    for s in ["bitcoin","btc","saylor","strategy","halving","etf","$"]:
        if s in text:
            score += 3
    return min(score, 150)

def classify_content(a: dict) -> str:
    text = (a["title"] + " " + a["desc"]).lower()
    if a["cat"] == "geo":   return "geo"
    if a["cat"] == "macro": return "macro"
    if a["br"]:             return "br"
    bull_kw = ["alta","subiu","sobe","atingiu","supera","recorde","bullish",
               "surge","rally","all-time","ath","soars","rises","gains","comprou"]
    bear_kw = ["queda","caiu","cai","despenca","colapso","crash","panico",
               "bearish","falls","drops","plunge","selloff","decline","correction"]
    edu_kw  = ["como","por que","o que e","guia","entenda","aprenda",
               "tutorial","what is","how to","why","explained","guide"]
    bull_s = sum(1 for k in bull_kw if k in text)
    bear_s = sum(1 for k in bear_kw if k in text)
    edu_s  = sum(1 for k in edu_kw if k in text)
    if edu_s >= 2:   return "edu"
    if bull_s > bear_s: return "bull"
    if bear_s > bull_s: return "bear"
    return "edu"

def dedupe(articles: list) -> list:
    seen = set()
    out  = []
    for a in articles:
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

# ── BUILD PIPELINE ────────────────────────────────────────────────────────────
async def build_news(n_cripto=12, n_macro=8, n_geo=6) -> list:
    log.info(f"Fetching {len(FEEDS)} RSS feeds...")
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch_feed(client, f) for f in FEEDS], return_exceptions=True
        )
    all_articles = []
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)

    for a in all_articles:
        a["cls"]   = classify_content(a)
        a["score"] = score_article(a)

    all_articles = dedupe(all_articles)
    all_articles.sort(key=lambda x: x["score"], reverse=True)

    cripto = [a for a in all_articles if a["cat"] == "cripto"][:n_cripto]
    macro  = [a for a in all_articles if a["cat"] == "macro"][:n_macro]
    geo    = [a for a in all_articles if a["cat"] == "geo"][:n_geo]

    selected = cripto + macro + geo
    selected.sort(key=lambda x: x["score"], reverse=True)

    enriched = []
    for i, a in enumerate(selected[:MAX_ART]):
        a["id"] = i + 1
        try:
            enriched.append(enrich_article(a))
        except Exception as e:
            log.warning(f"Enrich failed: {e}")
            a["fmt"] = "EDUCATIVO_CONTEXTO"
            enriched.append(a)

    log.info(f"Done: {len(enriched)} artigos ({len(cripto)}c/{len(macro)}m/{len(geo)}g)")
    return enriched

# ── BACKGROUND REFRESH ────────────────────────────────────────────────────────
async def auto_refresh():
    while True:
        try:
            data = await build_news()
            _cache["news"] = data
            _cache["ts"]   = datetime.now(timezone.utc)
            log.info(f"Cache refreshed: {len(data)} artigos")
        except Exception as e:
            log.error(f"Cache refresh error: {e}")
        await asyncio.sleep(CACHE_TTL)

@app.on_event("startup")
async def startup():
    log.info(f"Cripto Brasil Intel v5 | {len(FEEDS)} fontes | porta {PORT}")
    asyncio.create_task(auto_refresh())

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service":      "Cripto Brasil Intel API",
        "version":      "5.0.0",
        "sources":      len(FEEDS),
        "formats":      len(FORMATS),
        "cache_ok":     _cache_valid(),
        "articles":     len(_cache.get("news", [])),
        "last_refresh": str(_cache.get("ts", "aguardando...")),
        "docs":         "/docs",
    }

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "ts":     datetime.now(timezone.utc).isoformat(),
        "cache":  _cache_valid(),
        "articles": len(_cache.get("news", [])),
    }

@app.get("/api/news")
async def news(
    limit:   int  = Query(24, ge=1, le=60),
    cripto:  int  = Query(12, ge=0, le=30),
    macro:   int  = Query(8,  ge=0, le=20),
    geo:     int  = Query(6,  ge=0, le=20),
    refresh: bool = Query(False),
):
    """Retorna noticias enriquecidas com conteudo editorial."""
    if not _cache_valid() or refresh:
        try:
            data = await build_news(cripto, macro, geo)
            _cache["news"] = data
            _cache["ts"]   = datetime.now(timezone.utc)
        except Exception as e:
            if _cache.get("news"):
                log.warning(f"Stale cache: {e}")
            else:
                raise HTTPException(503, f"RSS fetch falhou: {e}")

    return {
        "articles":  _cache["news"][:limit],
        "total":     len(_cache.get("news", [])),
        "cached_at": str(_cache.get("ts", "")),
        "sources":   len(FEEDS),
    }

@app.get("/api/sources")
async def sources_status():
    """Testa todos os feeds em tempo real."""
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch_feed(client, f) for f in FEEDS], return_exceptions=True
        )
    return {"sources": [{
        "name":   FEEDS[i]["name"],
        "cat":    FEEDS[i]["cat"],
        "br":     FEEDS[i]["br"],
        "weight": FEEDS[i]["weight"],
        "ok":     isinstance(r, list),
        "count":  len(r) if isinstance(r, list) else 0,
        "error":  str(r) if not isinstance(r, list) else None,
    } for i, r in enumerate(results)]}

@app.get("/api/sources/stats")
async def sources_stats():
    return {"stats": _source_stats, "total_feeds": len(FEEDS)}

@app.get("/api/editorial_formats")
async def editorial_formats():
    return {"formats": {
        k: {
            "desc":        v["desc"],
            "viral_bonus": v["viral_bonus"],
            "best_for":    v["best_for"],
            "trigger_kw":  v["trigger_kw"][:5],
        } for k, v in FORMATS.items()
    }}

# ── QUEUE ─────────────────────────────────────────────────────────────────────
class QueueAction(BaseModel):
    hash: str

def _load_queue() -> list:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except:
            return []
    return []

def _save_queue(q: list):
    QUEUE_FILE.write_text(json.dumps(q, indent=2, default=str))

@app.get("/api/queue")
async def get_queue():
    q = _load_queue()
    return {
        "queue":    q,
        "total":    len(q),
        "pending":  sum(1 for x in q if x.get("status") == "READY_TO_APPROVE"),
        "approved": sum(1 for x in q if "APPROVED" in x.get("status", "")),
    }

@app.post("/api/queue/build")
async def build_queue():
    """Gera/atualiza fila com artigos atuais."""
    articles = _cache.get("news", [])
    if not articles:
        articles = await build_news()
    q = _load_queue()
    existing = {x["hash"] for x in q}
    added = 0
    for a in articles[:8]:
        h = hashlib.md5(a["title"].encode()).hexdigest()[:12]
        if h in existing:
            continue
        q.append({
            "hash":        h,
            "title":       a["title"],
            "src":         a.get("src", ""),
            "cat":         a.get("cat", ""),
            "fmt":         a.get("fmt", "EDUCATIVO_CONTEXTO"),
            "hook":        a.get("hook", ""),
            "caption":     a.get("caption", ""),
            "slides":      a.get("slides", []),
            "reel_script": a.get("reel", {}).get("script", "") if isinstance(a.get("reel"), dict) else "",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=added * 3)).isoformat(),
            "status":      "APPROVED" if AUTO_APPR else "READY_TO_APPROVE",
            "created_at":  datetime.now(timezone.utc).isoformat(),
        })
        existing.add(h)
        added += 1
    _save_queue(q)
    return {"added": added, "total": len(q)}

@app.post("/api/queue/approve")
async def approve_item(action: QueueAction):
    q = _load_queue()
    for item in q:
        if item.get("hash") == action.hash:
            item["status"]      = "APPROVED_MANUAL"
            item["approved_at"] = datetime.now(timezone.utc).isoformat()
            _save_queue(q)
            return {"status": "approved", "hash": action.hash}
    raise HTTPException(404, f"Item {action.hash} nao encontrado")

@app.post("/api/queue/reject")
async def reject_item(action: QueueAction):
    q = _load_queue()
    orig = len(q)
    q = [x for x in q if x.get("hash") != action.hash]
    if len(q) == orig:
        raise HTTPException(404, f"Item {action.hash} nao encontrado")
    _save_queue(q)
    return {"status": "rejected", "removed": orig - len(q)}

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n Cripto Brasil Intel v5")
    print(f"   {len(FEEDS)} fontes RSS · {len(FORMATS)} formatos editoriais")
    print(f"   Cache TTL: {CACHE_TTL}s · Max artigos: {MAX_ART}")
    print(f"   http://localhost:{PORT}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT,
                reload=(ENV == "development"), log_level="info")
