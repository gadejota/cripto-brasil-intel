"""
CRIPTO BRASIL INTEL — Backend v8
==================================
95 fontes RSS · Filtro analista v1 · 72h freshness · Impact scoring 0-3★

FILOSOFIA DO ANALISTA:
  Só passa artigo que um analista de cripto leria com atenção.
  Sem previsão de preço, sem análise gráfica, sem memecoins, sem XRP.
  Só fatos, dados, movimentos, fundamentos e macro.

Variáveis de ambiente:
  PORT=8000           porta do servidor
  CACHE_TTL=900       segundos entre refreshes (padrão 15min)
  MAX_ARTICLES=32     máximo de artigos por request
  ENVIRONMENT=production

Endpoints:
  GET  /api/news?limit=24&cripto=14&macro=8&geo=6
  GET  /api/sources              → status de cada fonte RSS
  GET  /api/health
  GET  /docs
"""

import asyncio, hashlib, json, logging, os, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, Query
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
AUTO_APPR  = os.getenv("AUTO_APPROVE", "false").lower() == "true"
QUEUE_FILE = Path(os.getenv("QUEUE_FILE", "publisher_queue.json"))
ENV        = os.getenv("ENVIRONMENT", "production")
FRESHNESS_H = 72   # horas — artigos mais velhos são descartados

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cripto-intel")

app = FastAPI(
    title="Cripto Brasil Intel API v8",
    description="95 fontes · Filtro analista · 72h freshness · Impact 0-3★",
    version="8.0.0",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════════════════
# 95 FONTES RSS
# Critério: só fontes que cobrem fatos, dados, fundamentos e macro
# ═════════════════════════════════════════════════════════════════════════════
FEEDS = [

    # ── CRIPTO BR — TIER 1 (peso alto, PT-BR, fatos) ─────────────────────────
    {"url":"https://livecoins.com.br/feed/",
     "name":"Livecoins","src":"t-lv","cat":"cripto","br":True,"weight":2.0},
    {"url":"https://criptofacil.com/feed/",
     "name":"CriptoFacil","src":"t-cf","cat":"cripto","br":True,"weight":1.9},
    {"url":"https://br.cointelegraph.com/rss",
     "name":"Cointelegraph BR","src":"t-ctbr","cat":"cripto","br":True,"weight":1.9},
    {"url":"https://www.cointimes.com.br/feed/",
     "name":"Cointimes","src":"t-ct2","cat":"cripto","br":True,"weight":1.7},
    {"url":"https://portaldobitcoin.uol.com.br/feed/",
     "name":"Portal Bitcoin","src":"t-pb","cat":"cripto","br":True,"weight":1.7},
    {"url":"https://exame.com/cripto/feed/",
     "name":"Exame Cripto","src":"t-ex","cat":"cripto","br":True,"weight":1.7},
    {"url":"https://www.infomoney.com.br/guias/bitcoin/feed/",
     "name":"InfoMoney Cripto","src":"t-im","cat":"cripto","br":True,"weight":1.6},
    {"url":"https://www.beincrypto.com.br/feed/",
     "name":"BeInCrypto BR","src":"t-bic","cat":"cripto","br":True,"weight":1.6},
    {"url":"https://www.cnnbrasil.com.br/economia/mercados/feed/",
     "name":"CNN Brasil Cripto","src":"t-cnn","cat":"cripto","br":True,"weight":1.5},
    {"url":"https://blocknews.com.br/feed/",
     "name":"Blocknews","src":"t-bn","cat":"cripto","br":True,"weight":1.4},
    {"url":"https://abcripto.com.br/feed/",
     "name":"ABcripto","src":"t-abc","cat":"cripto","br":True,"weight":1.5},
    {"url":"https://www.moneytimes.com.br/feed/",
     "name":"MoneyTimes","src":"t-mt","cat":"cripto","br":True,"weight":1.4},
    {"url":"https://braziljournal.com/feed",
     "name":"Brazil Journal Cripto","src":"t-bjc","cat":"cripto","br":True,"weight":1.5},

    # ── CRIPTO BR — TIER 2 (blogs de exchanges e institutos BR) ───────────────
    {"url":"https://blog.mercadobitcoin.com.br/feed",
     "name":"Mercado Bitcoin Blog","src":"t-mb","cat":"cripto","br":True,"weight":1.7},
    {"url":"https://hashdex.com/pt-BR/blog/feed",
     "name":"Hashdex Blog","src":"t-hx","cat":"cripto","br":True,"weight":1.6},
    {"url":"https://foxbit.com.br/blog/feed/",
     "name":"Foxbit Blog","src":"t-fb","cat":"cripto","br":True,"weight":1.4},
    {"url":"https://www.bitcointrade.com.br/blog/feed/",
     "name":"BitcoinTrade Blog","src":"t-bt","cat":"cripto","br":True,"weight":1.3},
    {"url":"https://coinext.com.br/blog/feed",
     "name":"Coinext Blog","src":"t-cx","cat":"cripto","br":True,"weight":1.2},
    {"url":"https://www.criptointeligente.com.br/feed/",
     "name":"Cripto Inteligente","src":"t-ci","cat":"cripto","br":True,"weight":1.3},

    # ── CRIPTO GLOBAL — TIER 1 VIRAL (CoinDesk, crypto.news, The Block = prioridade máxima)
    # Essas 4 fontes geram o maior volume de notícias virais no mercado cripto
    {"url":"https://www.coindesk.com/arc/outboundfeeds/rss/",
     "name":"CoinDesk","src":"t-cd","cat":"cripto","br":False,"weight":2.8},
    {"url":"https://crypto.news/feed/",
     "name":"crypto.news","src":"t-crn","cat":"cripto","br":False,"weight":2.5},
    {"url":"https://www.theblock.co/rss.xml",
     "name":"The Block","src":"t-tb","cat":"cripto","br":False,"weight":2.5},
    {"url":"https://cryptonews.com/news/feed/",
     "name":"CryptoNews","src":"t-cn","cat":"cripto","br":False,"weight":2.3},
    {"url":"https://cointelegraph.com/rss",
     "name":"Cointelegraph","src":"t-ct","cat":"cripto","br":False,"weight":2.2},
    {"url":"https://bitcoinmagazine.com/.rss/full/",
     "name":"Bitcoin Magazine","src":"t-bm","cat":"cripto","br":False,"weight":2.0},
    {"url":"https://decrypt.co/feed",
     "name":"Decrypt","src":"t-dc","cat":"cripto","br":False,"weight":1.8},
    {"url":"https://blockworks.co/feed",
     "name":"Blockworks","src":"t-bk","cat":"cripto","br":False,"weight":1.8},
    {"url":"https://thedefiant.io/feed",
     "name":"The Defiant","src":"t-def","cat":"cripto","br":False,"weight":1.6},
    {"url":"https://unchainedcrypto.com/feed/",
     "name":"Unchained Crypto","src":"t-uc","cat":"cripto","br":False,"weight":1.6},
    {"url":"https://coinmarketcap.com/rss/news.xml",
     "name":"CoinMarketCap News","src":"t-cmc","cat":"cripto","br":False,"weight":1.6},
    {"url":"https://dlnews.com/rss.xml",
     "name":"DL News","src":"t-dln","cat":"cripto","br":False,"weight":1.6},

    # ── ON-CHAIN & DADOS (máxima prioridade — raros mas decisivos) ─────────────
    {"url":"https://insights.glassnode.com/rss/",
     "name":"Glassnode Insights","src":"t-gn","cat":"onchain","br":False,"weight":2.5},
    {"url":"https://cryptoquant.com/feed/research",
     "name":"CryptoQuant Research","src":"t-cq","cat":"onchain","br":False,"weight":2.4},
    {"url":"https://messari.io/rss/research",
     "name":"Messari Research","src":"t-ms","cat":"onchain","br":False,"weight":2.3},
    {"url":"https://research.delphi.digital/feed",
     "name":"Delphi Digital","src":"t-dd","cat":"onchain","br":False,"weight":2.3},
    {"url":"https://nansen.ai/research/feed",
     "name":"Nansen Research","src":"t-nn","cat":"onchain","br":False,"weight":2.2},
    {"url":"https://www.chainalysis.com/blog/feed/",
     "name":"Chainalysis Blog","src":"t-ca","cat":"onchain","br":False,"weight":2.0},
    {"url":"https://arcane.no/research/rss",
     "name":"Arcane Research","src":"t-ar","cat":"onchain","br":False,"weight":1.8},

    # ── ETF & INSTITUCIONAL (fluxo de capital real) ───────────────────────────
    {"url":"https://www.etf.com/sections/features-and-news/rss",
     "name":"ETF.com","src":"t-etfc","cat":"etf","br":False,"weight":1.8},
    {"url":"https://www.etftrends.com/crypto-etf-channel/feed/",
     "name":"ETF Trends Crypto","src":"t-etft","cat":"etf","br":False,"weight":1.9},
    {"url":"https://bitcointreasuries.net/feed",
     "name":"Bitcoin Treasuries","src":"t-btr","cat":"etf","br":False,"weight":2.0},
    {"url":"https://www.coindesk.com/arc/outboundfeeds/rss/?category=markets",
     "name":"CoinDesk Markets","src":"t-cdm","cat":"etf","br":False,"weight":1.7},

    # ── CRIPTO GLOBAL — TIER 2 ────────────────────────────────────────────────
    {"url":"https://cryptobriefing.com/feed/",
     "name":"Crypto Briefing","src":"t-cb","cat":"cripto","br":False,"weight":1.3},
    {"url":"https://www.cryptoslate.com/feed/",
     "name":"CryptoSlate","src":"t-cs","cat":"cripto","br":False,"weight":1.3},
    {"url":"https://www.coinbureau.com/feed/",
     "name":"Coin Bureau","src":"t-cbu","cat":"cripto","br":False,"weight":1.4},
    {"url":"https://ambcrypto.com/feed/",
     "name":"AMBCrypto","src":"t-amb","cat":"cripto","br":False,"weight":1.2},
    {"url":"https://beincrypto.com/feed/",
     "name":"BeInCrypto","src":"t-bic2","cat":"cripto","br":False,"weight":1.4},
    {"url":"https://watcher.guru/news/feed",
     "name":"Watcher.Guru","src":"t-wg","cat":"cripto","br":False,"weight":1.3},
    {"url":"https://www.newsbtc.com/feed/",
     "name":"NewsBTC","src":"t-nb","cat":"cripto","br":False,"weight":1.1},
    {"url":"https://u.today/rss",
     "name":"U.Today","src":"t-ut","cat":"cripto","br":False,"weight":1.2},
    {"url":"https://coingape.com/feed/",
     "name":"CoinGape","src":"t-cg","cat":"cripto","br":False,"weight":1.1},

    # ── MACRO EUA — FONTES PRIMÁRIAS ──────────────────────────────────────────
    {"url":"https://www.federalreserve.gov/feeds/press_all.xml",
     "name":"Federal Reserve","src":"t-fed","cat":"macro","br":False,"weight":3.0},
    {"url":"https://www.bls.gov/feed/bls_latest.rss",
     "name":"BLS (CPI/Jobs)","src":"t-bls","cat":"macro","br":False,"weight":2.8},
    {"url":"https://apps.bea.gov/rss/data.xml",
     "name":"BEA (GDP)","src":"t-bea","cat":"macro","br":False,"weight":2.5},
    {"url":"https://home.treasury.gov/system/files/rss/press-releases-rss.xml",
     "name":"US Treasury","src":"t-ust","cat":"macro","br":False,"weight":2.3},

    # ── MACRO EUA — MÍDIA ─────────────────────────────────────────────────────
    {"url":"https://feeds.reuters.com/reuters/businessNews",
     "name":"Reuters Business","src":"t-rt","cat":"macro","br":False,"weight":1.7},
    {"url":"https://www.cnbc.com/id/20910258/device/rss/rss.html",
     "name":"CNBC Economy","src":"t-cnbc","cat":"macro","br":False,"weight":1.6},
    {"url":"https://www.cnbc.com/id/10000664/device/rss/rss.html",
     "name":"CNBC Markets","src":"t-cnbc2","cat":"macro","br":False,"weight":1.5},
    {"url":"https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
     "name":"WSJ Markets","src":"t-wsj","cat":"macro","br":False,"weight":1.6},
    {"url":"https://www.ft.com/rss/home/us",
     "name":"Financial Times","src":"t-ft","cat":"macro","br":False,"weight":1.6},
    {"url":"https://www.economist.com/finance-and-economics/rss.xml",
     "name":"The Economist","src":"t-eco","cat":"macro","br":False,"weight":1.5},
    {"url":"https://feeds.marketwatch.com/marketwatch/topstories/",
     "name":"MarketWatch","src":"t-mw","cat":"macro","br":False,"weight":1.4},
    {"url":"https://apnews.com/rss/business",
     "name":"AP Business","src":"t-ap","cat":"macro","br":False,"weight":1.4},
    {"url":"https://thehill.com/business/feed/",
     "name":"The Hill Business","src":"t-thb","cat":"macro","br":False,"weight":1.2},

    # ── BANCOS CENTRAIS GLOBAIS ────────────────────────────────────────────────
    {"url":"https://www.ecb.europa.eu/rss/press.html",
     "name":"ECB (Banco Central Europeu)","src":"t-ecb","cat":"macro","br":False,"weight":2.5},
    {"url":"https://www.bankofengland.co.uk/rss/news",
     "name":"Bank of England","src":"t-boe","cat":"macro","br":False,"weight":2.2},
    {"url":"https://www.boj.or.jp/en/announcements/rss.xml",
     "name":"Bank of Japan","src":"t-boj","cat":"macro","br":False,"weight":2.2},
    {"url":"https://www.pboc.gov.cn/en/3688110/3688172/rss.xml",
     "name":"PBOC (China)","src":"t-pboc","cat":"macro","br":False,"weight":2.3},

    # ── MACRO BR ──────────────────────────────────────────────────────────────
    {"url":"https://www.bcb.gov.br/api/feed/ptbr/PressRelease",
     "name":"Banco Central BR","src":"t-bcb","cat":"macro","br":True,"weight":2.5},
    {"url":"https://valor.globo.com/rss/ultimas-noticias",
     "name":"Valor Economico","src":"t-ve","cat":"macro","br":True,"weight":1.6},
    {"url":"https://g1.globo.com/rss/g1/economia/",
     "name":"G1 Economia","src":"t-g1","cat":"macro","br":True,"weight":1.4},
    {"url":"https://economia.estadao.com.br/rss/",
     "name":"Estadao Eco","src":"t-est","cat":"macro","br":True,"weight":1.4},
    {"url":"https://agenciabrasil.ebc.com.br/rss/economia/feed.xml",
     "name":"Agencia Brasil","src":"t-agb","cat":"macro","br":True,"weight":1.3},
    {"url":"https://exame.com/economia/feed/",
     "name":"Exame Economia","src":"t-exe","cat":"macro","br":True,"weight":1.4},
    {"url":"https://www.infomoney.com.br/mercados/feed/",
     "name":"InfoMoney Mercados","src":"t-imm","cat":"macro","br":True,"weight":1.4},
    {"url":"https://braziljournal.com/feed",
     "name":"Brazil Journal","src":"t-bj","cat":"macro","br":True,"weight":1.5},

    # ── GEOPOLÍTICA ───────────────────────────────────────────────────────────
    {"url":"https://feeds.reuters.com/reuters/worldNews",
     "name":"Reuters World","src":"t-rtw","cat":"geo","br":False,"weight":1.8},
    {"url":"https://apnews.com/rss/world-news",
     "name":"AP World","src":"t-apw","cat":"geo","br":False,"weight":1.7},
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
     "name":"NYT World","src":"t-nyt","cat":"geo","br":False,"weight":1.6},
    {"url":"https://feeds.bbci.co.uk/news/world/rss.xml",
     "name":"BBC World","src":"t-bbc","cat":"geo","br":False,"weight":1.6},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml",
     "name":"Al Jazeera","src":"t-aj","cat":"geo","br":False,"weight":1.5},
    {"url":"https://foreignpolicy.com/feed/",
     "name":"Foreign Policy","src":"t-fp","cat":"geo","br":False,"weight":1.6},
    {"url":"https://www.defenseone.com/rss/all/",
     "name":"Defense One","src":"t-d1","cat":"geo","br":False,"weight":1.5},
    {"url":"https://feeds.washingtonpost.com/rss/world",
     "name":"Washington Post","src":"t-wp","cat":"geo","br":False,"weight":1.5},
    {"url":"https://rss.politico.com/politics-news.xml",
     "name":"Politico","src":"t-po","cat":"geo","br":False,"weight":1.4},
    {"url":"https://www.theguardian.com/world/rss",
     "name":"The Guardian","src":"t-grd","cat":"geo","br":False,"weight":1.4},
    {"url":"https://thehill.com/news/feed/",
     "name":"The Hill","src":"t-th","cat":"geo","br":False,"weight":1.2},
    {"url":"https://www.economist.com/international/rss.xml",
     "name":"Economist World","src":"t-ecow","cat":"geo","br":False,"weight":1.5},
    {"url":"https://feeds.a.dj.com/rss/RSSWorldNews.xml",
     "name":"WSJ World","src":"t-wsjw","cat":"geo","br":False,"weight":1.5},
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
     "name":"NYT US","src":"t-nytu","cat":"geo","br":False,"weight":1.4},
    {"url":"https://rss.dw.com/rss/en-all",
     "name":"Deutsche Welle","src":"t-dw","cat":"geo","br":False,"weight":1.3},
    {"url":"https://southchinamorningpost.com/rss/section/world.xml",
     "name":"South China Morning Post","src":"t-scmp","cat":"geo","br":False,"weight":1.4},
]

# ═════════════════════════════════════════════════════════════════════════════
# SISTEMA DE FILTRO DO ANALISTA
# ═════════════════════════════════════════════════════════════════════════════

# ── LISTAS NEGRAS — artigo descartado se título ou desc contiver qualquer um ─

# Tópicos irrelevantes (sem exceção)
BLACKLIST_TOPICS = [
    # Memecoins
    "dogecoin","doge/","$doge","shiba","shib","pepe","pepecoin","floki",
    "bonk","meme coin","memecoin","wif","dogwifhat","brett","mog","wojak",
    # XRP / Ripple (política editorial)
    " xrp ","xrp price","xrp surges","xrp drops","ripple price",
    "xrp/usd","xrp chart","xrp analysis","xrp technical",
    # Conteúdo de baixo valor
    "price prediction","price target","price forecast",
    "technical analysis","chart analysis","ta:",
    "support level","resistance level","bullish pattern","bearish pattern",
    "moving average","rsi ","macd ","fibonacci","head and shoulders",
    "cup and handle","double bottom","death cross","golden cross",
    "candlestick","candlestick pattern",
    # Opinião / soft content
    "opinion:","opinion |","editorial:","commentary:",
    "what i think","my take","hot take","unpopular opinion",
    "weekly wrap","weekly recap","monthly recap","this week in",
    "top 10","top 5","top 3 cryptos","best crypto","best altcoin",
    # Stock market (sem relação com cripto)
    "stock split","dividend yield","earnings per share","p/e ratio",
    "quarterly earnings","q3 earnings","q4 earnings","annual report",
    # Outros irrelevantes
    "nft game","play to earn","axie","stepn","nft drop","mint nft",
    "airdrop guide","how to buy","best exchange","review:",
    "casino","gambling","betting","poker",
    "dating","health","fitness","lifestyle",
    "giveaway","win free","free bitcoin",
]

# Domínios ou fontes de baixa qualidade (soft-block — reduz score mas não elimina)
LOW_QUALITY_SIGNALS = [
    "sponsored","advertisement","partner content","press release","pr:",
    "get paid","earn money","make money with crypto",
    "learn how to trade","trading course","master class",
]

# ── LISTA BRANCA — artigo passa mesmo que pareça técnico/especializado ─────
# (garante que notícias de fundamentos não sejam derrubadas pelo blacklist)
WHITELIST_OVERRIDE = [
    "xrp etf","xrp regulatory","xrp sec settlement","xrp cleared",
    "ripple lawsuit","ripple regulation",  # XRP entra só se for regulação
    "doge treasury","dogecoin treasury",   # só se for institucional
]

# ── RELEVÂNCIA — palavras que indicam notícia real de impacto ─────────────
HIGH_IMPACT_KW = [
    # Macro dados reais
    "cpi","pce","nonfarm","payroll","gdp","unemployment rate","inflation data",
    "fomc","rate decision","rate cut","rate hike","interest rate",
    "jobs report","jobs added","unemployment claims",
    "dados de inflação","taxa de juros","pib","selic",
    # Bancos centrais
    "federal reserve","jerome powell","fed chair",
    "ecb","lagarde","bank of japan","boj","bank of england",
    "banco central","bacen","copom",
    # Geopolítica de impacto real
    "oil embargo","sanctions","tariff","trade war","nuclear","strait",
    "war escalation","ceasefire","war","conflict escalation",
    # Bitcoin/Crypto fundamentos
    "etf flows","etf inflow","etf outflow","bitcoin etf",
    "spot etf","institutional","treasury","reserve",
    "bitcoin treasury","corporate bitcoin","microstrategy","strategy",
    "halving","hashrate","mining difficulty","protocol upgrade",
    "network upgrade","hard fork","soft fork","eip-","bip-",
    "staking","liquid staking","restaking","eigenlayer",
    # On-chain dados
    "on-chain","onchain","whale","large transaction","exchange outflow",
    "exchange inflow","realized price","mvrv","nupl","sopr",
    "funding rate","open interest","liquidation","long squeeze","short squeeze",
    "hyperliquid","perpetual","derivatives",
    # Regulação real
    "regulation","regulatory","sec lawsuit","sec approved","cftc",
    "legislation","bill","law","vote","hearing","congress crypto",
    "regulação","regulamentação","marco legal","cvm resolução",
    # Grandes empresas/fundos
    "blackrock","fidelity","vanguard","jpmorgan","goldman sachs",
    "citadel","millennium","point72","cathie wood","ark invest",
    "grayscale","hashdex","21shares","vaneck","invesco",
    # Empresas que compram BTC
    "bought bitcoin","purchases bitcoin","adds bitcoin","bitcoin purchase",
    "bitcoin acquisition","comprou bitcoin","adquiriu bitcoin",
]

MEDIUM_IMPACT_KW = [
    "bitcoin","btc","ethereum","eth","solana","sol","bnb","avalanche",
    "defi","stablecoin","usdt","usdc","tether","circle","tron",
    "lightning network","layer 2","base","arbitrum","optimism",
    "crypto market","crypto exchange","crypto regulation",
    "binance","coinbase","kraken","okx","bybit",
    "trump crypto","trump bitcoin","trump digital assets",
    "el salvador","central africa","legal tender",
]


def is_fresh(pub_str: str, max_hours: int = FRESHNESS_H) -> bool:
    """Retorna True se o artigo foi publicado dentro de max_hours horas."""
    if not pub_str:
        return True  # sem data → não descarta (pode ser fonte sem data)
    try:
        from email.utils import parsedate_to_datetime
        pub_dt = parsedate_to_datetime(pub_str)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        age_h = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
        return age_h <= max_hours
    except:
        return True


def analyst_filter(article: dict) -> dict:
    """
    Filtra e pontua cada artigo como um analista de cripto faria.
    Retorna o artigo com campos extras:
      - analyst_pass: bool — passa ou não
      - analyst_stars: int (0-3) — impacto/importância
      - analyst_sentiment: str ("positivo"/"neutro"/"negativo")
      - analyst_note: str — interpretação breve (1-2 frases)
      - analyst_reject_reason: str (se analyst_pass=False)
    """
    title  = article.get("title", "")
    desc   = article.get("desc", "")
    cat    = article.get("cat", "")
    text   = (title + " " + desc).lower()

    # ── 1. FRESHNESS ──────────────────────────────────────────────────────────
    if not is_fresh(article.get("pub", ""), FRESHNESS_H):
        return {**article,
                "analyst_pass": False,
                "analyst_reject_reason": f"Artigo com mais de {FRESHNESS_H}h",
                "analyst_stars": 0, "analyst_sentiment": "neutro", "analyst_note": ""}

    # ── 2. WHITELIST — passa direto mesmo com palavras suspeitas ──────────────
    whitelist_hit = any(w in text for w in WHITELIST_OVERRIDE)

    # ── 3. BLACKLIST — rejeita imediatamente ──────────────────────────────────
    if not whitelist_hit:
        for bl in BLACKLIST_TOPICS:
            if bl in text:
                return {**article,
                        "analyst_pass": False,
                        "analyst_reject_reason": f"Blacklist: '{bl}'",
                        "analyst_stars": 0, "analyst_sentiment": "neutro", "analyst_note": ""}

    # ── 4. RELEVÂNCIA — precisa de pelo menos 1 sinal de impacto ──────────────
    high_hits   = [kw for kw in HIGH_IMPACT_KW   if kw in text]
    medium_hits = [kw for kw in MEDIUM_IMPACT_KW if kw in text]
    total_hits  = len(high_hits) * 3 + len(medium_hits)

    # On-chain: filtro extra rigoroso
    if cat == "onchain" and not high_hits:
        return {**article,
                "analyst_pass": False,
                "analyst_reject_reason": "On-chain sem sinal de alto impacto",
                "analyst_stars": 0, "analyst_sentiment": "neutro", "analyst_note": ""}

    # Mínimo: precisa de algum sinal relevante (salvo geo/macro primárias)
    primary_sources = article.get("weight", 0) >= 2.0
    if total_hits == 0 and not primary_sources:
        return {**article,
                "analyst_pass": False,
                "analyst_reject_reason": "Sem sinais de impacto real no mercado",
                "analyst_stars": 0, "analyst_sentiment": "neutro", "analyst_note": ""}

    # ── 5. PONTUAÇÃO DE IMPACTO (0-3 estrelas) ────────────────────────────────
    if total_hits >= 9 or any(k in text for k in ["fomc","rate decision","federal reserve statement","cpi data","gdp","payroll report","ban","ban bitcoin","etf approved","etf rejected","legal tender","nuclear","war escalation"]):
        stars = 3
    elif total_hits >= 4 or any(k in text for k in ["etf flows","institutional","treasury","regulation","rate cut","rate hike","central bank","banco central","selic","halving","hard fork","whale","liquidation"]):
        stars = 2
    else:
        stars = 1

    # Penalidade: se tem sinais de baixa qualidade
    for lq in LOW_QUALITY_SIGNALS:
        if lq in text:
            stars = max(0, stars - 1)

    # Se stars=0 após penalidade, passa com 0 mas ainda entra (é raro)

    # ── 6. SENTIMENTO ─────────────────────────────────────────────────────────
    pos_kw = [
        "alta","sobe","subiu","aprovado","approved","comprou","bought","inflow",
        "surges","gains","rally","record","ath","all-time high","bullish",
        "green","grow","recovery","nova máxima","record high","adota",
        "legal tender","approved etf","cleared","settled",
    ]
    neg_kw = [
        "queda","caiu","cai","crash","ban","proibição","rejected","selloff",
        "hack","exploit","breach","liquidation","outflow","short","bearish",
        "red","falls","drops","plunge","correction","recession","downgrade",
        "fraud","scam","arrested","indicted","fined","penalty","sanction",
    ]
    pos_score = sum(1 for k in pos_kw if k in text)
    neg_score = sum(1 for k in neg_kw if k in text)

    if pos_score > neg_score + 1:
        sentiment = "positivo"
    elif neg_score > pos_score + 1:
        sentiment = "negativo"
    else:
        sentiment = "neutro"

    # ── 7. NOTA DO ANALISTA — 1-2 frases diretas ──────────────────────────────
    note = _generate_analyst_note(title, text, cat, stars, sentiment, high_hits, article.get("br", False))

    return {
        **article,
        "analyst_pass":      True,
        "analyst_stars":     stars,
        "analyst_sentiment": sentiment,
        "analyst_note":      note,
        "analyst_reject_reason": "",
    }


def _generate_analyst_note(title: str, text: str, cat: str, stars: int, sentiment: str, high_hits: list, is_br: bool) -> str:
    """Gera nota analítica breve e objetiva — máx 2 frases, sem floreios."""

    # Dados de inflação/emprego EUA
    if any(k in text for k in ["cpi","pce","inflation data","dados de inflação"]):
        if sentiment == "negativo":
            return "Inflação acima do esperado reduz probabilidade de corte de juros pelo Fed. Pressão de curto prazo para Bitcoin e ativos de risco."
        elif sentiment == "positivo":
            return "Inflação dentro ou abaixo do esperado abre espaço para corte de juros. Catalisador positivo para Bitcoin e mercados de risco."
        return "Dado de inflação relevante para a decisão do Fed sobre juros. Impacto direto no apetite por ativos de risco."

    if any(k in text for k in ["nonfarm","payroll","jobs report","unemployment"]):
        if sentiment == "negativo":
            return "Mercado de trabalho fraco eleva risco de recessão. Bitcoin tende a sofrer correlacionado com mercados tradicionais no curto prazo."
        return "Dado de emprego dos EUA relevante para a próxima decisão do Fed. Mercado vai reprecificar expectativas de corte de juros."

    if any(k in text for k in ["gdp","pib","recession"]):
        if "recession" in text or "recessão" in text:
            return "Risco de recessão aumentado. Historicamente Bitcoin cai no curto prazo mas se recupera antes dos ativos tradicionais quando o ciclo vira."
        return "Dado de PIB reprecifica expectativas macroeconômicas. Observar reação do dólar e dos treasuries para entender o impacto em cripto."

    # Fed / Bancos Centrais
    if any(k in text for k in ["fomc","federal reserve","powell","rate decision","rate cut","rate hike"]):
        if "rate cut" in text or "corte" in text:
            return "Corte de juros ou sinalização positiva é bullish para Bitcoin. Reduz o custo de oportunidade e aumenta apetite por risco."
        if "rate hike" in text or "alta de juros" in text:
            return "Alta de juros ou postura hawkish pressiona ativos de risco. Bitcoin pode sofrer no curto prazo junto com Nasdaq."
        return "Comunicado do Fed é o dado mais monitorado do mercado. Qualquer surpresa reprecifica todo o mercado de risco incluindo cripto."

    if any(k in text for k in ["ecb","lagarde","bce"]):
        return "Decisão do Banco Central Europeu afeta apetite global por risco. Mercado de cripto monitora junto com dólar e euro."

    if any(k in text for k in ["boj","bank of japan"]):
        return "Banco do Japão é o maior credor do mundo. Mudança na política monetária japonesa pode gerar onda de liquidez ou contração global."

    if any(k in text for k in ["selic","copom","banco central","bacen"]):
        if sentiment == "negativo":
            return "Selic mais alta aumenta custo de oportunidade do cripto para o investidor brasileiro. Competição direta com renda fixa."
        return "Decisão de política monetária brasileira afeta o custo de oportunidade do cripto em reais. Relevante para o investidor BR."

    # ETF / Institucional
    if any(k in text for k in ["etf flows","etf inflow","etf outflow","bitcoin etf"]):
        if "inflow" in text or "inflows" in text:
            return "Entrada de capital via ETFs é demanda real e estrutural por Bitcoin. Diferente de compra especulativa — saídas são mais lentas."
        if "outflow" in text or "outflows" in text:
            return "Saída de capital dos ETFs indica redução de exposição institucional. Sinal de cautela para o curto prazo."
        return "Fluxo de ETFs de Bitcoin é o dado mais próximo da demanda institucional real. Acompanhar tendência dos últimos 7 dias."

    if any(k in text for k in ["treasury","bitcoin treasury","comprou bitcoin","bought bitcoin","bitcoin purchase","microstrategy","strategy"]):
        return "Empresa acumulando Bitcoin no balanço é demanda permanente de mercado. Sinaliza que gestores corporativos estão adotando BTC como reserva de valor."

    if any(k in text for k in ["blackrock","fidelity","vanguard","jpmorgan","goldman"]):
        return "Movimentação de gestora de grande porte tem peso real no mercado. Sinalizações de gestores desse tamanho precedem fluxo de capital."

    # On-chain
    if any(k in text for k in ["whale","exchange outflow","exchange inflow","onchain","on-chain"]):
        if "outflow" in text:
            return "Saída de Bitcoin das exchanges reduz pressão de venda disponível. Historicamente bullish quando sustentada por mais de 72h."
        if "inflow" in text:
            return "Entrada de Bitcoin nas exchanges pode indicar preparação para venda. Monitorar nos próximos dias."
        return "Dado on-chain relevante. Movimentações de baleias e fluxo de exchanges precedem movimentos de preço de 24 a 72 horas."

    if any(k in text for k in ["mvrv","nupl","sopr","realized price","funding rate","open interest","liquidation"]):
        return "Métrica on-chain de alto valor analítico. Dados como MVRV, SOPR e Open Interest dão contexto de posicionamento do mercado que o preço não mostra."

    if any(k in text for k in ["hyperliquid","large position","perpetual","leverage"]):
        return "Posição alavancada grande em exchange de derivativos pode ser catalisador de volatilidade. Liquidações em cascata são o risco principal."

    # Regulação
    if any(k in text for k in ["regulation","regulatory","sec","cftc","legislation","bill","vote","regulação","cvm","marco legal"]):
        if sentiment == "positivo":
            return "Avanço regulatório positivo reduz incerteza e abre espaço para entrada de capital institucional. Bullish estrutural."
        if sentiment == "negativo":
            return "Regulação restritiva ou indefinição jurídica afasta capital institucional. Impacto negativo de médio prazo."
        return "Desenvolvimento regulatório que merece acompanhamento. Clareza regulatória é pré-requisito para adoção institucional em larga escala."

    # Fundamentos cripto
    if any(k in text for k in ["halving","hard fork","soft fork","protocol upgrade","network upgrade"]):
        return "Mudança de fundamento do protocolo. Eventos como halving e upgrades afetam emissão, segurança e utilidade de longo prazo."

    # Geopolítica
    if any(k in text for k in ["war","guerra","nuclear","oil embargo","sanctions","strait"]):
        if sentiment == "negativo":
            return "Escalada geopolítica gera fuga para dólar e ativos seguros. Bitcoin pode cair no curto prazo junto com equities, mas historicamente recupera primeiro."
        return "Evento geopolítico relevante para mercados globais. Observar impacto no petróleo, dólar e curva de treasuries — a cadeia chega até o Bitcoin."

    if any(k in text for k in ["tariff","trade war","tarifa","guerra comercial"]):
        return "Tarifas e guerra comercial geram inflação importada e reduzem crescimento. Postura do Fed fica mais hawkish. Pressão para Bitcoin no curto prazo."

    # Trump
    if "trump" in text:
        return "Declarações de Trump movem mercados de forma imprevisível. Observar o contexto específico — impacto direto pode ser em setores ou em percepção de risco geral."

    # BR específico
    if is_br:
        return "Notícia com impacto direto para o investidor brasileiro. Contexto de câmbio, Selic e regulação local são determinantes para o cripto em reais."

    # Default por sentimento
    if stars == 3:
        return "Notícia de alto impacto para os mercados cripto. Acompanhar reação nas próximas 6-12 horas."
    if stars == 2:
        return "Notícia relevante com potencial de mover o mercado. Monitorar."
    return "Notícia de contexto. Relevante para o quadro macro/fundamentalista, sem impacto imediato de preço esperado."


# ═════════════════════════════════════════════════════════════════════════════
# VIRAL SCORING — 7 gatilhos × multiplicador de tier
#
# Baseado no guia editorial de curadoria:
#   TIER 1 (1.3x): dado primário — on-chain, Fed, BLS, Bacen, SEC filings
#   TIER 2 (1.2x): análise institucional — CoinDesk, The Block, InfoMoney
#   TIER 3 (1.0x): amplificação — Cointelegraph, Decrypt, mainstream
#   TIER 4 (0.8x): social/sinal — não entra nos feeds, ignorado
#
#   G1 Contradição emocional    25 pts
#   G2 Número absurdo + contexto 20 pts
#   G3 Impacto BR direto         18 pts
#   G4 Virada histórica          15 pts
#   G5 Padrão histórico          12 pts
#   G6 Conflito de narrativa     10 pts
#   G7 Urgência com prazo         8 pts
#
#   Score final = soma_gatilhos × tier_multiplier
#   Escala: 90-100 MEGA | 75-89 ALTO | 60-74 MÉDIO-ALTO | 45-59 MÉDIO | <45 BAIXO
# ═════════════════════════════════════════════════════════════════════════════

# ── Tier por src_key ──────────────────────────────────────────────────────────
# Tier 1: fontes que GERAM o fato (on-chain real, macro oficial)
_TIER1_SRCS = {
    "t-gn",   # Glassnode
    "t-cq",   # CryptoQuant
    "t-ms",   # Messari Research
    "t-dd",   # Delphi Digital
    "t-nn",   # Nansen Research
    "t-ca",   # Chainalysis
    "t-fed",  # Federal Reserve
    "t-bls",  # BLS (CPI/Jobs)
    "t-bea",  # BEA (GDP)
    "t-ust",  # US Treasury
    "t-bcb",  # Banco Central BR
    "t-ecb",  # ECB
    "t-boe",  # Bank of England
    "t-boj",  # Bank of Japan
    "t-pboc", # PBOC China
    "t-btr",  # Bitcoin Treasuries (dados oficiais)
}

# Tier 2: análise institucional premium
_TIER2_SRCS = {
    "t-cd",   # CoinDesk
    "t-cdm",  # CoinDesk Markets
    "t-tb",   # The Block
    "t-bk",   # Blockworks
    "t-ar",   # Arcane Research
    "t-lv",   # Livecoins
    "t-im",   # InfoMoney Cripto
    "t-ex",   # Exame Cripto
    "t-mb",   # Mercado Bitcoin Blog
    "t-hx",   # Hashdex Blog
    "t-etft", # ETF Trends Crypto
    "t-etfc", # ETF.com
    "t-crn",  # crypto.news
    "t-cn",   # CryptoNews
}

def _tier_multiplier(a: dict) -> float:
    src = a.get("src_key", a.get("src", ""))
    cat = a.get("cat", "")
    if src in _TIER1_SRCS or cat == "onchain":
        return 1.3
    if src in _TIER2_SRCS:
        return 1.2
    return 1.0

# ── Keyword lists por gatilho ─────────────────────────────────────────────────

# G1 — Contradição emocional: mercado em pânico + dado positivo, ou vice-versa
_G1_PANIC   = ["fear","medo","panic","crash","colapso","despenca","selloff",
               "queda","cai","bear","baixa","caiu","plunge","rout","bloodbath"]
_G1_CONTRA  = ["comprou","bought","purchases","acquires","adds","accumulate",
               "inflow","acumulou","aumentou","subiu","record","máxima","high",
               "aprovado","approved","reserve","reserva","treasury","tesouraria"]

# G2 — Número absurdo + contexto
_G2_BIG_NUM = [r"\$[\d]+[bm]",r"[\d]+\s*bilh",r"[\d]+\s*trilh",r"[\d]+\s*milh",
               r"[\d]+%",r"us\$\s*[\d]",r"r\$\s*[\d]"]
_G2_CONTEXT = ["histórico","histórica","recorde","record","all-time","ath",
               "nunca antes","primeira vez","first time","ciclo","cycle",
               "fear","greed","on-chain","onchain"]

# G3 — Impacto BR direto
_G3_BR = ["iof","selic","real/dólar","receita federal","drex","bacen",
          "banco central","b3","tributação","tributar","imposto","cripto brasil",
          "exchange brasileira","exchange br","regulação brasil","regulamentação",
          "cvm","cpf","declarar","declaração","r$","reais","real","brasileiro",
          "brasil","brazil","br"]

# G4 — Virada histórica
_G4_FIRST = ["primeiro","primeira","first","pioneiro","inédito","inédita",
             "nunca antes","inaugural","histórico","landmark","milestone",
             "reserva soberana","sovereign reserve","lei federal","federal law",
             "conta no fed","fed account","banco federal","federal bank"]

# G5 — Padrão histórico documentado
_G5_HIST = ["ciclo anterior","ciclos anteriores","2018","2020","2022",
            "bear market anterior","halving anterior","histórico de","em 2018",
            "em 2020","em 2022","padrão de ciclo","nas últimas","vezes na história",
            "times in history","historically","historicamente"]

# G6 — Conflito de narrativa
_G6_CONTRA_NARR = ["kraken","coinbase","aprovado","approved","comprou","bought",
                   "reserva","reserve","etf","institutional","institucional",
                   "blackrock","fidelity","strategy","microstrategy","saylor",
                   "governo","government","lei","law","bill","regulamentou",
                   "stablecoin act","genius act","bitcoin act"]

# G7 — Urgência com prazo
_G7_URGENCY = ["prazo","deadline","data limite","até","by march","by april",
               "by june","by july","by august","30 dias","60 dias","90 dias",
               "próximos","próximas","meses","agosto","setembro","outubro",
               "novembro","dezembro","janeiro","fevereiro","março","abril","maio",
               "reunião","vote","voting","decisão","decision","hearing","2025","2026"]


def score_article(a: dict) -> dict:
    """
    Calcula o viral score usando os 7 gatilhos do guia editorial.
    Retorna dict com score final (0-100) e breakdown dos gatilhos ativados.
    """
    title = (a.get("title") or "").lower()
    desc  = (a.get("desc")  or "").lower()
    text  = title + " " + desc
    cat   = a.get("cat", "")
    br    = a.get("br", False)
    pub   = a.get("pub", "")

    import re

    gatilhos = {}

    # ── G1: Contradição emocional (25 pts) ───────────────────────────────────
    has_panic  = any(kw in text for kw in _G1_PANIC)
    has_contra = any(kw in text for kw in _G1_CONTRA)
    # Contradição = pânico + sinal positivo, ou compra institucional em bear
    if (has_panic and has_contra) or        (any(k in text for k in ["comprou","bought","purchases","reserve","treasury"]) and
        any(k in text for k in ["fear","medo","bear","queda","baixa","crash"])):
        gatilhos["G1_contradicao_emocional"] = 25

    # ── G2: Número absurdo + contexto (20 pts) ───────────────────────────────
    has_big_num = any(re.search(p, text) for p in _G2_BIG_NUM)
    has_context = any(kw in text for kw in _G2_CONTEXT)
    if has_big_num and has_context:
        gatilhos["G2_numero_absurdo_contexto"] = 20
    elif has_big_num:
        gatilhos["G2_numero_absurdo_contexto"] = 10  # número sem contexto vale metade

    # ── G3: Impacto BR direto (18 pts) ───────────────────────────────────────
    if br or any(kw in text for kw in _G3_BR):
        gatilhos["G3_impacto_br_direto"] = 18

    # ── G4: Virada histórica (15 pts) ────────────────────────────────────────
    if any(kw in text for kw in _G4_FIRST):
        gatilhos["G4_virada_historica"] = 15

    # ── G5: Padrão histórico documentado (12 pts) ────────────────────────────
    if any(kw in text for kw in _G5_HIST):
        gatilhos["G5_padrao_historico"] = 12

    # ── G6: Conflito de narrativa (10 pts) ───────────────────────────────────
    # Notícia bullish/institucional em momento de narrativa negativa dominante
    if any(kw in text for kw in _G6_CONTRA_NARR):
        if any(k in text for k in ["aprovado","approved","comprou","bought","reserve",
                                    "lei","law","bill","regulamentou","account","conta"]):
            gatilhos["G6_conflito_narrativa"] = 10

    # ── G7: Urgência com prazo (8 pts) ───────────────────────────────────────
    if any(kw in text for kw in _G7_URGENCY):
        gatilhos["G7_urgencia_prazo"] = 8

    # ── Bônus de recência (publicado hoje vale mais) ──────────────────────────
    today = datetime.now().strftime("%d %b %Y")
    if today in pub:
        gatilhos["bonus_hoje"] = 8

    # ── Score base + multiplicador de tier ───────────────────────────────────
    score_base = sum(gatilhos.values())
    tier_mult  = _tier_multiplier(a)
    score_final = min(100, round(score_base * tier_mult))

    # Garantia mínima: fontes primárias sempre passam um limiar base
    if a.get("cat") == "onchain" and score_final < 30:
        score_final = 30

    # Classificação verbal
    if score_final >= 90:
        classificacao = "MEGA_VIRAL"
    elif score_final >= 75:
        classificacao = "ALTO_VIRAL"
    elif score_final >= 60:
        classificacao = "MEDIO_ALTO"
    elif score_final >= 45:
        classificacao = "MEDIO"
    else:
        classificacao = "BAIXO"

    return {
        "score": score_final,
        "gatilhos": gatilhos,
        "tier_mult": tier_mult,
        "classificacao": classificacao,
    }


# ═════════════════════════════════════════════════════════════════════════════
# CLASSIFY CONTENT
# ═════════════════════════════════════════════════════════════════════════════
def classify_content(a: dict) -> str:
    text = (a["title"] + " " + a["desc"]).lower()
    cat  = a.get("cat", "cripto")
    if cat == "geo":     return "geo"
    if cat == "macro":   return "macro"
    if cat == "onchain": return "edu"
    if cat == "etf":     return "bull"
    if a.get("br"):      return "br"

    bull_kw = ["alta","subiu","sobe","atingiu","supera","recorde","bullish","surge","rally",
               "all-time","ath","soars","rises","gains","comprou","bought","inflow","approved"]
    bear_kw = ["queda","caiu","cai","despenca","colapso","crash","bearish","falls","drops",
               "plunge","selloff","decline","correction","hack","exploit","ban","rejected","outflow"]
    edu_kw  = ["como","por que","o que é","guia","entenda","aprenda","explica","what is",
               "how to","why","explained","understand","fundamentals","protocol","upgrade"]

    bull_s = sum(1 for k in bull_kw if k in text)
    bear_s = sum(1 for k in bear_kw if k in text)
    edu_s  = sum(1 for k in edu_kw  if k in text)

    if edu_s >= 2:       return "edu"
    if bull_s > bear_s:  return "bull"
    if bear_s > bull_s:  return "bear"
    return "edu"


def dedupe(articles: list) -> list:
    seen = set()
    out  = []
    for a in articles:
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())[:70]
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# CACHE
# ─────────────────────────────────────────────────────────────────────────────
_cache: dict = {}
_source_stats: dict = {}

def _cache_valid() -> bool:
    if "ts" not in _cache:
        return False
    return (datetime.now(timezone.utc) - _cache["ts"]).seconds < CACHE_TTL


# ─────────────────────────────────────────────────────────────────────────────
# RSS FETCH
# ─────────────────────────────────────────────────────────────────────────────
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "media":   "http://search.yahoo.com/mrss/",
}

async def fetch_feed(client: httpx.AsyncClient, feed: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CriptoBrasilIntel/8.0; +https://criptobrasil.intel)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        r = await client.get(feed["url"], timeout=12, follow_redirects=True, headers=headers)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = root.findall(".//item")
        articles = []
        for item in items[:10]:
            title   = (item.findtext("title") or "").strip()
            link    = (item.findtext("link") or "").strip()
            desc    = (item.findtext("description") or "").strip()
            pub     = (item.findtext("pubDate") or
                       item.findtext("dc:date", namespaces=NS) or "").strip()
            content = (item.findtext("content:encoded", namespaces=NS) or desc).strip()
            if not title or not link:
                continue
            desc_clean = re.sub(r"<[^>]+>", " ", desc)
            desc_clean = re.sub(r"\s+", " ", desc_clean).strip()[:600]
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
                "content": re.sub(r"<[^>]+>", "", content)[:1000],
            })
        stat = _source_stats.get(feed["name"], {"ok": 0, "err": 0})
        _source_stats[feed["name"]] = {
            "ok": stat["ok"] + 1, "err": stat["err"],
            "last": datetime.now(timezone.utc).isoformat(), "count": len(articles),
        }
        return articles
    except Exception as e:
        stat = _source_stats.get(feed["name"], {"ok": 0, "err": 0})
        _source_stats[feed["name"]] = {
            "ok": stat["ok"], "err": stat["err"] + 1,
            "last": datetime.now(timezone.utc).isoformat(),
            "count": 0, "error": str(e)[:120],
        }
        log.warning(f"Feed [{feed['name']}]: {str(e)[:80]}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# BUILD PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
async def build_news(n_cripto=14, n_macro=8, n_geo=6) -> list:
    log.info(f"Fetching {len(FEEDS)} RSS feeds...")
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[fetch_feed(client, f) for f in FEEDS], return_exceptions=True
        )

    all_articles = []
    for r in results:
        if isinstance(r, list):
            all_articles.extend(r)

    log.info(f"Raw: {len(all_articles)} artigos brutos")

    # Classify + aliases primeiro
    for a in all_articles:
        a["cls"]         = classify_content(a)
        a["_cls"]        = a["cls"]
        a["excerpt"]     = a.get("desc", a.get("content",""))[:500]
        a["source_name"] = a.get("src","")
        a["link"]        = a.get("link", a.get("url","#"))

    # Dedupe antes do filtro
    all_articles = dedupe(all_articles)

    # ── FILTRO DO ANALISTA ────────────────────────────────────────────────────
    filtered = []
    rejected = 0
    for a in all_articles:
        result = analyst_filter(a)
        if result.get("analyst_pass", False):
            filtered.append(result)
        else:
            rejected += 1

    log.info(f"Filtro analista: {len(filtered)} passou | {rejected} rejeitado")

    # Score viral — 7 gatilhos × multiplicador de tier
    for a in filtered:
        result = score_article(a)
        a["score"]          = result["score"]
        a["viral_gatilhos"] = result["gatilhos"]
        a["viral_tier"]     = result["tier_mult"]
        a["viral_class"]    = result["classificacao"]

    filtered.sort(key=lambda x: x["score"], reverse=True)

    # Seleção por categoria — priorizando cripto BR
    cripto_br  = [a for a in filtered if a["cat"] in ("cripto","onchain","etf") and a.get("br")]
    cripto_gl  = [a for a in filtered if a["cat"] in ("cripto","onchain","etf") and not a.get("br")]
    macro_arts = [a for a in filtered if a["cat"] == "macro"]
    geo_arts   = [a for a in filtered if a["cat"] == "geo"]

    # 60% cripto BR, 40% cripto global
    n_br = max(1, (n_cripto * 6) // 10)
    n_gl = n_cripto - n_br
    cripto = (cripto_br[:n_br] + cripto_gl[:n_gl])[:n_cripto]
    macro  = macro_arts[:n_macro]
    geo    = geo_arts[:n_geo]

    selected = cripto + macro + geo
    selected.sort(key=lambda x: x["score"], reverse=True)

    enriched = []
    for i, a in enumerate(selected[:MAX_ART]):
        a["id"] = i + 1
        try:
            enriched.append(enrich_article(a))
        except Exception as e:
            log.warning(f"Enrich failed [{a.get('title','?')[:40]}]: {e}")
            a["editorial_format"] = "EDUCATIVO_CONTEXTO"
            enriched.append(a)

    stats = {
        "total": len(enriched),
        "cripto_br":  sum(1 for a in enriched if a.get("cat") in ("cripto","onchain","etf") and a.get("br")),
        "cripto_gl":  sum(1 for a in enriched if a.get("cat") in ("cripto","onchain","etf") and not a.get("br")),
        "macro":  sum(1 for a in enriched if a.get("cat") == "macro"),
        "geo":    sum(1 for a in enriched if a.get("cat") == "geo"),
        "stars3": sum(1 for a in enriched if a.get("analyst_stars") == 3),
        "stars2": sum(1 for a in enriched if a.get("analyst_stars") == 2),
        "stars1": sum(1 for a in enriched if a.get("analyst_stars") == 1),
    }
    log.info(f"Pipeline: {stats}")
    return enriched


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND REFRESH
# ─────────────────────────────────────────────────────────────────────────────
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
    log.info(f"Cripto Brasil Intel v8 | {len(FEEDS)} fontes | porta {PORT}")
    asyncio.create_task(auto_refresh())


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service":         "Cripto Brasil Intel API",
        "version":         "8.0.0",
        "sources":         len(FEEDS),
        "br_sources":      sum(1 for f in FEEDS if f["br"]),
        "cripto_sources":  sum(1 for f in FEEDS if f["cat"] == "cripto"),
        "onchain_sources": sum(1 for f in FEEDS if f["cat"] == "onchain"),
        "formats":         len(FORMATS),
        "freshness_hours": FRESHNESS_H,
        "cache_ok":        _cache_valid(),
        "articles":        len(_cache.get("news", [])),
        "last_refresh":    str(_cache.get("ts", "aguardando...")),
        "docs":            "/docs",
    }

@app.get("/api/health")
async def health():
    return {
        "status":   "ok",
        "ts":       datetime.now(timezone.utc).isoformat(),
        "cache":    _cache_valid(),
        "articles": len(_cache.get("news", [])),
    }

@app.get("/api/news")
async def news(
    limit:   int  = Query(24, ge=1, le=60),
    cripto:  int  = Query(14, ge=0, le=30),
    macro:   int  = Query(8,  ge=0, le=20),
    geo:     int  = Query(6,  ge=0, le=20),
    refresh: bool = Query(False),
    stars:   int  = Query(0,  ge=0, le=3, description="Mínimo de estrelas do analista (0=todos)"),
):
    """Retorna notícias filtradas pelo analista, enriquecidas e ordenadas por score."""
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

    articles = _cache.get("news", [])
    if stars > 0:
        articles = [a for a in articles if a.get("analyst_stars", 0) >= stars]

    return {
        "articles":   articles[:limit],
        "total":      len(articles),
        "cached_at":  str(_cache.get("ts", "")),
        "sources":    len(FEEDS),
        "filter_72h": True,
        "distribution": {
            "3_stars": sum(1 for a in articles if a.get("analyst_stars") == 3),
            "2_stars": sum(1 for a in articles if a.get("analyst_stars") == 2),
            "1_star":  sum(1 for a in articles if a.get("analyst_stars") == 1),
        }
    }

@app.get("/api/sources")
async def sources_status():
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
        } for k, v in FORMATS.items()
    }}


# ─────────────────────────────────────────────────────────────────────────────
# QUEUE
# ─────────────────────────────────────────────────────────────────────────────
class QueueAction(BaseModel):
    hash: str

def _load_queue() -> list:
    if QUEUE_FILE.exists():
        try:    return json.loads(QUEUE_FILE.read_text())
        except: return []
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
            "stars":       a.get("analyst_stars", 0),
            "sentiment":   a.get("analyst_sentiment", "neutro"),
            "note":        a.get("analyst_note", ""),
            "fmt":         a.get("editorial_format", "EDUCATIVO_CONTEXTO"),
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


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cripto_br_count = sum(1 for f in FEEDS if f.get("br") and f["cat"] == "cripto")
    onchain_count   = sum(1 for f in FEEDS if f["cat"] == "onchain")
    etf_count       = sum(1 for f in FEEDS if f["cat"] == "etf")
    print(f"\n Cripto Brasil Intel v8")
    print(f"   {len(FEEDS)} fontes RSS")
    print(f"   {cripto_br_count} cripto PT-BR | {onchain_count} on-chain | {etf_count} ETF/institucional")
    print(f"   Filtro 72h · Analista v1 · Viral score v4")
    print(f"   http://localhost:{PORT}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT,
                reload=(ENV == "development"), log_level="info")
