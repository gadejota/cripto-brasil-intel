"""
Banco de Conteúdo Vault Capital — Backend v15
Fixes: viral scoring, Claude API content gen, PT-BR translation, new viral sources
"""
import asyncio, hashlib, logging, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
PORT        = int(os.getenv("PORT", 8000))
CACHE_TTL   = int(os.getenv("CACHE_TTL", 1800))   # 30min
MAX_ART     = int(os.getenv("MAX_ARTICLES", 40))
CLAUDE_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

app = FastAPI(title="Vault Capital News Backend v15")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache: dict = {}

# ── RSS FEEDS — 60 FONTES ─────────────────────────────────────────────────────
# Pesos: viral_potential = quão virais são as notícias dessa fonte no Instagram
FEEDS = [
    # ── CRIPTO BR — máxima relevância Instagram ──────────────────────────────
    {"url":"https://livecoins.com.br/feed/",              "name":"Livecoins",         "src":"t-lv",   "cat":"cripto","br":True, "w":2.2},
    {"url":"https://criptofacil.com/feed/",               "name":"CriptoFacil",       "src":"t-cf",   "cat":"cripto","br":True, "w":2.0},
    {"url":"https://www.cointimes.com.br/feed/",          "name":"Cointimes",         "src":"t-ct2",  "cat":"cripto","br":True, "w":1.9},
    {"url":"https://br.cointelegraph.com/rss",            "name":"CT BR",             "src":"t-ctbr", "cat":"cripto","br":True, "w":2.0},
    {"url":"https://portaldobitcoin.uol.com.br/feed/",    "name":"Portal Bitcoin",    "src":"t-pb",   "cat":"cripto","br":True, "w":1.8},
    {"url":"https://www.infomoney.com.br/guias/bitcoin/feed/","name":"InfoMoney Cripto","src":"t-im","cat":"cripto","br":True, "w":1.9},
    {"url":"https://www.beincrypto.com.br/feed/",         "name":"BeInCrypto BR",     "src":"t-bic",  "cat":"cripto","br":True, "w":1.7},
    {"url":"https://exame.com/cripto/feed/",              "name":"Exame Cripto",      "src":"t-ex",   "cat":"cripto","br":True, "w":1.8},
    {"url":"https://www.moneytimes.com.br/feed/",         "name":"MoneyTimes",        "src":"t-mt",   "cat":"cripto","br":True, "w":1.5},
    {"url":"https://blocknews.com.br/feed/",              "name":"Blocknews",         "src":"t-bn",   "cat":"cripto","br":True, "w":1.4},
    {"url":"https://www.cnnbrasil.com.br/economia/mercados/feed/","name":"CNN Brasil","src":"t-cnn","cat":"cripto","br":True, "w":1.6},
    {"url":"https://abcripto.com.br/feed/",               "name":"ABcripto",          "src":"t-abc",  "cat":"cripto","br":True, "w":1.5},

    # ── CRIPTO GLOBAL — alta viralidade ──────────────────────────────────────
    {"url":"https://cointelegraph.com/rss",               "name":"Cointelegraph",     "src":"t-ct",   "cat":"cripto","br":False,"w":2.2},
    {"url":"https://www.coindesk.com/arc/outboundfeeds/rss/","name":"CoinDesk",       "src":"t-cd",   "cat":"cripto","br":False,"w":2.5},
    {"url":"https://theblock.co/rss.xml",                 "name":"The Block",         "src":"t-tb",   "cat":"cripto","br":False,"w":2.3},
    {"url":"https://decrypt.co/feed",                     "name":"Decrypt",           "src":"t-dc",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://blockworks.co/feed",                  "name":"Blockworks",        "src":"t-bw",   "cat":"cripto","br":False,"w":2.1},
    {"url":"https://bitcoinmagazine.com/.rss/full/",      "name":"Bitcoin Magazine",  "src":"t-bm",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://cryptoslate.com/feed/",               "name":"CryptoSlate",       "src":"t-cs",   "cat":"cripto","br":False,"w":1.9},
    {"url":"https://www.newsbtc.com/feed/",               "name":"NewsBTC",           "src":"t-nb",   "cat":"cripto","br":False,"w":1.7},
    {"url":"https://cryptobriefing.com/feed/",            "name":"Crypto Briefing",   "src":"t-cb",   "cat":"cripto","br":False,"w":1.8},
    {"url":"https://www.crypto.news/feed/",               "name":"Crypto.news",       "src":"t-cn",   "cat":"cripto","br":False,"w":1.9},
    {"url":"https://dlnews.com/rss.xml",                  "name":"DL News",           "src":"t-dl",   "cat":"cripto","br":False,"w":2.0},
    {"url":"https://u.today/rss",                         "name":"U.Today",           "src":"t-ut",   "cat":"cripto","br":False,"w":1.6},
    {"url":"https://coinmarketcap.com/rss/news.xml",      "name":"CMC News",          "src":"t-cmc",  "cat":"cripto","br":False,"w":1.8},
    {"url":"https://ambcrypto.com/feed/",                 "name":"AMBCrypto",         "src":"t-amb",  "cat":"cripto","br":False,"w":1.6},
    {"url":"https://beincrypto.com/feed/",                "name":"BeInCrypto",        "src":"t-bic2", "cat":"cripto","br":False,"w":1.8},
    {"url":"https://protos.com/feed/",                    "name":"Protos",            "src":"t-pr",   "cat":"cripto","br":False,"w":1.9},

    # ── MACRO GLOBAL ─────────────────────────────────────────────────────────
    {"url":"https://www.cnbc.com/id/20910258/device/rss/rss.html","name":"CNBC Markets","src":"t-cnbc","cat":"macro","br":False,"w":1.8},
    {"url":"https://feeds.a.dj.com/rss/RSSMarketsMain.xml","name":"WSJ Markets",      "src":"t-wsj",  "cat":"macro","br":False,"w":1.9},
    {"url":"https://www.ft.com/rss/home/us",             "name":"Financial Times",    "src":"t-ft",   "cat":"macro","br":False,"w":1.8},
    {"url":"https://www.economist.com/finance-and-economics/rss.xml","name":"Economist","src":"t-ec","cat":"macro","br":False,"w":1.7},
    {"url":"https://apnews.com/rss/business",            "name":"AP Business",        "src":"t-ap",   "cat":"macro","br":False,"w":1.6},

    # ── MACRO BR ─────────────────────────────────────────────────────────────
    {"url":"https://valor.globo.com/rss/ultimas-noticias","name":"Valor Econômico",   "src":"t-ve",   "cat":"macro","br":True, "w":1.8},
    {"url":"https://g1.globo.com/rss/g1/economia/",      "name":"G1 Economia",        "src":"t-g1",   "cat":"macro","br":True, "w":1.6},
    {"url":"https://economia.estadao.com.br/rss/",       "name":"Estadão Economia",   "src":"t-est",  "cat":"macro","br":True, "w":1.6},
    {"url":"https://agenciabrasil.ebc.com.br/rss/economia/feed.xml","name":"Agência Brasil","src":"t-ab","cat":"macro","br":True,"w":1.4},

    # ── GEO / POLÍTICA ────────────────────────────────────────────────────────
    {"url":"https://apnews.com/rss/world-news",          "name":"AP World",           "src":"t-apw",  "cat":"geo","br":False,"w":1.7},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml",  "name":"Al Jazeera",         "src":"t-aj",   "cat":"geo","br":False,"w":1.6},
    {"url":"https://rss.politico.com/politics-news.xml", "name":"Politico",           "src":"t-pol",  "cat":"geo","br":False,"w":1.7},
    {"url":"https://feeds.washingtonpost.com/rss/world", "name":"Washington Post",    "src":"t-wp",   "cat":"geo","br":False,"w":1.7},
]

# ── NAMESPACE XML ─────────────────────────────────────────────────────────────
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "media":   "http://search.yahoo.com/mrss/",
}

# ── KEYWORDS VIRAIS ──────────────────────────────────────────────────────────
VIRAL_TRIGGERS = {
    # Gatilho 1: Contradição emocional (+25)
    "contradicao": ["acumulou","comprou mais","ignorou","enquanto","mesmo assim",
                    "apesar","contra o consenso","foi contra","desafiou","surpreendeu"],
    # Gatilho 2: Número absurdo (+20)
    "numero_absurdo": ["bilhões","trilhões","bilhão","trilhão","milhões","milhão",
                       "bilhao","trilhao","milhao","$1","$2","$5","$10","$100","r$",
                       "1000%","500%","200%","record","recorde","historico","histórico",
                       "nunca","jamais","primeiro","inédito","inedito"],
    # Gatilho 3: Impacto BR (+18)
    "impacto_br": ["brasil","brasileiro","real","reais","selic","bacen","receita federal",
                   "iof","exchange brasileira","mercado brasileiro","investidor br",
                   "b3","bovespa"],
    # Gatilho 4: Virada histórica (+15)
    "virada": ["ath","all-time","máxima","mínima","topo","fundo","ciclo","halving",
               "maior","menor","mais alto","mais baixo","supera","bate","atinge"],
    # Gatilho 5: Urgência (+12)
    "urgencia": ["agora","hoje","urgente","breaking","alerta","atenção","cuidado",
                 "semana","horas","dias","prazo","deadline","vence","expira"],
    # Gatilho 6: Personagem famoso (+10)
    "personagem": ["saylor","michael saylor","strategy","microstrategy","trump",
                   "blackrock","fidelity","elon","musk","bukele","warren","buffett",
                   "powell","fed","etf","vanguard","jpmorgan","goldman"],
    # Gatilho 7: Conflito narrativa (+8)
    "conflito": ["proibiu","baniu","regulação","regulacao","processo","sec",
                 "fraude","colapso","crash","falência","falencia","scam","hack",
                 "roubou","perdeu","caiu","despencou"],
}

CRYPTO_BONUS = ["bitcoin","btc","ethereum","eth","cripto","crypto","blockchain",
                "defi","nft","stablecoin","solana","xrp","cardano","binance",
                "coinbase","halving","onchain","etf","whale","baleia"]

# ── VIRAL SCORING ────────────────────────────────────────────────────────────
def score_article(a: dict) -> int:
    text  = (a["title"] + " " + a.get("desc","")).lower()
    score = 0

    # Base weight (0-50)
    score += min(int(a.get("w", 1.0) * 20), 50)

    # Viral triggers
    for trigger, keywords in VIRAL_TRIGGERS.items():
        bonus = {"contradicao":25,"numero_absurdo":20,"impacto_br":18,
                 "virada":15,"urgencia":12,"personagem":10,"conflito":8}[trigger]
        if any(kw in text for kw in keywords):
            score += bonus

    # Crypto bonus keywords
    score += sum(3 for kw in CRYPTO_BONUS if kw in text)

    # BR bonus
    if a.get("br"):
        score += 10

    # Freshness bonus (last 6h = +30, last 24h = +20, last 72h = +10)
    try:
        from email.utils import parsedate_to_datetime
        pub_dt = parsedate_to_datetime(a.get("pub",""))
        age_h = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
        if age_h <= 6:    score += 30
        elif age_h <= 24: score += 20
        elif age_h <= 72: score += 10
    except:
        pass

    # Normalize to 0-100 scale
    return min(int(score * 100 / 180), 99)

# ── TRANSLATION (PT-BR) ──────────────────────────────────────────────────────
TRANSLATE_CACHE: dict = {}

async def translate_to_ptbr(text: str, client: httpx.AsyncClient) -> str:
    """Traduz texto para PT-BR via Google Translate (unofficial API)."""
    if not text or len(text) < 5:
        return text

    # Check if already Portuguese (contains common PT words)
    pt_indicators = ["bitcoin caiu","bitcoin subiu","de bitcoin","do bitcoin",
                     "para o","com o","para","pela","pelo","dos","das","não",
                     "também","mais","como","muito","quando","depois"]
    text_lower = text.lower()
    if any(ind in text_lower for ind in pt_indicators):
        return text  # Already PT

    # Check cache
    cache_key = hashlib.md5(text.encode()).hexdigest()[:8]
    if cache_key in TRANSLATE_CACHE:
        return TRANSLATE_CACHE[cache_key]

    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client":"gtx","sl":"auto","tl":"pt","dt":"t","q":text}
        r = await client.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            translated = "".join(part[0] for part in data[0] if part[0])
            TRANSLATE_CACHE[cache_key] = translated
            return translated
    except Exception as e:
        log.debug(f"Translation failed: {e}")

    return text  # Return original if translation fails

# ── CONTENT GENERATION WITH CLAUDE ──────────────────────────────────────────
CONTENT_CACHE: dict = {}

CLAUDE_SYSTEM = """Você é editor de conteúdo cripto para Instagram brasileiro. Gera conteúdo viral de altíssima qualidade.

REGRAS ABSOLUTAS:
- NUNCA "vai subir", "moon", "compra agora" - isso é proibido
- NUNCA cole o texto da notícia diretamente - reescreva com ângulo editorial
- SEMPRE use dados com período exato: "Março de 2026: Bitcoin a $65K"
- SEMPRE inclua slide AVISO HONESTO obrigatório
- Último slide SEMPRE termina: "Salva esse carrossel. Não pela análise. Pelo registro de como você estava se sentindo agora."

CARROSSEL (7-8 slides):
- SLIDE 1 CAPA: contradição impossível que prende. Ex: "A empresa perdeu $6B em 90 dias. O que fez depois?" NUNCA apenas "Bitcoin caiu X%"
- SLIDES 2-3: contexto histórico com DATAS e NÚMEROS reais
- SLIDES 4-5: análise profunda + mecanismo
- SLIDE 6: AVISO HONESTO — o que pode dar errado
- SLIDE 7-8: conclusão + fechamento obrigatório

REEL (30-40 segundos, ~120-150 palavras):
- Abertura (5s): 1 frase que provoca contradição ou número absurdo
- Desenvolvimento (20s): 3 dados concretos com períodos específicos
- Aviso honesto (5s): "Agora o aviso..."
- Fechamento (5s): "Salva esse vídeo. Não pela previsão. Pelo lembrete."

Retorne SOMENTE JSON válido, sem markdown:
{"slides":[{"role":"capa","t":"texto"},{"role":"corpo","t":"texto"},{"role":"aviso","t":"⚠️ O AVISO HONESTO\\n\\ntexto"},{"role":"corpo","t":"texto"},{"role":"final","t":"Salva esse carrossel..."}],"reel":{"script":"roteiro completo","dur":"35s","music":"sugestão de música"},"hook":"frase de abertura 1 linha","post":"post completo 150-200 palavras","cta":"call to action 1 linha","caption":"legenda instagram com hashtags"}"""

async def generate_with_claude(article: dict, client: httpx.AsyncClient) -> dict | None:
    """Usa Claude API para gerar carrossel, reel e post de alta qualidade."""
    if not CLAUDE_KEY:
        return None

    cache_key = hashlib.md5(article.get("title","").encode()).hexdigest()[:12]
    if cache_key in CONTENT_CACHE:
        return CONTENT_CACHE[cache_key]

    title   = article.get("title","")
    desc    = article.get("desc","") or article.get("excerpt","") or title
    source  = article.get("name","") or article.get("source","")
    cls     = article.get("cls","edu")
    score   = article.get("score", 50)

    prompt = f"""Notícia para criar conteúdo viral Instagram:

TÍTULO: {title}
FONTE: {source}
CATEGORIA: {cls}
VIRAL SCORE: {score}/100
CONTEXTO: {desc[:600]}

Gere carrossel 7-8 slides + reel 35s + post + hook para Instagram Vault Capital.
P�blico-alvo: investidor brasileiro 25-45 anos, interesse em cripto e finanças.
Tom: analítico, sem hype, baseado em dados, com humor inteligente ocasional."""

    try:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 3000,
                "system": CLAUDE_SYSTEM,
                "messages": [{"role":"user","content":prompt}]
            },
            timeout=30,
        )
        if r.status_code == 200:
            raw = r.json()["content"][0]["text"]
            raw = re.sub(r'^```json\s*|\s*```$','', raw.strip())
            data = __import__('json').loads(raw)
            CONTENT_CACHE[cache_key] = data
            return data
    except Exception as e:
        log.warning(f"Claude generation failed for '{title[:40]}': {e}")

    return None

# ── CLASSIFY CONTENT ─────────────────────────────────────────────────────────
def classify_content(a: dict) -> str:
    text = (a["title"] + " " + a.get("desc","")).lower()
    cat  = a.get("cat","cripto")

    if cat == "geo": return "geo"
    if cat == "macro":
        if a.get("br"): return "br"
        return "macro"
    if a.get("br"):    return "br"

    bull_kw = ["alta","subiu","sobe","topo","record","recorde","atinge","supera",
               "comprou","acumula","cresce","rally","pump","bull"]
    bear_kw = ["baixa","caiu","cai","queda","colapso","crash","falência","falencia",
               "fraude","hack","ban","proibiu","despencou","sell","dump","bear"]
    edu_kw  = ["entenda","como funciona","o que é","explicando","guia","tutorial",
               "aprenda","saiba","descubra","análise","analise"]

    bull = sum(1 for kw in bull_kw if kw in text)
    bear = sum(1 for kw in bear_kw if kw in text)
    edu  = sum(1 for kw in edu_kw  if kw in text)

    if bull > bear and bull > edu:  return "bull"
    if bear > bull:                  return "bear"
    if edu > 0:                      return "edu"
    return "edu"

# ── CLEAN HTML FROM DESCRIPTIONS ─────────────────────────────────────────────
def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>','', text or '')
    text = re.sub(r'&amp;','&', text)
    text = re.sub(r'&lt;','<', text)
    text = re.sub(r'&gt;','>', text)
    text = re.sub(r'&quot;','"', text)
    text = re.sub(r'&#\d+;','', text)
    text = re.sub(r'\s+',' ', text).strip()
    return text[:500]

# ── DEDUPLICATE ───────────────────────────────────────────────────────────────
def dedupe(articles: list) -> list:
    seen, out = set(), []
    for a in articles:
        key = re.sub(r'\W','', (a["title"][:60]).lower())
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out

# ── FETCH ONE RSS FEED ────────────────────────────────────────────────────────
async def fetch_feed(client: httpx.AsyncClient, feed: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; VaultCapitalBot/1.0; +https://vaultcapital.com.br)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        r = await client.get(feed["url"], timeout=15, follow_redirects=True, headers=headers)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = root.findall(".//item")
        articles = []
        for item in items[:12]:
            title = clean_html(item.findtext("title") or "")
            link  = (item.findtext("link") or "").strip()
            desc  = clean_html(
                item.findtext("description") or
                item.findtext(f"content:encoded", namespaces=NS) or
                item.findtext(f"content", namespaces=NS) or ""
            )
            pub = (
                item.findtext("pubDate") or
                item.findtext("dc:date", namespaces=NS) or
                item.findtext("published") or ""
            ).strip()

            if not title or len(title) < 5:
                continue

            articles.append({
                "title": title,
                "link":  link,
                "desc":  desc,
                "pub":   pub,
                "name":  feed["name"],
                "src":   feed["src"],
                "cat":   feed["cat"],
                "br":    feed["br"],
                "w":     feed["w"],
            })
        return articles
    except Exception as e:
        log.debug(f"Feed failed {feed['name']}: {e}")
        return []

# ── BUILD NEWS ────────────────────────────────────────────────────────────────
async def build_news() -> list:
    log.info(f"Fetching {len(FEEDS)} RSS feeds...")

    async with httpx.AsyncClient() as client:
        # Fetch all feeds in parallel
        feed_results = await asyncio.gather(
            *[fetch_feed(client, f) for f in FEEDS],
            return_exceptions=True
        )

        all_articles = []
        for r in feed_results:
            if isinstance(r, list):
                all_articles.extend(r)

        log.info(f"Raw articles: {len(all_articles)}")

        # Translate English titles to PT-BR
        translate_tasks = []
        for a in all_articles:
            if not a.get("br") and a.get("title"):
                translate_tasks.append((a, translate_to_ptbr(a["title"], client)))

        if translate_tasks:
            titles = await asyncio.gather(*[t[1] for t in translate_tasks], return_exceptions=True)
            for (a, _), translated in zip(translate_tasks, titles):
                if isinstance(translated, str) and translated:
                    a["title_en"] = a["title"]  # Keep original
                    a["title"] = translated

        # Score and classify
        for a in all_articles:
            a["cls"]   = classify_content(a)
            a["score"] = score_article(a)

        # Deduplicate and sort
        all_articles = dedupe(all_articles)
        all_articles.sort(key=lambda x: x["score"], reverse=True)

        # Select top articles
        selected = all_articles[:MAX_ART]

        # Generate content with Claude for top 15 articles
        log.info(f"Generating Claude content for top articles...")
        top_articles = selected[:15]

        content_tasks = [generate_with_claude(a, client) for a in top_articles]
        generated = await asyncio.gather(*content_tasks, return_exceptions=True)

        for a, gen in zip(top_articles, generated):
            if isinstance(gen, dict):
                # Apply generated content
                if gen.get("slides") and len(gen["slides"]) >= 4:
                    a["slides"] = gen["slides"]
                if gen.get("reel",{}).get("script"):
                    a["reel"] = gen["reel"]
                if gen.get("hook"):
                    a["hook"] = gen["hook"]
                if gen.get("post"):
                    a["post_feed"] = gen["post"]
                if gen.get("cta"):
                    a["cta"] = gen["cta"]
                if gen.get("caption"):
                    a["caption"] = gen["caption"]
                a["_claude_generated"] = True

        # Add IDs
        for i, a in enumerate(selected):
            a["id"] = i + 1

        log.info(f"Done: {len(selected)} articles, {sum(1 for a in selected if a.get('_claude_generated'))} with Claude content")
        return selected

# ── CACHE HELPERS ─────────────────────────────────────────────────────────────
def _cache_valid() -> bool:
    if "ts" not in _cache:
        return False
    age = (datetime.now(timezone.utc) - _cache["ts"]).total_seconds()
    return age < CACHE_TTL

# ── BACKGROUND REFRESH ────────────────────────────────────────────────────────
async def auto_refresh():
    while True:
        try:
            data = await build_news()
            _cache["news"] = data
            _cache["ts"]   = datetime.now(timezone.utc)
            log.info(f"Cache refreshed: {len(data)} articles")
        except Exception as e:
            log.error(f"Cache refresh error: {e}")
        await asyncio.sleep(CACHE_TTL)

@app.on_event("startup")
async def startup():
    asyncio.create_task(auto_refresh())

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"service":"Vault Capital News Backend","version":"v15",
            "sources":len(FEEDS),"cache_valid":_cache_valid(),
            "cached_at":str(_cache.get("ts",""))}

@app.get("/api/health")
async def health():
    if not _cache_valid() and not _cache.get("news"):
        try:
            data = await build_news()
            _cache["news"] = data
            _cache["ts"]   = datetime.now(timezone.utc)
        except Exception as e:
            raise HTTPException(503, str(e))
    return {
        "status":   "ok",
        "articles": len(_cache.get("news",[])),
        "sources":  len(FEEDS),
        "cached_at":str(_cache.get("ts","")),
        "cache_ttl": CACHE_TTL,
        "claude":   bool(CLAUDE_KEY),
    }

@app.get("/api/news")
async def news(
    limit:   int  = Query(32, ge=1, le=60),
    refresh: bool = Query(False),
):
    if not _cache_valid() or refresh:
        try:
            data = await build_news()
            _cache["news"] = data
            _cache["ts"]   = datetime.now(timezone.utc)
        except Exception as e:
            if _cache.get("news"):
                log.warning(f"Stale cache used: {e}")
            else:
                raise HTTPException(503, f"RSS fetch failed: {e}")

    articles = _cache.get("news",[])[:limit]
    return {
        "articles":  articles,
        "total":     len(_cache.get("news",[])),
        "cached_at": str(_cache.get("ts","")),
        "sources":   len(FEEDS),
    }

@app.get("/api/sources")
async def sources_status():
    return {"feeds": [{"name":f["name"],"url":f["url"],"cat":f["cat"],"br":f["br"],"w":f["w"]} for f in FEEDS]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
