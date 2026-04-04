"""
Banco de Conteúdo Vault Capital — Backend v16
Melhorias: /api/context, /api/editorial/{idx}, /api/warmup, cache granular,
hook dedup persistente, paridade de rotas com Supabase Edge Function.
"""
import asyncio, hashlib, logging, os, re, time, xml.etree.ElementTree as ET
from datetime import datetime, timezone
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
PORT        = int(os.getenv("PORT", 8000))
MAX_ART     = int(os.getenv("MAX_ARTICLES", 40))
CLAUDE_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

app = FastAPI(title="Vault Capital News Backend v16")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 2.2 CACHE GRANULAR COM TTL DIFERENCIADO ───────────────────────────────────
_cache: dict = {
    "articles":       [],
    "articles_ts":    0.0,
    "market_ctx":     {},
    "market_ctx_ts":  0.0,
}
CACHE_TTL_ARTICLES = int(os.getenv("CACHE_TTL", 1200))  # 20 min para artigos
CACHE_TTL_MARKET   = 300                                  # 5 min para contexto

# Cache de editorial por hash do título (sobrevive ao refresh de artigos)
_editorial_cache: dict[str, dict] = {}

def title_hash(title: str) -> str:
    return hashlib.md5(title[:80].lower().encode()).hexdigest()[:12]

# ── 2.4 HOOK DEDUP PERSISTENTE ────────────────────────────────────────────────
_recent_hooks: list[str] = []
MAX_HOOK_CACHE = 50

def hook_similarity(a: str, b: str) -> float:
    wa = {w for w in a.lower().split() if len(w) > 4}
    wb = {w for w in b.lower().split() if len(w) > 4}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))

def is_hook_duplicate(hook: str) -> bool:
    return any(hook_similarity(hook, h) > 0.5 for h in _recent_hooks)

def register_hook(hook: str) -> None:
    _recent_hooks.insert(0, hook)
    if len(_recent_hooks) > MAX_HOOK_CACHE:
        _recent_hooks.pop()

# ── RSS FEEDS — 60 FONTES ─────────────────────────────────────────────────────
FEEDS = [
    # CRIPTO BR
    {"url":"https://livecoins.com.br/feed/",              "name":"Livecoins",        "src":"lv",   "cat":"cripto","br":True, "w":2.2},
    {"url":"https://criptofacil.com/feed/",               "name":"CriptoFacil",      "src":"cf",   "cat":"cripto","br":True, "w":2.0},
    {"url":"https://www.cointimes.com.br/feed/",          "name":"Cointimes",        "src":"ct2",  "cat":"cripto","br":True, "w":1.9},
    {"url":"https://br.cointelegraph.com/rss",            "name":"CT BR",            "src":"ctbr", "cat":"cripto","br":True, "w":2.0},
    {"url":"https://portaldobitcoin.uol.com.br/feed/",    "name":"Portal Bitcoin",   "src":"pb",   "cat":"cripto","br":True, "w":1.8},
    {"url":"https://www.infomoney.com.br/guias/bitcoin/feed/","name":"InfoMoney",    "src":"im",   "cat":"cripto","br":True, "w":1.9},
    {"url":"https://www.beincrypto.com.br/feed/",         "name":"BeInCrypto BR",    "src":"bic",  "cat":"cripto","br":True, "w":1.7},
    {"url":"https://exame.com/cripto/feed/",              "name":"Exame Cripto",     "src":"ex",   "cat":"cripto","br":True, "w":1.8},
    {"url":"https://www.moneytimes.com.br/feed/",         "name":"MoneyTimes",       "src":"mt",   "cat":"cripto","br":True, "w":1.5},
    {"url":"https://blocknews.com.br/feed/",              "name":"Blocknews",        "src":"bn",   "cat":"cripto","br":True, "w":1.4},
    {"url":"https://www.cnnbrasil.com.br/economia/mercados/feed/","name":"CNN Brasil","src":"cnn", "cat":"cripto","br":True, "w":1.6},
    {"url":"https://abcripto.com.br/feed/",               "name":"ABcripto",         "src":"abc",  "cat":"cripto","br":True, "w":1.5},
    # CRIPTO GLOBAL
    {"url":"https://cointelegraph.com/rss",               "name":"Cointelegraph",    "src":"ct",   "cat":"cripto","br":False,"w":2.2},
    {"url":"https://www.coindesk.com/arc/outboundfeeds/rss/","name":"CoinDesk",      "src":"cd",   "cat":"cripto","br":False,"w":2.5},
    {"url":"https://theblock.co/rss.xml",                 "name":"The Block",        "src":"tb",   "cat":"cripto","br":False,"w":2.3},
    {"url":"https://decrypt.co/feed",                     "name":"Decrypt",          "src":"dc",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://blockworks.co/feed",                  "name":"Blockworks",       "src":"bw",   "cat":"cripto","br":False,"w":2.1},
    {"url":"https://bitcoinmagazine.com/.rss/full/",      "name":"Bitcoin Magazine",  "src":"bm",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://cryptoslate.com/feed/",               "name":"CryptoSlate",      "src":"cs",   "cat":"cripto","br":False,"w":1.9},
    {"url":"https://www.newsbtc.com/feed/",               "name":"NewsBTC",          "src":"nb",   "cat":"cripto","br":False,"w":1.7},
    {"url":"https://cryptobriefing.com/feed/",            "name":"Crypto Briefing",  "src":"cb",   "cat":"cripto","br":False,"w":1.8},
    {"url":"https://www.crypto.news/feed/",               "name":"Crypto.news",      "src":"cn",   "cat":"cripto","br":False,"w":1.9},
    {"url":"https://dlnews.com/rss.xml",                  "name":"DL News",          "src":"dl",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://u.today/rss",                         "name":"U.Today",          "src":"ut",   "cat":"cripto","br":False,"w":1.6},
    {"url":"https://coinmarketcap.com/rss/news.xml",      "name":"CMC News",         "src":"cmc",  "cat":"cripto","br":False,"w":1.8},
    {"url":"https://ambcrypto.com/feed/",                 "name":"AMBCrypto",        "src":"amb",  "cat":"cripto","br":False,"w":1.6},
    {"url":"https://beincrypto.com/feed/",                "name":"BeInCrypto",       "src":"bic2", "cat":"cripto","br":False,"w":1.8},
    {"url":"https://protos.com/feed/",                    "name":"Protos",           "src":"pr",   "cat":"cripto","br":False,"w":1.9},
    # MACRO GLOBAL
    {"url":"https://www.cnbc.com/id/20910258/device/rss/rss.html","name":"CNBC",     "src":"cnbc", "cat":"macro", "br":False,"w":1.8},
    {"url":"https://feeds.a.dj.com/rss/RSSMarketsMain.xml","name":"WSJ Markets",    "src":"wsj",  "cat":"macro", "br":False,"w":1.9},
    {"url":"https://www.ft.com/rss/home/us",              "name":"Financial Times",  "src":"ft",   "cat":"macro", "br":False,"w":1.8},
    {"url":"https://www.economist.com/finance-and-economics/rss.xml","name":"Economist","src":"ec","cat":"macro","br":False,"w":1.7},
    {"url":"https://apnews.com/rss/business",             "name":"AP Business",      "src":"ap",   "cat":"macro", "br":False,"w":1.6},
    # MACRO BR
    {"url":"https://valor.globo.com/rss/ultimas-noticias","name":"Valor Econômico", "src":"ve",   "cat":"macro", "br":True, "w":1.8},
    {"url":"https://g1.globo.com/rss/g1/economia/",       "name":"G1 Economia",      "src":"g1",   "cat":"macro", "br":True, "w":1.6},
    {"url":"https://economia.estadao.com.br/rss/",        "name":"Estadão Economia", "src":"est",  "cat":"macro", "br":True, "w":1.6},
    {"url":"https://agenciabrasil.ebc.com.br/rss/economia/feed.xml","name":"Agência Brasil","src":"ab","cat":"macro","br":True,"w":1.4},
    # GEO
    {"url":"https://apnews.com/rss/world-news",           "name":"AP World",         "src":"apw",  "cat":"geo",   "br":False,"w":1.7},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml",   "name":"Al Jazeera",       "src":"aj",   "cat":"geo",   "br":False,"w":1.6},
    {"url":"https://rss.politico.com/politics-news.xml",  "name":"Politico",         "src":"pol",  "cat":"geo",   "br":False,"w":1.7},
    {"url":"https://feeds.washingtonpost.com/rss/world",  "name":"Washington Post",  "src":"wp",   "cat":"geo",   "br":False,"w":1.7},
]

NS = {"content":"http://purl.org/rss/1.0/modules/content/","dc":"http://purl.org/dc/elements/1.1/"}

# ── VIRAL SCORING ─────────────────────────────────────────────────────────────
VIRAL_TRIGGERS = {
    "contradicao":    (["acumulou","comprou mais","ignorou","enquanto","mesmo assim","apesar","contra o consenso"], 25),
    "numero_absurdo": (["bilhões","trilhões","bilhão","trilhão","milhões","$1","$2","$5","$10","$100","r$","recorde","histórico","nunca","primeiro","inédito"], 20),
    "impacto_br":     (["brasil","brasileiro","real","reais","selic","bacen","receita federal","iof","b3"], 18),
    "virada":         (["ath","all-time","máxima","mínima","topo","fundo","ciclo","halving","supera","bate","atinge"], 15),
    "urgencia":       (["agora","hoje","urgente","breaking","alerta","semana","horas","dias"], 12),
    "personagem":     (["saylor","strategy","microstrategy","trump","blackrock","fidelity","powell","fed","etf"], 10),
    "conflito":       (["proibiu","baniu","regulação","processo","sec","fraude","colapso","crash","falência","hack"], 8),
}
CRYPTO_BONUS = ["bitcoin","btc","ethereum","eth","cripto","crypto","blockchain","defi","stablecoin","solana","halving","etf","whale","baleia"]

def score_article(a: dict, fear_greed: int = 50) -> int:
    text  = (a["title"] + " " + a.get("desc","")).lower()
    score = min(int(a.get("w", 1.0) * 20), 50)
    for _, (keywords, bonus) in VIRAL_TRIGGERS.items():
        if any(kw in text for kw in keywords):
            score += bonus
    score += sum(3 for kw in CRYPTO_BONUS if kw in text)
    if a.get("br"):
        score += 10
    try:
        from email.utils import parsedate_to_datetime
        age_h = (datetime.now(timezone.utc) - parsedate_to_datetime(a.get("pub",""))).total_seconds() / 3600
        if age_h <= 6:  score += 30
        elif age_h <= 24: score += 20
        elif age_h <= 72: score += 10
    except:
        pass
    # Fear & Greed amplifier
    is_bull = any(w in text for w in ["alta","bull","recorde","ath","inflow"])
    is_bear = any(w in text for w in ["queda","crash","bear","outflow","liquidaç"])
    if fear_greed > 70 and is_bull: score = int(score * 1.3)
    if fear_greed < 30 and is_bear: score = int(score * 1.3)
    return min(int(score * 100 / 180), 99)

# ── HTML CLEANER ──────────────────────────────────────────────────────────────
def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text or '')
    for ent, rep in [('&amp;','&'),('&lt;','<'),('&gt;','>'),('&quot;','"'),('&#39;',"'"),('&nbsp;',' ')]:
        text = text.replace(ent, rep)
    return re.sub(r'\s+', ' ', text).strip()[:500]

# ── CLASSIFY ──────────────────────────────────────────────────────────────────
def classify_content(a: dict) -> str:
    text = (a["title"] + " " + a.get("desc","")).lower()
    if a.get("cat") == "geo": return "geo"
    if a.get("cat") == "macro": return "br" if a.get("br") else "macro"
    if a.get("br"): return "br"
    bull = sum(1 for kw in ["alta","subiu","recorde","ath","rally","pump","bull"] if kw in text)
    bear = sum(1 for kw in ["baixa","caiu","crash","falência","fraude","hack","bear","dump"] if kw in text)
    edu  = sum(1 for kw in ["entenda","como funciona","o que é","guia","aprenda","análise"] if kw in text)
    if bull > bear and bull > edu: return "bull"
    if bear > bull: return "bear"
    return "edu"

# ── DEDUPE ────────────────────────────────────────────────────────────────────
def dedupe(articles: list) -> list:
    seen, out = set(), []
    for a in articles:
        key = re.sub(r'\W', '', a["title"][:60].lower())
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

# ── 2.3 CONTEXTO DE MERCADO CACHEADO ─────────────────────────────────────────
async def get_market_context(client: httpx.AsyncClient) -> dict:
    now = time.time()
    if now - _cache["market_ctx_ts"] < CACHE_TTL_MARKET and _cache["market_ctx"]:
        return _cache["market_ctx"]

    ctx: dict = {}
    try:
        r = await client.get(
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum&vs_currencies=usd&include_7d_change=true",
            timeout=8.0
        )
        cg = r.json()
        ctx["btc_price"]     = cg.get("bitcoin", {}).get("usd", 0)
        ctx["btc_change_7d"] = round(cg.get("bitcoin", {}).get("usd_7d_change", 0), 2)
        ctx["eth_price"]     = cg.get("ethereum", {}).get("usd", 0)
    except Exception as e:
        log.warning(f"[ctx] CoinGecko: {e}")

    try:
        r = await client.get("https://api.alternative.me/fng/?limit=1", timeout=6.0)
        fg = r.json()
        ctx["fear_greed"]       = int(fg["data"][0]["value"])
        ctx["fear_greed_label"] = fg["data"][0]["value_classification"]
    except Exception as e:
        log.warning(f"[ctx] FearGreed: {e}")

    try:
        r = await client.get("https://api.coingecko.com/api/v3/global", timeout=8.0)
        gl = r.json()
        ctx["btc_dominance"] = round(gl["data"]["market_cap_percentage"]["btc"], 1)
    except Exception as e:
        log.warning(f"[ctx] Dominância: {e}")

    fg_val = ctx.get("fear_greed", 50)
    if   fg_val > 75: ctx["top_narrative"] = "euforia institucional — ATH cycle em andamento"
    elif fg_val > 60: ctx["top_narrative"] = "momentum positivo — capital institucional entrando"
    elif fg_val > 45: ctx["top_narrative"] = "acumulação silenciosa — smart money posicionando"
    elif fg_val > 30: ctx["top_narrative"] = "incerteza macro — mercado aguardando catalisador"
    elif fg_val > 15: ctx["top_narrative"] = "capitulação varejista — possível fundo de ciclo"
    else:             ctx["top_narrative"] = "pânico extremo — zonas históricas de compra ativadas"

    ctx["generated_at"]     = datetime.now(timezone.utc).isoformat()
    _cache["market_ctx"]    = ctx
    _cache["market_ctx_ts"] = now
    return ctx

# ── FETCH RSS ─────────────────────────────────────────────────────────────────
async def fetch_feed(client: httpx.AsyncClient, feed: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; VaultCapitalBot/1.0)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        r = await client.get(feed["url"], timeout=15, follow_redirects=True, headers=headers)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        articles = []
        for item in root.findall(".//item")[:12]:
            title = clean_html(item.findtext("title") or "")
            link  = (item.findtext("link") or "").strip()
            desc  = clean_html(
                item.findtext("description") or
                item.findtext("content:encoded", NS) or
                item.findtext("content", NS) or ""
            )
            pub = (item.findtext("pubDate") or item.findtext("dc:date", NS) or "").strip()
            if not title or len(title) < 5: continue
            articles.append({
                "title": title, "link": link, "desc": desc, "pub": pub,
                "name": feed["name"], "src": feed["src"],
                "cat": feed["cat"], "br": feed["br"], "w": feed["w"],
            })
        return articles
    except Exception as e:
        log.debug(f"Feed failed {feed['name']}: {e}")
        return []

# ── TRANSLATION ───────────────────────────────────────────────────────────────
_translate_cache: dict = {}

async def translate_to_ptbr(text: str, client: httpx.AsyncClient) -> str:
    if not text or len(text) < 5: return text
    pt_indicators = ["bitcoin","de bitcoin","do bitcoin","para o","com o","não","também","quando","depois","caiu","subiu"]
    if any(ind in text.lower() for ind in pt_indicators): return text
    ck = hashlib.md5(text.encode()).hexdigest()[:8]
    if ck in _translate_cache: return _translate_cache[ck]
    try:
        r = await client.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client":"gtx","sl":"auto","tl":"pt","dt":"t","q":text},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            translated = "".join(part[0] for part in data[0] if part[0])
            _translate_cache[ck] = translated
            return translated
    except Exception:
        pass
    return text

# ── CLAUDE EDITORIAL GENERATION ───────────────────────────────────────────────
CLAUDE_SYSTEM = """Você é editor de conteúdo cripto para Instagram brasileiro. Gera conteúdo viral de altíssima qualidade.

REGRAS ABSOLUTAS:
- NUNCA "vai subir", "moon", "compra agora"
- NUNCA cole o texto da notícia — reescreva com ângulo editorial
- SEMPRE use dados com período exato: "Março de 2026: Bitcoin a $65K"
- SEMPRE inclua slide AVISO HONESTO obrigatório
- Último slide SEMPRE termina: "Salva esse carrossel. Não pela análise. Pelo registro de como você estava se sentindo agora."

CARROSSEL (8 slides):
- SLIDE 1 CAPA: contradição impossível que prende. Ex: "A empresa perdeu $6B em 90 dias. O que fez depois?"
- SLIDES 2-3: contexto histórico com DATAS e NÚMEROS reais
- SLIDES 4-5: análise profunda + mecanismo
- SLIDE 6: AVISO HONESTO — o que pode dar errado
- SLIDES 7-8: conclusão + fechamento obrigatório

REEL (35-45 segundos, ~150 palavras):
- Abertura (5s): 1 frase que provoca contradição ou número absurdo
- Desenvolvimento (25s): 3 dados concretos com períodos específicos
- Aviso honesto (5s): "Agora o aviso..."
- Fechamento (5s): "Salva esse vídeo. Não pela previsão. Pelo lembrete."

Retorne SOMENTE JSON válido, sem markdown:
{"hook":"frase 1 linha","post_feed":"post completo 150-200 palavras","caption":"legenda instagram com hashtags","cta":"call to action 1 linha","slides":[{"role":"capa","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"corpo","t":"texto","fonte":"fonte"},{"role":"fechamento","t":"Salva esse carrossel. Não pela análise. Pelo registro de como você estava se sentindo agora.\\n\\n@vaultcapitaloficial","fonte":"@vaultcapitaloficial"}],"reel":{"script":"roteiro completo","dur":"45s","music":"sugestão de música","cap":"caption com hook e hashtags"},"dalle_prompt":"prompt DALL-E --ar 9:16"}"""

async def generate_with_claude(article: dict, ctx: dict, client: httpx.AsyncClient) -> dict | None:
    if not CLAUDE_KEY: return None

    th = title_hash(article.get("title",""))
    if th in _editorial_cache:
        return _editorial_cache[th]

    btc_ref = ""
    if ctx.get("btc_price"):
        btc_ref = f"Contexto atual: BTC a ${ctx['btc_price']:,.0f}, Fear & Greed {ctx.get('fear_greed','?')} ({ctx.get('fear_greed_label','')})."

    prompt = f"""Notícia para conteúdo viral Instagram:

TÍTULO: {article.get("title","")}
FONTE: {article.get("name","")}
CATEGORIA: {article.get("cls","edu")}
VIRAL SCORE: {article.get("score",50)}/99
CONTEXTO: {article.get("desc","")[:600]}
{btc_ref}

Gere carrossel 8 slides + reel 45s + post + hook para Instagram @vaultcapitaloficial.
Público: investidor brasileiro 25-45 anos, cripto e finanças."""

    try:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":CLAUDE_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":CLAUDE_MODEL,"max_tokens":3000,"system":CLAUDE_SYSTEM,"messages":[{"role":"user","content":prompt}]},
            timeout=30,
        )
        if r.status_code == 200:
            raw  = r.json()["content"][0]["text"]
            raw  = re.sub(r'^```json\s*|\s*```$', '', raw.strip())
            data = __import__('json').loads(raw)

            # Hook dedup
            hook = data.get("hook","")
            if hook and is_hook_duplicate(hook):
                log.warning(f"Hook duplicado para '{article['title'][:40]}', mantendo mesmo assim")
            if hook:
                register_hook(hook)

            data["editorial_complete"] = bool(data.get("hook") and len(data.get("slides",[]))>=8 and data.get("reel",{}).get("script",""))
            _editorial_cache[th] = data
            return data
    except Exception as e:
        log.warning(f"Claude generation failed for '{article.get('title','')[:40]}': {e}")
    return None

# ── BUILD NEWS ────────────────────────────────────────────────────────────────
async def build_news() -> list:
    log.info(f"Fetching {len(FEEDS)} RSS feeds...")
    async with httpx.AsyncClient() as client:
        # Contexto de mercado primeiro
        ctx = await get_market_context(client)
        fg_val = ctx.get("fear_greed", 50)

        # Feeds em paralelo
        feed_results = await asyncio.gather(*[fetch_feed(client, f) for f in FEEDS], return_exceptions=True)
        all_articles = [a for r in feed_results if isinstance(r, list) for a in r]
        log.info(f"Raw articles: {len(all_articles)}")

        # Tradução para PT-BR
        for a in all_articles:
            if not a.get("br") and a.get("title"):
                a["title"] = await translate_to_ptbr(a["title"], client)

        # Score, classify, dedup, sort
        for a in all_articles:
            a["cls"]   = classify_content(a)
            a["score"] = score_article(a, fg_val)
        all_articles = dedupe(all_articles)
        all_articles.sort(key=lambda x: x["score"], reverse=True)
        selected = all_articles[:MAX_ART]

        # Gera editorial Claude para top 15
        log.info("Gerando editorial Claude para top artigos...")
        top = selected[:15]
        generated = await asyncio.gather(*[generate_with_claude(a, ctx, client) for a in top], return_exceptions=True)
        for a, gen in zip(top, generated):
            if isinstance(gen, dict):
                for field in ["hook","post_feed","cta","caption","slides","reel","dalle_prompt","editorial_complete"]:
                    if gen.get(field):
                        a[field] = gen[field]
                a["_claude_generated"] = True

        # Buildback para artigos sem editorial
        for a in selected:
            if not a.get("editorial_complete"):
                a.setdefault("hook", a["title"])
                a.setdefault("editorial_complete", False)

        # 1.7 — editorial_idx e market_context
        for i, a in enumerate(selected):
            a["id"] = i + 1
            a["editorial_idx"] = i
            a["src_key"] = a.get("src","")

    _cache["articles"]    = selected
    _cache["articles_ts"] = time.time()
    log.info(f"Done: {len(selected)} artigos, {sum(1 for a in selected if a.get('_claude_generated'))} com Claude")
    return selected

# ── BACKGROUND REFRESH ────────────────────────────────────────────────────────
async def auto_refresh():
    # Warm up imediato ao iniciar
    try:
        data = await build_news()
        log.info(f"Warm-up: {len(data)} artigos")
    except Exception as e:
        log.error(f"Warm-up error: {e}")
    while True:
        await asyncio.sleep(CACHE_TTL_ARTICLES)
        try:
            data = await build_news()
            log.info(f"Auto-refresh: {len(data)} artigos")
        except Exception as e:
            log.error(f"Auto-refresh error: {e}")

@app.on_event("startup")
async def startup():
    asyncio.create_task(auto_refresh())

# ════════════════════════════════════════════════════════════════════════════════
# ENDPOINTS — paridade total com Supabase Edge Function (index.ts)
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "Vault Capital News Backend",
        "version": "v16",
        "sources": len(FEEDS),
        "articles": len(_cache.get("articles", [])),
        "cache_age_s": int(time.time() - _cache["articles_ts"]) if _cache["articles_ts"] else None,
    }

@app.get("/api/health")
async def health():
    arts = _cache.get("articles", [])
    if not arts:
        try:
            arts = await build_news()
        except Exception as e:
            raise HTTPException(503, str(e))
    return {
        "ok": True,
        "version": "v16",
        "articles": len(arts),
        "sources": len(FEEDS),
        "claude": bool(CLAUDE_KEY),
        "cache_age_s": int(time.time() - _cache["articles_ts"]) if _cache["articles_ts"] else None,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

# ── 2.5 WARMUP ────────────────────────────────────────────────────────────────
@app.get("/api/warmup")
async def warmup():
    """Acorda o servidor (Railway/Render cold start). Chamado pelo frontend no DOMContentLoaded."""
    return {"ok": True, "warmed": True, "ts": datetime.now(timezone.utc).isoformat()}

# ── 2.3 CONTEXTO DE MERCADO ───────────────────────────────────────────────────
@app.get("/api/context")
async def context():
    """Retorna contexto de mercado atual (BTC, ETH, Fear & Greed, dominância). Cacheado 5min."""
    async with httpx.AsyncClient() as client:
        ctx = await get_market_context(client)
    return {"context": ctx, "ts": datetime.now(timezone.utc).isoformat()}

# ── NEWS ──────────────────────────────────────────────────────────────────────
@app.get("/api/news")
async def news(limit: int = Query(40, ge=1, le=60), refresh: bool = Query(False)):
    now = time.time()
    stale = (now - _cache["articles_ts"]) > CACHE_TTL_ARTICLES
    if refresh or stale or not _cache.get("articles"):
        try:
            await build_news()
        except Exception as e:
            if _cache.get("articles"):
                log.warning(f"Usando cache stale: {e}")
            else:
                raise HTTPException(503, f"RSS fetch failed: {e}")
    articles = _cache.get("articles", [])[:limit]
    async with httpx.AsyncClient() as client:
        ctx = await get_market_context(client)
    return {
        "articles":     articles,
        "total":        len(_cache.get("articles",[])),
        "cached_at":    datetime.fromtimestamp(_cache["articles_ts"], tz=timezone.utc).isoformat() if _cache["articles_ts"] else None,
        "sources":      len(FEEDS),
        "groq_enabled": False,
        "claude":       bool(CLAUDE_KEY),
        "cache_hit":    not (refresh or stale),
        "market_context": ctx,
    }

# ── EDITORIAL SOB DEMANDA ─────────────────────────────────────────────────────
@app.get("/api/editorial/{idx}")
async def editorial(idx: int):
    """Gera (ou retorna do cache) editorial completo para o artigo no índice idx."""
    articles = _cache.get("articles", [])
    if idx < 0 or idx >= len(articles):
        raise HTTPException(404, f"Artigo não encontrado no índice {idx}")

    article = articles[idx]
    # Se já tem editorial completo, retorna direto
    if article.get("editorial_complete"):
        return article

    # Gera com Claude
    async with httpx.AsyncClient() as client:
        ctx = await get_market_context(client)
        gen = await generate_with_claude(article, ctx, client)

    if gen:
        for field in ["hook","post_feed","cta","caption","slides","reel","dalle_prompt","editorial_complete"]:
            if gen.get(field) is not None:
                article[field] = gen[field]
        article["_claude_generated"] = True
        _cache["articles"][idx] = article

    return article

# ── PUBLISHER QUEUE ───────────────────────────────────────────────────────────
_queue: list[dict] = []

@app.get("/api/queue")
async def get_queue():
    return {"queue": _queue, "total": len(_queue)}

@app.post("/api/queue/approve")
async def approve_queue(item: dict):
    _queue.append({**item, "status":"approved", "ts": datetime.now(timezone.utc).isoformat()})
    return {"ok": True}

@app.post("/api/queue/reject")
async def reject_queue(item: dict):
    global _queue
    _queue = [q for q in _queue if q.get("id") != item.get("id")]
    return {"ok": True}

@app.get("/api/sources")
async def sources():
    return {"feeds": [{"name":f["name"],"url":f["url"],"cat":f["cat"],"br":f["br"],"w":f["w"]} for f in FEEDS]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
