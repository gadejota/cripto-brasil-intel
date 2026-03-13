"""
CRIPTO BRASIL INTEL — Editorial Engine v3
==========================================
Reescrito do zero. Zero boilerplate. Conteúdo real.

DNA do canal: direto, educativo, BR, sem mimimi
Tom: Marcus Aurelius encontrou o Itaú Unibanco e foi pro cripto

Formats:
  PREVISAO_ACERTADA    → especialista com track record diz X
  CORRENTE_IMPACTO     → evento → cadeia macro → seu Bitcoin
  ANGULO_BRASIL        → notícia global pelo ângulo do investidor BR
  CONTRAINTUITIVO      → take que vai contra o senso comum
  ALERTA_MERCADO       → urgente, financeiro, ação imediata
  EDUCATIVO_CONTEXTO   → ensina conceito usando o evento atual
  COMPARACAO_HISTORICA → padrão histórico + o que aconteceu + e agora?
"""

import re, html
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# LIMPEZA DE TEXTO
# ─────────────────────────────────────────────────────────────────────────────

def clean(text: str, max_len: int = 0) -> str:
    """Limpa HTML entities, tags e resíduos de RSS."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    # WordPress "O post X apareceu primeiro em Y"
    text = re.sub(r"\s*O post .+?apareceu primeiro em .+?\.?\s*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    # "Fonte: X" solto no fim
    text = re.sub(r"\s*Fonte:\s*[\w\s\.]+$", "", text)
    # "Siga o X no..." (BeInCrypto, etc)
    text = re.sub(r"^Siga o .+? no\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if max_len and len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0] + "…"
    return text


def extract_numbers(text: str) -> list:
    """Extrai valores numéricos relevantes do texto."""
    patterns = [
        r"(?:US?\$|R\$)\s*[\d\.,]+[KkMBT]?",     # US$ 75K, R$ 1,2B
        r"[\d\.,]+\s*%",                             # 11,5%, 47%
        r"[\d\.,]+\s*(?:mil|bilh[õo]es?|trilh)",    # 1,5 bilhões
        r"(?:\$|€|£)\s*[\d\.,]+[KkMBT]?",          # $75k
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, re.IGNORECASE))
    return [x.strip() for x in found[:4]]


def extract_entities(title: str) -> dict:
    """Extrai entidades relevantes do título para preencher hooks."""
    tl = title.lower()
    nums = extract_numbers(title)

    names = [n for n in [
        "Saylor", "Michael Saylor", "MicroStrategy", "Strategy", "BlackRock",
        "Fidelity", "Trump", "Powell", "Jerome Powell", "Lula", "Haddad",
        "Bacen", "Banco Central", "CVM", "Binance", "Coinbase", "Kraken",
        "Tether", "USDT", "Circle", "Ripple", "SEC", "Fed", "FOMC",
        "Nvidia", "Tesla", "Grayscale", "ARK", "Cathie Wood", "Hashdex",
        "Mercado Bitcoin", "Foxbit", "NovaDax",
    ] if n.lower() in tl]

    assets = [a for a in [
        "Bitcoin", "BTC", "Ethereum", "ETH", "XRP", "Solana", "SOL",
        "DOGE", "BNB", "ADA", "LINK", "MATIC", "AVAX", "OP", "ARB",
    ] if a.lower() in tl]

    places = [p for p in [
        "Brasil", "EUA", "China", "Japão", "Europa", "Irã", "Rússia",
        "Israel", "Oriente Médio", "Ásia", "América Latina",
    ] if p.lower() in tl]

    return {
        "nums":   nums,
        "num1":   nums[0] if nums else "",
        "names":  names,
        "name1":  names[0] if names else "",
        "assets": assets,
        "asset1": assets[0] if assets else "Bitcoin",
        "places": places,
        "place1": places[0] if places else "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMATOS EDITORIAIS
# ─────────────────────────────────────────────────────────────────────────────

FORMATS = {
    "PREVISAO_ACERTADA": {
        "desc":        "Especialista com track record diz algo sobre o mercado",
        "viral_bonus": 18,
        "trigger_kw":  [
            "predicted","forecast","warned","analyst says","expert says","says bitcoin",
            "previu","prevê","analista diz","especialista alerta","acertou","previsão",
            "told us","was right","target","price target","meta de preço",
        ],
        "best_for": ["geo","macro","bull"],
    },
    "CORRENTE_IMPACTO": {
        "desc":        "Evento global → cadeia macro → impacto no Bitcoin brasileiro",
        "viral_bonus": 14,
        "trigger_kw":  [
            "war","guerra","sanction","tariff","oil","fed","rate hike","rate cut",
            "petróleo","tarifa","juros","inflação","dólar sobe","crise",
            "iran","russia","china","conflict","conflito","strait","estreito",
        ],
        "best_for": ["geo","macro"],
    },
    "ANGULO_BRASIL": {
        "desc":        "Notícia vista pelo ângulo exclusivo do investidor brasileiro",
        "viral_bonus": 12,
        "trigger_kw":  [
            "brasil","brasileiro","real","selic","bacen","iof","receita federal",
            "governo","regulação","regulacao","mercado bitcoin","foxbit","b3",
            "ibovespa","câmbio","cambio","imposto","cpf","renda fixa","tesouro direto",
        ],
        "best_for": ["br","macro","geo"],
    },
    "CONTRAINTUITIVO": {
        "desc":        "Take que inverte o senso comum — provoca e gera debate",
        "viral_bonus": 16,
        "trigger_kw":  [
            "contrary","actually","wrong","myth","surprising","counter","opposite",
            "contrário","na verdade","errado","mito","surpreendente","ao contrário",
            "stop","para de","not what","não é o que","vendendo enquanto","selling while",
        ],
        "best_for": ["edu","bull","bear"],
    },
    "ALERTA_MERCADO": {
        "desc":        "Evento urgente que exige atenção imediata do portfólio",
        "viral_bonus": 15,
        "trigger_kw":  [
            "breaking","urgent","alert","crash","spike","emergency","record","all-time",
            "urgente","alerta","queda","disparou","emergência","recorde","rompe",
            "despenca","ath","historic","histórico","desaba","explode","derrete",
        ],
        "best_for": ["bear","bull","macro"],
    },
    "EDUCATIVO_CONTEXTO": {
        "desc":        "Usa evento atual para ensinar conceito — evergreen + relevante",
        "viral_bonus": 8,
        "trigger_kw":  [
            "what is","why","how","explained","understand","guide","tutorial",
            "o que é","por que","como","entenda","explica","guia","aprenda",
            "iniciante","para iniciantes","saiba como","descubra",
        ],
        "best_for": ["edu","br"],
    },
    "COMPARACAO_HISTORICA": {
        "desc":        "Evento atual espelha precedente histórico — o que aconteceu + e agora?",
        "viral_bonus": 13,
        "trigger_kw":  [
            "again","reminds","similar","repeat","history","like 2020","like 2022",
            "novamente","parecido","repete","história","como em","igual a",
            "2008","2020","2022","covid","crise","guerra","war",
        ],
        "best_for": ["macro","geo","edu"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HOOKS — preenchidos com conteúdo real do artigo
# ─────────────────────────────────────────────────────────────────────────────

def pick_hook(cls: str, article: dict) -> str:
    title  = clean(article.get("title", ""))
    exc    = clean(article.get("excerpt", article.get("desc", "")), 200)
    ent    = extract_entities(title)
    fmt    = article.get("_fmt_detected", "EDUCATIVO_CONTEXTO")

    asset  = ent["asset1"]
    name   = ent["name1"]
    place  = ent["place1"]
    num    = ent["num1"]
    short  = title[:60] + ("…" if len(title) > 60 else "")

    # Hooks específicos por formato e contexto
    if fmt == "PREVISAO_ACERTADA" and name:
        return f"{name} acertou antes quando ninguém acreditava. Agora está dizendo uma coisa nova sobre o {asset}."
    if fmt == "PREVISAO_ACERTADA":
        return f"Esse analista teve um dos melhores track records de {asset} dos últimos 2 anos. Leia o que ele está dizendo agora."

    if fmt == "ALERTA_MERCADO" and num:
        return f"Para tudo. {num} — esse número muda o raciocínio sobre o {asset} hoje."
    if fmt == "ALERTA_MERCADO":
        return f"Antes de você abrir qualquer exchange hoje, precisa saber disso."

    if fmt == "CORRENTE_IMPACTO" and place:
        return f"O que está acontecendo {('em ' + place) if place else 'agora'} vai mudar o preço do {asset} nas próximas semanas. Deixa eu te mostrar a corrente."
    if fmt == "CORRENTE_IMPACTO":
        return f"Existe uma corrente de causa e efeito que começa nessa notícia e termina no seu portfólio cripto."

    if fmt == "ANGULO_BRASIL" and num:
        return f"{num} — o número que o investidor brasileiro precisa entender antes de qualquer decisão agora."
    if fmt == "ANGULO_BRASIL":
        return f"Esse é o ângulo que ninguém está mostrando sobre isso pra quem investe em cripto no Brasil."

    if fmt == "CONTRAINTUITIVO":
        return f"A narrativa dominante sobre isso está errada. E vou te mostrar o porquê com dados."

    if fmt == "COMPARACAO_HISTORICA":
        return f"Isso já aconteceu antes. Nas duas últimas vezes, quem entendeu o padrão saiu muito na frente."

    if cls == "bull" and num:
        return f"{num} — o número que confirmou o que eu estava esperando sobre o {asset}."
    if cls == "bear":
        return f"Para tudo. Lê isso antes de tomar qualquer decisão agora."
    if cls == "br":
        return f"O ângulo brasileiro que a maioria está ignorando: {short}"
    if cls == "edu":
        return f"A maioria dos investidores BR ainda não entendeu isso — e vai pagar caro por ignorar."

    # Fallback genérico com contexto real
    return f"Isso que aconteceu com o {asset} hoje importa mais do que o preço em si. Deixa eu explicar."


# ─────────────────────────────────────────────────────────────────────────────
# CTA — contextual
# ─────────────────────────────────────────────────────────────────────────────

def pick_cta(cls: str, fmt: str) -> str:
    if fmt == "ALERTA_MERCADO":
        return "Não mexe no portfólio antes de ler isso até o fim. Salva pra reler depois."
    if fmt == "CONTRAINTUITIVO":
        return "Concorda ou discorda? Me conta nos comentários. Esse debate vale muito."
    if fmt == "COMPARACAO_HISTORICA":
        return "Salva esse post. Vai querer reler quando o mercado virar."
    if cls == "geo":
        return "Manda pra alguém que precisa entender o que está acontecendo antes de tomar qualquer decisão."
    if cls == "edu":
        return "Salva isso. 90% das pessoas no mercado não sabem esse contexto todo."
    if cls == "br":
        return "Manda pra um brasileiro que tem cripto e ainda não viu isso."
    return "Manda pra alguém que precisa ver isso antes de tomar qualquer decisão."


# ─────────────────────────────────────────────────────────────────────────────
# REEL SCRIPT — humano, direto, usa conteúdo real
# ─────────────────────────────────────────────────────────────────────────────

def reel_script(article: dict, fmt: str) -> str:
    """
    Script de reel no DNA @criptobrasilofc:
    - Tom coloquial BR, primeira pessoa, direto
    - Hook forte na primeira frase (não "olá", não "hoje vou falar")
    - Conteúdo real do artigo, não frases genéricas
    - ~160-220 palavras (55-70s falado a 160 wpm)
    - Final: insight ou pergunta — nunca CTA genérico
    """
    title  = clean(article.get("title", ""))
    exc    = clean(article.get("excerpt", article.get("desc", "")), 450)
    cont   = clean(article.get("content", ""), 600)
    src    = article.get("source_name", article.get("src", ""))
    cls    = article.get("_cls", article.get("cls", "edu"))
    ent    = extract_entities(title)
    num    = ent["num1"]
    nums   = ent["nums"]
    asset  = ent["asset1"]
    name   = ent["name1"]
    place  = ent["place1"]

    body = exc if exc else cont[:400]

    if fmt == "ALERTA_MERCADO":
        num_line = f"\n\nO número que importa aqui: {num}. Isso não apareceu por acaso." if num else ""
        return f"""Para tudo. Isso é urgente.

{title}

{body}

Fonte: {src}.{num_line}

Esse tipo de movimento não acontece no vácuo. Quando você vê isso, o mercado está processando uma informação que a maioria ainda não entendeu — e normalmente leva 48 a 72 horas pra precificar de verdade.

Não é hora de entrar em pânico. É hora de atenção cirúrgica. Os erros mais caros que eu já vi nesse mercado não foram de análise — foram de reação emocional em momentos exatamente como esse."""

    elif fmt == "CORRENTE_IMPACTO":
        place_line = f"começa {('em ' + place) if place else 'lá fora'}" 
        return f"""Vou te mostrar uma corrente que {place_line} e termina no preço do {asset} aqui no Brasil.

{body}

Fonte: {src}.

A sequência completa: esse evento cria pressão no petróleo e no dólar. Dólar forte significa inflação importada. Inflação importada significa Fed hesita em cortar juros. Mercados de risco sofrem. Bitcoin vai junto em dólar. E ainda fica mais caro em reais porque o câmbio abriu contra você.

{'Números reais nessa equação: ' + ', '.join(nums[:2]) + '.' if nums else ''}

Duas forças contra o {asset} ao mesmo tempo. Quem entende a corrente inteira não reage ao preço. Antecipa o contexto."""

    elif fmt == "ANGULO_BRASIL":
        num_line = f"\n\nO detalhe que muda tudo: {num}." if num else "\n\nO detalhe que a maioria está ignorando é o impacto direto no contexto brasileiro."
        return f"""Tem um ângulo nessa notícia que quase ninguém está mostrando pro investidor brasileiro.

{title}

{body}

Fonte: {src}.{num_line}

Você investe em reais. Compra cripto em dólar. Paga IOF na conversão. E ainda compete com Selic de dois dígitos. Essa equação é única no mundo — e significa que o impacto de qualquer notícia global chega aqui de forma diferente do que você lê em inglês.

Quem ignora esse contexto está tomando decisão com metade das informações."""

    elif fmt == "PREVISAO_ACERTADA":
        name_line = f"{name} " if name else "Esse analista "
        return f"""{name_line}tinha razão antes quando o mercado não queria ouvir.

{body}

Fonte: {src}.

{'O número específico que ele está apontando: ' + num + '.' if num else ''}

A questão não é se você concorda ou discorda. A questão é: você tem uma tese própria baseada em dados, ou está esperando alguém te dizer o que fazer?

Analistas com bom histórico enxergam conexões antes do mercado consolidar o consenso. É exatamente aí que estão os maiores ganhos — e os maiores riscos pra quem age tarde demais."""

    elif fmt == "CONTRAINTUITIVO":
        return f"""A narrativa dominante sobre isso está errada. E vou te mostrar o porquê.

{body}

Fonte: {src}.

{'O dado que inverte essa lógica: ' + num + '.' if num else 'Os dados on-chain contam uma história diferente do que a manchete sugere.'}

O mercado de curto prazo reflete consenso — e consenso é sempre atrasado. Quando todo mundo está dizendo a mesma coisa, o {asset} já se moveu. Os melhores trades da história do cripto foram feitos contra o consenso do momento.

Discorda? Me fala nos comentários. Esse é o tipo de debate que faz alguém repensar o próprio portfólio."""

    elif fmt == "COMPARACAO_HISTORICA":
        return f"""Isso já aconteceu antes. E quem entendeu o padrão histórico saiu muito na frente.

{body}

Fonte: {src}.

Em março de 2020, o {asset} caiu 50% em 48 horas. Quem comprou no fundo multiplicou por 12 em 13 meses. Em novembro de 2022, colapso FTX + inflação + guerra. {asset} foi a $15k. Quem comprou entre $15k e $20k tem mais de 300% hoje.

{'A referência numérica atual: ' + num + '.' if num else 'A pergunta que separa quem perde de quem ganha: os fundamentos mudaram, ou só o sentimento mudou?'}

A história não se repete exatamente. Mas rima alto."""

    else:  # EDUCATIVO_CONTEXTO
        return f"""Tem um contexto por trás disso que a maioria está ignorando.

{title}

{body}

Fonte: {src}.

{'O dado que muda a leitura: ' + num + '.' if num else ''}

Entender o contexto não é pra você agir impulsivamente. É pra você não agir por medo. A diferença entre quem perde e quem ganha nesse mercado, na maioria das vezes, não é timing — é clareza sobre o que está acontecendo enquanto os outros reagem ao preço.

Quem faz a pergunta certa no momento certo está sempre à frente."""


# ─────────────────────────────────────────────────────────────────────────────
# CAROUSEL SLIDES — conteúdo real, um insight por slide
# ─────────────────────────────────────────────────────────────────────────────

def carousel_slides(article: dict, fmt: str) -> list:
    """
    Carrossel no DNA @criptobrasilofc:
    - Capa: número forte ou claim direto
    - Corpo: um insight real por slide, curto, negrito nas frases-chave
    - Lista: mitos vs realidade (formato educativo)
    - Final: conclusão forte sem CTA explícito
    - 5-7 slides — qualidade > quantidade
    - Zero boilerplate, conteúdo real do artigo
    """
    title  = clean(article.get("title", ""))
    exc    = clean(article.get("excerpt", article.get("desc", "")), 500)
    cont   = clean(article.get("content", ""), 700)
    src    = article.get("source_name", article.get("src", ""))
    cls    = article.get("_cls", article.get("cls", "edu"))
    ent    = extract_entities(title)
    num    = ent["num1"]
    nums   = ent["nums"]
    asset  = ent["asset1"]
    place  = ent["place1"]
    name   = ent["name1"]
    body   = exc if len(exc) > 80 else (cont[:450] if cont else exc)

    def S(role, t, img="", arrow=True):
        t = t + ("\n\n👇👇" if arrow and role not in ("capa","final") else "")
        return {"role": role, "t": t.strip(), "img": img, "arrow": (arrow and role not in ("capa","final"))}

    def capa(t, img=""):  return S("capa",  t, img, False)
    def corpo(t, img=""): return S("corpo", t, img, True)
    def lista(t):         return S("lista", t, "",  True)
    def final(t):         return S("final", t, "",  False)

    # ── ALERTA_MERCADO ────────────────────────────────────────────────────────
    if fmt == "ALERTA_MERCADO":
        num_capa = f"**{num}**\n\n" if num else ""
        return [
            capa(
                f"{num_capa}**{title}**\n\nIsso exige atenção agora.",
                img="gráfico do evento ou print da notícia"
            ),
            corpo(
                f"**O que aconteceu:**\n\n{body}\n\nFonte: {src}.",
                img="print ou gráfico"
            ),
            corpo(
                f"**Por que isso importa agora:**\n\n"
                f"Eventos desse tipo se movem em dois tempos:\n\n"
                f"Primeiro vem a reação emocional do varejo — impulsiva, exagerada, geralmente errada.\n\n"
                f"Depois vem a correção pelos dados reais — e é onde surgem as oportunidades.",
            ),
            corpo(
                f"**O que monitorar nas próximas 48h:**\n\n"
                f"• Volume acima da média histórica\n"
                f"• Saída de stablecoins de exchanges (sinal de compra ou saída de capital?)\n"
                f"• Open interest em futuros (alavancagem acumulada)\n\n"
                f"Esses três dados dizem mais do que qualquer manchete.",
            ),
            final(
                f"Não é hora de pânico. É hora de atenção.\n\n"
                f"Mercado em stress é onde se formam as melhores assimetrias — e os maiores erros.\n\n"
                f"A diferença entre os dois é contexto.\n\n@criptobrasilofc"
            ),
        ]

    # ── CORRENTE_IMPACTO ──────────────────────────────────────────────────────
    elif fmt == "CORRENTE_IMPACTO":
        place_str = f"em {place}" if place else "lá fora"
        return [
            capa(
                f"**{title}**\n\nParece distante? Deixa eu te mostrar como isso chega direto no seu {asset}.",
                img="mapa ou gráfico macro"
            ),
            corpo(
                f"**O evento:**\n\n{body}\n\nFonte: {src}.",
                img="imagem da notícia"
            ),
            corpo(
                f"**Elo 1 — Energia e dólar:**\n\n"
                f"Conflito ou incerteza {place_str} cria pressão em rotas de commodities.\n\n"
                f"Petróleo sobe → inflação sobe → Fed hesita em cortar juros → custo de capital sobe globalmente.\n\n"
                f"{'Referência: ' + nums[0] if nums else 'Esse mecanismo levou semanas pra se materializar em 2022 — mas quando veio, foi 77% de queda no BTC.'}",
                img="gráfico petróleo/juros"
            ),
            corpo(
                f"**Elo 2 — Mercados de risco:**\n\n"
                f"**{asset} ainda é classificado como ativo de risco** pelos algoritmos institucionais.\n\n"
                f"Quando o Nasdaq corrige por stress macro, o BTC vai junto — independente dos fundamentos on-chain.\n\n"
                f"A correlação é temporária. Mas no curto prazo, ela dói.",
                img="gráfico BTC vs Nasdaq"
            ),
            corpo(
                f"**Elo 3 — O real:**\n\n"
                f"Turbulência global = dólar mais forte = real mais fraco.\n\n"
                f"**Quem compra {asset} em reais paga duas vezes:** quando o ativo sobe em dólar, e quando o dólar sobe em reais.\n\n"
                f"Esse duplo efeito é ignorado por quem só acompanha o preço em dólar.",
                img="gráfico USD/BRL"
            ),
            final(
                f"Entender a corrente inteira é o que separa quem reage de quem antecipa.\n\n"
                f"O evento aconteceu {place_str}. O impacto chega aqui.\n\n"
                f"A questão é se você vai entender isso antes ou depois do preço se mover.\n\n@criptobrasilofc"
            ),
        ]

    # ── ANGULO_BRASIL ─────────────────────────────────────────────────────────
    elif fmt == "ANGULO_BRASIL":
        num_hook = f"**{num}** — " if num else ""
        return [
            capa(
                f"{num_hook}o ângulo que quase ninguém está mostrando.\n\n**{title}**",
                img="imagem BR ou flag verde amarelo cripto"
            ),
            corpo(
                f"**O que aconteceu:**\n\n{body}\n\nFonte: {src}.",
                img="print da notícia"
            ),
            corpo(
                f"**Por que isso afeta o brasileiro de forma diferente:**\n\n"
                f"Você investe em reais. Compra em dólar. Paga IOF. E compete com Selic de dois dígitos.\n\n"
                f"Essa equação é única no mundo. Qualquer análise em inglês ignora ela completamente.",
            ),
            corpo(
                f"**O impacto prático:**\n\n"
                f"{'Quando o dólar se move para ' + num + ', o custo de entrada em ' + asset + ' muda junto — mesmo se o preço em dólar ficar parado.' if num else 'Quando o câmbio se move 10%, o custo de entrada em cripto muda junto — mesmo se o preço em dólar ficar parado.'}\n\n"
                f"E quando a Selic está alta, a renda fixa compete diretamente com cripto pelo mesmo capital.\n\n"
                f"Dois fatores que analistas internacionais não consideram.",
                img="gráfico Selic vs BTC em R$"
            ),
            final(
                f"O investidor brasileiro que ignora o contexto cambial e de juros está tomando decisões com metade das informações.\n\n"
                f"Isso não é pessimismo. É a realidade de viver num país de moeda fraca investindo em ativo dolarizado.\n\n@criptobrasilofc"
            ),
        ]

    # ── PREVISAO_ACERTADA ─────────────────────────────────────────────────────
    elif fmt == "PREVISAO_ACERTADA":
        name_str = name if name else "Esse analista"
        return [
            capa(
                f"**{name_str}** acertou quando ninguém acreditava.\n\nAgora está dizendo algo novo sobre o {asset}.\n\n**{title}**",
                img="gráfico ou print da declaração"
            ),
            corpo(
                f"**O contexto completo:**\n\n{body}\n\nFonte: {src}.",
                img="print da análise"
            ),
            corpo(
                f"**Por que prestar atenção:**\n\n"
                f"Analistas com bom histórico não são sortudos — eles enxergam conexões que o mercado ainda não precificou.\n\n"
                f"{'O número específico que aponta: ' + num + '.' if num else 'A metodologia importa mais do que o nome. Vale entender o raciocínio por trás, não só a conclusão.'}",
            ),
            corpo(
                f"**A implicação pro seu {asset}:**\n\n"
                f"Previsões de analistas com track record movem sentimento antes de moverem preço.\n\n"
                f"**Sentimento é o que determina o próximo ciclo de compra ou venda do varejo.**\n\n"
                f"Entender isso é diferente de seguir cegamente.",
            ),
            final(
                f"Você não precisa concordar com tudo que especialistas dizem.\n\n"
                f"Mas precisa saber o que eles estão dizendo — especialmente quando o histórico é forte.\n\n"
                f"Ignorar completamente é tão perigoso quanto seguir sem pensar.\n\n@criptobrasilofc"
            ),
        ]

    # ── CONTRAINTUITIVO ───────────────────────────────────────────────────────
    elif fmt == "CONTRAINTUITIVO":
        return [
            capa(
                f"A narrativa dominante sobre isso está errada. Vou provar.\n\n**{title}**",
                img="gráfico que mostra o contraste"
            ),
            corpo(
                f"**O que todo mundo está dizendo:**\n\n{body}\n\nFonte: {src}.",
            ),
            lista(
                f'1- **"O mercado já sabe disso"**\n\n'
                f"Sabe o consenso. Não sabe o que está sendo ignorado.\n\n"
                f"{'O dado ignorado: ' + num if num else 'Os dados on-chain raramente batem com a narrativa dominante no curto prazo. É uma das maiores arestas que ainda existem nesse mercado.'}"
            ),
            lista(
                f'2- **"Isso não afeta o {asset}"**\n\n'
                f"Afeta. Mas de forma indireta e com defasagem de semanas.\n\n"
                f"É exatamente aí que a maioria erra: espera o impacto óbvio enquanto o impacto real já aconteceu silenciosamente."
            ),
            lista(
                f'3- **"Agora não é hora de agir"**\n\n'
                f"Não agir é uma ação. E às vezes é a mais cara que existe.\n\n"
                f"A questão não é agir ou não agir. É saber *por que* você está fazendo cada escolha."
            ),
            final(
                f"Mercado errado por muito tempo ainda é mercado errado.\n\n"
                f"Mas nesses momentos de dissonância entre narrativa e dados é que se formam as melhores assimetrias.\n\n@criptobrasilofc"
            ),
        ]

    # ── COMPARACAO_HISTORICA ──────────────────────────────────────────────────
    elif fmt == "COMPARACAO_HISTORICA":
        return [
            capa(
                f"Isso já aconteceu antes. O {asset} saiu muito diferente depois.\n\n**{title}**",
                img="gráfico histórico longo prazo"
            ),
            corpo(
                f"**O evento de hoje:**\n\n{body}\n\nFonte: {src}.",
                img="imagem da notícia"
            ),
            corpo(
                f"**O paralelo histórico:**\n\n"
                f"**Março 2020:** {asset} caiu 50% em 48h. Subiu 1.200% nos 13 meses seguintes.\n\n"
                f"**Novembro 2022:** Colapso FTX + inflação + guerra. {asset} foi a $15k. Hoje, quem comprou ali tem 300%+.\n\n"
                f"Nos dois casos, os fundamentos não mudaram. Só o sentimento mudou.",
                img="gráfico BTC histórico"
            ),
            corpo(
                f"**Por que o padrão se repete:**\n\n"
                f"Em crises de liquidez, investidores vendem o que conseguem vender — não o que deveriam.\n\n"
                f"**{asset} é líquido 24h.** É um dos primeiros a sair em stress. E um dos primeiros a voltar quando o contexto normaliza.",
                img="gráfico liquidez cripto vs outros ativos"
            ),
            final(
                f"A história não se repete exatamente. Mas rima.\n\n"
                f"{'A referência atual: ' + num + '.' if num else 'A pergunta que importa: os fundamentos mudaram, ou só o sentimento?'}\n\n"
                f"Essa distinção vale mais do que qualquer indicador técnico.\n\n@criptobrasilofc"
            ),
        ]

    # ── EDUCATIVO_CONTEXTO (default) ──────────────────────────────────────────
    else:
        return [
            capa(
                f"2 minutos lendo isso vai mudar como você vê esse assunto.\n\n**{title}**",
                img="infográfico ou imagem educativa"
            ),
            corpo(
                f"**O contexto:**\n\n{body}\n\nFonte: {src}.",
            ),
            lista(
                f'1- **"Isso não afeta quem está no longo prazo"**\n\n'
                f"Afeta sim — no curto prazo. E curto prazo importa porque é quando a maioria toma as piores decisões.\n\n"
                f"Saber o que está acontecendo não é pra agir impulsivamente. É pra não agir por medo."
            ),
            lista(
                f'2- **"O mercado já precificou isso"**\n\n'
                f"{'O dado que ainda não foi precificado: ' + num if num else 'O mercado precifica consenso. E consenso sempre atrasa.'}\n\n"
                f"Preços refletem o que a maioria acredita agora — não necessariamente o que vai acontecer."
            ),
            lista(
                f'3- **"{asset} vai subir ou cair com isso?"**\n\n'
                f"Essa é a pergunta errada.\n\n"
                f"A pergunta certa: os fundamentos de longo prazo mudaram, ou só o sentimento de curto prazo está distorcido?\n\n"
                f"Essa distinção separa investidor de especulador."
            ),
            final(
                f"Você não precisa ter todas as respostas.\n\n"
                f"Mas precisa fazer as perguntas certas.\n\n"
                f"Quem faz a pergunta certa no momento certo está sempre à frente.\n\n@criptobrasilofc"
            ),
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MÚSICA E DALLE
# ─────────────────────────────────────────────────────────────────────────────

MUSIC = {
    ("PREVISAO_ACERTADA", "geo"):      "Hans Zimmer – Time (instrumental piano)",
    ("PREVISAO_ACERTADA", "macro"):    "Thriller financeiro — piano sombrio minimal",
    ("CORRENTE_IMPACTO",  "geo"):      "Breaking news urgente — percussão crescendo",
    ("CORRENTE_IMPACTO",  "macro"):    "Wall Street tensão — cordas graves",
    ("ALERTA_MERCADO",    "bear"):     "Inception bass drop — alarme dramático",
    ("ALERTA_MERCADO",    "bull"):     "Epic orchestral build — triunfo",
    ("ANGULO_BRASIL",     "br"):       "Informativo urgente BR — bateria rápida",
    ("EDUCATIVO_CONTEXTO","edu"):      "Lo-fi focus — beat analítico calmo",
    ("COMPARACAO_HISTORICA","macro"):  "Documentário score — gravidade histórica",
    ("CONTRAINTUITIVO",   "edu"):      "Plot twist reveal — suspense crescendo",
    "default":                          "Dark minimal eletrônico — tensão neutra",
}

DALLE_BASE = {
    "geo":   "Geopolitical crisis map dark editorial, yellow accent lines, global conflict zones, cinematic 9:16",
    "macro": "Bloomberg terminal dark mode, financial data crash, yellow #FFD600 charts, wall street noir 9:16",
    "bull":  "Bitcoin breaking all-time high neon green laser, dark cyber background, euphoric energy 9:16",
    "bear":  "Bitcoin red crash chart, dark terminal aesthetic, dramatic shadows, data journalism noir 9:16",
    "br":    "Brazil flag meets dark crypto terminal, R$ symbol glowing green, map Brazil editorial dark gold 9:16",
    "edu":   "Dark mode infographic clean, yellow accent #FFD600, data flow educational minimal 9:16",
}

TAGS = {
    "bull":  "#Bitcoin #Alta #CriptoBR #BullRun",
    "bear":  "#Bitcoin #Baixa #CriptoBR #Análise",
    "edu":   "#Bitcoin #Educação #CriptoBR #Cripto",
    "br":    "#CriptoBR #Bitcoin #Brasil #Regulação",
    "macro": "#Macro #FED #Bitcoin #Economia #Juros",
    "geo":   "#Geopolítica #Bitcoin #Macro #Guerra",
}


# ─────────────────────────────────────────────────────────────────────────────
# DETECT FORMAT
# ─────────────────────────────────────────────────────────────────────────────

def detect_format(article: dict) -> str:
    title  = clean(article.get("title", ""))
    exc    = clean(article.get("excerpt", article.get("desc", "")), 300)
    text   = (title + " " + exc).lower()
    cls    = article.get("_cls", article.get("cls", "edu"))

    scores = {fmt: 0 for fmt in FORMATS}

    for fmt_name, fmt in FORMATS.items():
        for kw in fmt["trigger_kw"]:
            if kw.lower() in text:
                scores[fmt_name] += 2
        if cls in fmt["best_for"]:
            scores[fmt_name] += 3

    # Regras contextuais de força
    if any(w in text for w in ["acertou","previu","predicted","forecast","price target","meta de preço","was right"]):
        scores["PREVISAO_ACERTADA"] += 12
    if any(w in text for w in ["war","guerra","iran","russia","missile","conflito","ataque","sanction","strait","estreito"]):
        scores["CORRENTE_IMPACTO"] += 8
        scores["ALERTA_MERCADO"]   += 3
    if any(w in text for w in ["brasil","brasileiro","selic","bacen","iof","real","câmbio","regulação","b3"]):
        scores["ANGULO_BRASIL"] += 10
    if any(w in text for w in ["2008","2020","2022","covid","história","novamente","repete","historical","como em 2"]):
        scores["COMPARACAO_HISTORICA"] += 8
    if any(w in text for w in ["breaking","urgente","recorde","crash","rompe","ath","all-time","despenca","histórico","record"]):
        scores["ALERTA_MERCADO"] += 8
    if any(w in text for w in ["errado","mito","contrário","na verdade","para de","wrong","actually","stop","not what"]):
        scores["CONTRAINTUITIVO"] += 10

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "EDUCATIVO_CONTEXTO"


# ─────────────────────────────────────────────────────────────────────────────
# ENRICH ARTICLE — entry point
# ─────────────────────────────────────────────────────────────────────────────

def enrich_article(article: dict) -> dict:
    # Garante aliases para compatibilidade
    article.setdefault("_cls",        article.get("cls", "edu"))
    article.setdefault("excerpt",     article.get("desc", article.get("content", ""))[:500])
    article.setdefault("source_name", article.get("src", ""))
    article.setdefault("link",        article.get("url", "#"))

    cls  = article["_cls"]
    fmt  = detect_format(article)
    article["_fmt_detected"] = fmt   # disponível para pick_hook

    title  = clean(article.get("title", ""))
    exc    = clean(article["excerpt"], 350)
    src    = article["source_name"]
    tags   = TAGS.get(cls, "#Bitcoin #Cripto #CriptoBR")
    hook   = pick_hook(cls, article)
    cta    = pick_cta(cls, fmt)
    slides = carousel_slides(article, fmt)
    script = reel_script(article, fmt)
    music  = MUSIC.get((fmt, cls), MUSIC["default"])
    dalle  = f"{title[:65]}, {DALLE_BASE.get(cls, DALLE_BASE['edu'])}"

    return {
        **article,
        "editorial_format":      fmt,
        "editorial_format_desc": FORMATS[fmt]["desc"],
        "hook":      hook,
        "tweet":     f"{hook}\n\n{title}\n\n🔗 {src}",
        "post_feed": f"**{hook}**\n\n{exc}\n\nFonte: {src}\n\n{cta}",
        "caption":   f"{title[:110]}{'…' if len(title)>110 else ''}\n\n{tags}\n\n@criptobrasilofc",
        "cta":       cta,
        "slides":    slides,
        "reel": {
            "dur":    "55-70s",
            "music":  music,
            "cap":    f"{hook}\n\n{tags}\n\n@criptobrasilofc",
            "script": script,
        },
        "dalle": dalle,
        "dalleVars": [
            f"{title[:55]}, dark editorial cinematic yellow accent --ar 9:16",
            f"{title[:55]}, data viz dark mode minimal --ar 1:1",
        ],
    }
