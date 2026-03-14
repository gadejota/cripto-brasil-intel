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
    """Gera script de reel baseado no formato editorial detectado."""
    title   = article["title"]
    excerpt = article.get("excerpt", title)
    source  = article.get("source_name", "")
    cls     = article.get("_cls", "edu")

    fmt_data = FORMATS.get(fmt, FORMATS["EDUCATIVO_CONTEXTO"])

    # Estrutura base por formato
    if fmt == "PREVISAO_ACERTADA":
        script = f"""Esse especialista fez previsões que o mundo ignorou — e acertou.

Agora ele está dizendo algo novo. E se ele acertar de novo?

{excerpt[:400]}

Fonte: {source}.

A questão não é se você concorda ou discorda. A questão é: você tem uma tese própria, ou está esperando que alguém te diga o que fazer?

Esse é o tipo de análise que separa quem entende o mercado de quem só reage a ele."""

    elif fmt == "CORRENTE_IMPACTO":
        script = f"""Vou te mostrar uma corrente de causa e efeito que começa num evento geopolítico e termina no seu portfólio.

{excerpt[:350]}

Fonte: {source}.

Como isso chega no Bitcoin:
Evento geopolítico → pressão no petróleo → inflação global → Fed hesita em cortar juros → mercados de risco sofrem → Bitcoin corrige junto.

Essa é a corrente. Entender ela é a diferença entre reagir e antecipar."""

    elif fmt == "ANGULO_BRASIL":
        script = f"""Enquanto todo mundo fala desse assunto no contexto global, poucos estão olhando pro que isso significa pro investidor brasileiro.

{excerpt[:350]}

Fonte: {source}.

No Brasil, isso se traduz em: pressão no dólar, Selic mais alta por mais tempo, cripto mais cara em reais — e uma janela de oportunidade que poucos vão aproveitar.

Esse é o ângulo que eu não vi ninguém falando hoje."""

    elif fmt == "CONTRAINTUITIVO":
        script = f"""Vou te dar um take que vai contra o que você está lendo por aí.

A narrativa dominante hoje é uma coisa. Mas os dados contam uma história diferente.

{excerpt[:350]}

Fonte: {source}.

Discorda? Ótimo. Me fala nos comentários. Esse é exatamente o tipo de debate que faz alguém pensar melhor sobre onde está colocando o dinheiro."""

    elif fmt == "ALERTA_MERCADO":
        script = f"""Para tudo. Lê isso antes de abrir qualquer exchange hoje.

{excerpt[:380]}

Fonte: {source}.

Não é hora de pânico. É hora de atenção. Esses são os números e os sinais que você precisa monitorar nas próximas 48 horas."""

    elif fmt == "COMPARACAO_HISTORICA":
        script = f"""Isso já aconteceu antes. E quem entendeu o padrão histórico saiu na frente.

{excerpt[:350]}

Fonte: {source}.

A história não se repete. Mas rima. E saber a letra é metade do caminho pra tomar uma decisão melhor hoje."""

    else:  # EDUCATIVO_CONTEXTO
        script = f"""Tem um contexto por trás dessa notícia que a maioria das pessoas está ignorando.

{excerpt[:380]}

Fonte: {source}.

Entendendo isso, você já sabe mais do que a maioria das pessoas que vai reagir emocionalmente a esse evento."""

    return script


def carousel_slides(article: dict, fmt: str) -> list:
    """
    Gera carrossel no padrão EXATO CriptoBrasilOFC observado no perfil:

    FORMATO VISUAL: Tweet-screenshot — card branco, foto + @CriptoBrasilOFC no header.
    TEXTO: 2-3 parágrafos curtos por slide. Negrito nas frases-chave (**texto**).
           👇👇 nos slides que continuam. Último slide termina no argumento mais forte,
           sem CTA explícito.
    TIPOS: narrativo (história avança beat a beat) ou lista (N- "Mito" → correção).
    """
    title   = article["title"]
    excerpt = article.get("excerpt", title)
    cls     = article.get("_cls", "edu")
    source  = article.get("source_name", "")

    # ── HELPERS ───────────────────────────────────────────────────────────────
    # Slide de capa: hook + contexto mínimo + imagem sugerida
    # Exatamente como slide 1 do Jiang: claim + quem é a pessoa + foto
    def capa(txt: str, img_hint: str = "") -> dict:
        return {"role": "capa", "t": txt, "img": img_hint, "arrow": False}

    # Slide narrativo: 2-3 parágrafos que avançam a história. Com 👇👇 se não é o último.
    def corpo(txt: str, continua: bool = True, img_hint: str = "") -> dict:
        t = txt + ("\n\n👇👇" if continua else "")
        return {"role": "corpo", "t": t, "img": img_hint, "arrow": continua}

    # Slide de lista: "N- 'Mito'" → 2 parágrafos de correção
    def item_lista(n: int, mito: str, correcao: str, continua: bool = True, img_hint: str = "") -> dict:
        t = f'{n}- **"{mito}"**\n\n{correcao}' + ("\n\n👇👇" if continua else "")
        return {"role": "lista", "t": t, "img": img_hint, "arrow": continua}

    # Slide final: termina no argumento mais forte. Sem CTA explícito — igual ao Jiang.
    def final(txt: str) -> dict:
        return {"role": "final", "t": txt, "img": "", "arrow": False}

    # ── PREVISÃO ACERTADA ────────────────────────────────────────────────────
    # Padrão exato do Jiang Xueqin (7.4k likes):
    # Slide 1: apresenta a pessoa + o claim chocante
    # Slides 2-N: prova credencial → previsões anteriores certas → a previsão nova
    # Último slide: o argumento mais forte da previsão, sem CTA
    if fmt == "PREVISAO_ACERTADA":
        return [
            capa(
                f"Esse homem fez grandes previsões, acertou, e agora está dizendo algo "
                f"que vai mudar sua visão sobre o mercado.\n\n"
                f"**{title}**\n\n"
                f"Fonte: {source}.",
                img_hint="foto do analista ou gráfico da previsão"
            ),
            corpo(
                f"Antes de você ignorar, deixa eu te contar o histórico dele.\n\n"
                f"{excerpt}\n\n"
                f"Analistas que acertam previsões improváveis não são sortudos — "
                f"eles enxergam conexões que a maioria ainda não está olhando.",
                img_hint="gráfico ou print da previsão anterior"
            ),
            corpo(
                f"E como já sabemos, mesmo contra o consenso do mercado, ele estava correto.\n\n"
                f"Isso não é um detalhe. É o que separa análise de achismo.\n\n"
                f"Quando alguém acerta o que ninguém apostava, o racional é prestar atenção "
                f"na próxima vez que ele abrir a boca.",
                img_hint="imagem do evento que ele previu"
            ),
            corpo(
                f"Agora ele está dizendo algo novo.\n\n"
                f"Algo que vai contra o que a maioria do mercado acredita hoje.\n\n"
                f"E quando ele foi questionado se ainda acreditava nisso, a resposta foi sim — "
                f"com argumentos específicos que muita gente ainda não está vendo.",
            ),
            corpo(
                f"**O impacto no Bitcoin e nos mercados cripto:**\n\n"
                f"Ativos de risco são os primeiros a sentir mudanças na narrativa geopolítica "
                f"e macroeconômica. Bitcoin inclusive.\n\n"
                f"Não porque os fundamentos mudaram — porque o sentimento dos grandes players muda. "
                f"E sentimento move preço no curto prazo.",
                img_hint="gráfico Bitcoin vs eventos macro"
            ),
            final(
                f"Você não precisa concordar com essa previsão.\n\n"
                f"Mas precisa ter uma resposta pra ela.\n\n"
                f"Quem entra em pânico quando o cenário muda é porque nunca tinha pensado "
                f"no que aconteceria se o consenso estivesse errado."
            ),
        ]

    # ── CORRENTE DE IMPACTO ──────────────────────────────────────────────────
    # Cada slide = um elo da corrente. Curto, direto, 2 parágrafos.
    elif fmt == "CORRENTE_IMPACTO":
        return [
            capa(
                f"**{title}**\n\n"
                f"Parece distante? Deixa eu te mostrar como isso chega direto no seu bolso.",
                img_hint="mapa geopolítico ou imagem do evento"
            ),
            corpo(
                f"O que aconteceu:\n\n"
                f"{excerpt}\n\n"
                f"Fonte: {source}.",
                img_hint="imagem da notícia"
            ),
            corpo(
                f"**Elo 1: energia.**\n\n"
                f"Conflitos em regiões produtoras de petróleo ou que controlam rotas de exportação "
                f"criam pressão imediata nos preços do barril.\n\n"
                f"Brent sobe. WTI sobe. Às vezes de forma discreta. Às vezes de 40% em 10 dias.",
                img_hint="gráfico petróleo"
            ),
            corpo(
                f"**Elo 2: inflação.**\n\n"
                f"Petróleo caro encarece transporte, produção, tudo que precisa de logística.\n\n"
                f"O Fed, que estava prestes a cortar juros, agora hesita. "
                f"Cortar juros com inflação subindo seria um erro histórico.",
                img_hint="gráfico inflação Fed"
            ),
            corpo(
                f"**Elo 3: mercados de risco.**\n\n"
                f"A alta dos mercados foi alimentada pela expectativa de cortes de juros. "
                f"Quando essa expectativa recua, o dinheiro institucional começa a sair.\n\n"
                f"Ações de tech caem. Nasdaq corrige. Bitcoin vai junto.",
                img_hint="gráfico Nasdaq vs BTC"
            ),
            corpo(
                f"**Elo 4: o Brasil.**\n\n"
                f"Turbulência externa = dólar mais forte = real mais fraco.\n\n"
                f"Pra quem compra Bitcoin em reais, o preço sobe duas vezes: porque o BTC subiu "
                f"em dólar, e porque o dólar subiu em reais.",
                img_hint="gráfico dólar/real"
            ),
            final(
                f"Entender a corrente inteira é o que separa quem reage de quem antecipa.\n\n"
                f"O evento aconteceu lá fora. O impacto chega aqui. "
                f"A questão é se você vai entender isso antes ou depois do preço se mover."
            ),
        ]

    # ── ALERTA DE MERCADO ────────────────────────────────────────────────────
    elif fmt == "ALERTA_MERCADO":
        return [
            capa(
                f"Para tudo.\n\n"
                f"**{title}**\n\n"
                f"Lê isso antes de abrir qualquer exchange hoje.",
                img_hint="gráfico queda ou breaking news"
            ),
            corpo(
                f"O que aconteceu:\n\n"
                f"{excerpt}\n\n"
                f"Fonte: {source}.",
                img_hint="imagem da notícia"
            ),
            corpo(
                f"Por que isso importa mais do que parece:\n\n"
                f"Não é o evento em si que move o preço — é a narrativa que se forma "
                f"em torno dele nas primeiras 48 horas.\n\n"
                f"Se os grandes players decidirem que isso justifica reduzir exposição, "
                f"o movimento pode ser rápido e desproporcional.",
            ),
            corpo(
                f"O que não fazer:\n\n"
                f"Não entre em pânico. As pessoas que mais perdem em crashes são as que vendem "
                f"no fundo depois de aguentar a queda inteira.\n\n"
                f"Mas também não ignore. Atenção consciente é diferente de pânico.",
            ),
            final(
                f"O que monitorar nas próximas 48h:\n\n"
                f"Volume de Bitcoin, dominância BTC vs altcoins, movimentação de stablecoins "
                f"em exchanges, e qualquer declaração nova do Fed ou Tesouro americano.\n\n"
                f"Você não precisa fazer nada agora. Mas precisa estar olhando."
            ),
        ]

    # ── CONTRAINTUITIVO ──────────────────────────────────────────────────────
    # Padrão "5 MENTIRAS": lista de mitos + correção. Numerado, curto, direto.
    elif fmt == "CONTRAINTUITIVO":
        return [
            capa(
                f"**Muito do que você acredita sobre esse assunto pode estar errado.**\n\n"
                f"{title}",
                img_hint="imagem relacionada ao tema"
            ),
            item_lista(
                1, "Isso não afeta o Bitcoin",
                f"Afeta. Bitcoin reage a qualquer evento que mude o apetite global por risco.\n\n"
                f"Não porque os fundamentos do ativo mudaram. Porque o sentimento dos players "
                f"institucionais muda — e eles movem o mercado.",
                img_hint="gráfico correlação Bitcoin"
            ),
            item_lista(
                2, "O mercado já precificou isso",
                f"O mercado precifica o que já é consenso. O que ainda não é consenso — "
                f"o que está acontecendo agora — ainda não está nos preços.\n\n"
                f"{excerpt[:200]}\n\nFonte: {source}.",
                img_hint="gráfico de mercado"
            ),
            item_lista(
                3, "Isso vai passar logo",
                f"Pode passar. Pode se aprofundar. A questão não é apostar num cenário.\n\n"
                f"É estar preparado pra qualquer um. Portfólio resiliente não precisa que o cenário "
                f"certo aconteça — ele sobrevive a todos.",
                img_hint="gráfico histórico de crises"
            ),
            final(
                f"A maioria das pessoas perde dinheiro não porque escolheu o ativo errado.\n\n"
                f"Mas porque tinha as premissas erradas sobre como o mundo funciona.\n\n"
                f"Questionar o que você acredita é a tarefa mais importante de qualquer investidor."
            ),
        ]

    # ── ÂNGULO BRASIL ────────────────────────────────────────────────────────
    elif fmt == "ANGULO_BRASIL":
        return [
            capa(
                f"Ninguém está te contando o que isso significa pra quem investe no Brasil.\n\n"
                f"**{title}**",
                img_hint="mapa ou imagem do evento"
            ),
            corpo(
                f"O que aconteceu:\n\n"
                f"{excerpt}\n\n"
                f"Fonte: {source}.",
                img_hint="imagem da notícia"
            ),
            corpo(
                f"**Como isso chega no dólar aqui:**\n\n"
                f"Eventos globais de incerteza fortalecem o dólar. Quando o dólar sobe, o real cai.\n\n"
                f"Qualquer ativo dolarizado — incluindo Bitcoin — fica mais caro em reais "
                f"automaticamente. Isso pode parecer bom se você já tem BTC. "
                f"É ruim se você quer comprar mais agora.",
                img_hint="gráfico dólar/real"
            ),
            corpo(
                f"**Como isso chega na Selic:**\n\n"
                f"O Banco Central monitora inflação importada via câmbio. "
                f"Dólar caro = importações mais caras = pressão inflacionária = "
                f"menos espaço pra cortar a Selic.\n\n"
                f"Selic alta por mais tempo significa custo de oportunidade maior "
                f"pra quem está em cripto vs renda fixa.",
                img_hint="gráfico Selic"
            ),
            final(
                f"O investidor brasileiro analisa esse evento em duas moedas: real e dólar.\n\n"
                f"Um Bitcoin que subiu 20% em dólar mas o dólar caiu 15% "
                f"significa só 5% de ganho em reais.\n\n"
                f"Esse cálculo simples é ignorado por 90% dos iniciantes em cripto no Brasil."
            ),
        ]

    # ── COMPARAÇÃO HISTÓRICA ─────────────────────────────────────────────────
    elif fmt == "COMPARACAO_HISTORICA":
        return [
            capa(
                f"Isso já aconteceu antes.\n\n"
                f"**{title}**\n\n"
                f"Quem entendeu o padrão histórico saiu na frente.",
                img_hint="imagem histórica ou gráfico longo prazo"
            ),
            corpo(
                f"O evento de hoje:\n\n"
                f"{excerpt}\n\n"
                f"Fonte: {source}.",
                img_hint="imagem da notícia"
            ),
            corpo(
                f"**2020:** Bitcoin caiu 50% em março. "
                f"Subiu 1200% até abril de 2021.\n\n"
                f"**2022:** guerra na Ucrânia + inflação + colapso FTX. Bitcoin caiu 77%. "
                f"Quem comprou entre $15k e $20k está com mais de 300% de retorno hoje.",
                img_hint="gráfico histórico Bitcoin"
            ),
            corpo(
                f"Por que esse padrão acontece?\n\n"
                f"Em momentos de stress, investidores vendem o que conseguem vender, "
                f"não o que deveriam.\n\n"
                f"Bitcoin é líquido 24h. Pode ser vendido em minutos. "
                f"Em crises de liquidez, ele é um dos primeiros a sair — "
                f"independente dos fundamentos.",
                img_hint="gráfico correlação crise"
            ),
            final(
                f"Isso não significa que você deve comprar agora de olhos fechados.\n\n"
                f"Significa que a decisão mais cara é vender com medo sem entender "
                f"se os fundamentos mudaram ou se é só o sentimento que está temporariamente distorcido.\n\n"
                f"A história não se repete. Mas rima."
            ),
        ]

    # ── EDUCATIVO CONTEXTO ────────────────────────────────────────────────────
    # Padrão "5 coisas que você precisa saber sobre X" — lista numerada
    elif fmt == "EDUCATIVO_CONTEXTO":
        return [
            capa(
                f"**2 minutos lendo isso vai mudar como você vê esse assunto.**\n\n"
                f"{title}",
                img_hint="imagem do tema educativo"
            ),
            corpo(
                f"O contexto:\n\n"
                f"{excerpt}\n\n"
                f"Fonte: {source}.",
            ),
            item_lista(
                1, "Isso não afeta quem está no longo prazo",
                f"Afeta sim — no curto prazo. E curto prazo importa porque "
                f"é quando a maioria das pessoas toma as piores decisões.\n\n"
                f"Saber o que está acontecendo não é pra você agir impulsivamente. "
                f"É pra você não agir por medo.",
            ),
            item_lista(
                2, "O mercado já sabe disso",
                f"O mercado sabe o que é público. O que está acontecendo agora ainda "
                f"está sendo processado.\n\n"
                f"Preços refletem consenso. E o consenso demora pra se formar.",
            ),
            item_lista(
                3, "Bitcoin vai subir ou cair com isso?",
                f"Essa é a pergunta errada.\n\n"
                f"A pergunta certa é: os fundamentos de longo prazo mudaram, "
                f"ou só o sentimento de curto prazo está distorcido?\n\n"
                f"Essa distinção é o que diferencia investidor de especulador.",
                continua=False
            ),
            final(
                f"Você não precisa ter todas as respostas.\n\n"
                f"Mas precisa fazer as perguntas certas.\n\n"
                f"Quem faz a pergunta certa no momento certo está sempre à frente."
            ),
        ]

    # ── DEFAULT / FALLBACK ────────────────────────────────────────────────────
    else:
        return [
            capa(
                f"**{title}**\n\n"
                f"Tem um detalhe nessa notícia que a maioria está ignorando.",
                img_hint="imagem relacionada"
            ),
            corpo(
                f"{excerpt}\n\nFonte: {source}.",
            ),
            corpo(
                f"Por que isso importa pra quem investe em cripto:\n\n"
                f"Nenhum ativo existe isolado do contexto macro e geopolítico.\n\n"
                f"Bitcoin reage a eventos globais — e entender essa conexão é "
                f"o que separa decisões de portfólio boas das ruins.",
                img_hint="gráfico Bitcoin"
            ),
            final(
                f"O dinheiro grande se move antes do varejo.\n\n"
                f"E deixa rastros nos dados on-chain e nos volumes de negociação.\n\n"
                f"Quem aprende a ler esses rastros nunca mais precisa adivinhar."
            ),
        ]


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

    # Campos do analista (injetados pelo server.py antes de chegar aqui)
    analyst_stars     = article.get("analyst_stars", 0)
    analyst_sentiment = article.get("analyst_sentiment", "neutro")
    analyst_note      = article.get("analyst_note", "")

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

    # Ícones de estrelas e sentimento para o frontend
    stars_icon = "★" * analyst_stars + "☆" * (3 - analyst_stars)
    sentiment_icon = {"positivo": "🟢", "negativo": "🔴", "neutro": "⚪"}.get(analyst_sentiment, "⚪")

    return {
        **article,
        "editorial_format":      fmt,
        "editorial_format_desc": FORMATS[fmt]["desc"],
        # Campos do analista no formato final
        "analyst_stars":         analyst_stars,
        "analyst_stars_icon":    stars_icon,
        "analyst_sentiment":     analyst_sentiment,
        "analyst_sentiment_icon": sentiment_icon,
        "analyst_note":          analyst_note,
        # Conteúdo editorial
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
