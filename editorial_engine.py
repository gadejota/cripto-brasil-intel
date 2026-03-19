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
    Script de reel — 20-35 segundos de fala.

    DNA (do guia editorial):
    ─ Tom: narrador analítico. Professor que achou um dado e quer que
      você entenda antes de todo mundo. Nunca hype, nunca FUD.
    ─ Estrutura obrigatória:
        ABERTURA  (5s) — dado ou contradição em 1 frase
        DESENVOLVIMENTO (20s) — 3 dados concretos com números reais,
                                 1 dado a cada ~6s
        AVISO HONESTO (5s) — "Agora o aviso que eu preciso te dar..."
        FECHAMENTO (5s) — ação ou reflexão, nunca CTA de compra
    ─ Linguagem proibida: "vai subir", "moon", "compra agora",
      "última chance", dados sem fonte ou período.
    ─ Linguagem obrigatória: "historicamente", período exato,
      valores em reais quando falar de impacto BR.
    """
    title  = article.get("title", "")
    excerpt = article.get("excerpt", article.get("desc", title))[:400]
    source  = article.get("source_name", article.get("src", ""))
    cls    = article.get("_cls", article.get("cls", "edu"))

    # Extrai números do título para tornar o script mais concreto
    import re
    nums = re.findall(r"[\$R\€]?[\d,\.]+\s*(?:%|bilh|trilh|mil|k|m|b)?", title.lower())
    num1 = nums[0].strip() if nums else ""
    num2 = nums[1].strip() if len(nums) > 1 else ""

    if fmt == "ALERTA_MERCADO":
        aviso = f"Agora o aviso que eu preciso te dar: isso não significa que vai continuar caindo. Significa que o mercado está processando uma informação que a maioria ainda não entendeu."
        return f"""Deixa eu te mostrar o número que a mídia não contextualizou.

{title}

{excerpt}

Fonte: {source}.

{("O número central aqui: " + num1 + ". Mas o contexto é o que muda tudo." + chr(10)) if num1 else ""}Historicamente, eventos desse tipo geram dois momentos distintos: primeiro a reação emocional do varejo — que é rápida e exagerada. Depois a correção pelos dados reais — que é onde estão as oportunidades.

{aviso}

Salva esse vídeo. Não pela previsão. Pelo lembrete de como o mercado se comporta quando o medo está alto."""

    elif fmt == "CORRENTE_IMPACTO":
        return f"""Isso aconteceu lá fora. Deixa eu te mostrar como chega no seu bolso.

{title}

{excerpt}

Fonte: {source}.

A corrente completa: esse evento pressiona o petróleo. Petróleo pressiona inflação global. Inflação faz o Fed hesitar em cortar juros. Mercados de risco corrigem. Bitcoin vai junto — não porque os fundamentos mudaram, mas porque os algoritmos institucionais ainda classificam BTC como ativo de risco.

{("E no Brasil: dólar sobe, real cai, e quem compra Bitcoin em reais paga duas vezes." + chr(10)) if cls in ("br","geo","macro") else ""}
Agora o aviso que eu preciso te dar: a corrente pode se desfazer em semanas. Quando o mercado percebe que os fundamentos cripto não mudaram, a recuperação costuma ser mais rápida do que a queda.

Salva esse vídeo. Não pela previsão. Pelo mecanismo."""

    elif fmt == "ANGULO_BRASIL":
        return f"""O número que quase ninguém está contextualizando pra quem investe no Brasil.

{title}

{excerpt}

Fonte: {source}.

Três dados que a análise em inglês ignora: primeiro, você compra Bitcoin em dólar, mas investe em reais — o câmbio entra na equação antes de qualquer movimento de preço. Segundo, a Selic a dois dígitos compete diretamente com cripto pelo mesmo capital. Terceiro, o IOF e as taxas de conversão aumentam seu custo de entrada em até 6%.

Agora o aviso que eu preciso te dar: isso não é pessimismo. É a realidade de operar num país de moeda fraca com ativo dolarizado. Quem ignora essa equação toma decisão com metade das informações.

O que você vai querer ter entendido daqui a 2 anos? Esse contexto."""

    elif fmt == "CONTRAINTUITIVO":
        return f"""A narrativa dominante sobre isso está errada. Vou te mostrar os dados.

{title}

{excerpt}

Fonte: {source}.

{("O número central: " + num1 + ". Parece ruim. Mas o histórico diz outra coisa." + chr(10)) if num1 else ""}Historicamente, os momentos de maior medo no cripto — novembro 2018, março 2020, novembro 2022 — foram os melhores pontos de entrada documentados. Não porque alguém previu. Porque os fundamentos não tinham mudado, só o sentimento.

Agora o aviso que eu preciso te dar: isso não significa que vai repetir agora. Significa que a pergunta certa não é "vai subir?" — é "os fundamentos mudaram?"

Salva esse vídeo. Vai ser útil quando o medo estiver maior do que está agora."""

    elif fmt == "PREVISAO_ACERTADA":
        return f"""Isso aconteceu 3 vezes na história. Vou te contar o que veio depois.

{title}

{excerpt}

Fonte: {source}.

{("O dado específico que está sendo apontado: " + num1 + "." + chr(10)) if num1 else ""}Analistas que acertam previsões improváveis não são sortudos — eles enxergam conexões que o mercado ainda não precificou. E quando o mercado finalmente precifica, já é tarde para a maioria.

Agora o aviso que eu preciso te dar: bom histórico não é garantia. A questão é entender o raciocínio por trás — não seguir cegamente.

O que você vai querer ter feito daqui a 4 anos quando olhar pra esse momento?"""

    elif fmt == "COMPARACAO_HISTORICA":
        return f"""Isso já aconteceu antes. Deixa eu te contar o que veio depois.

{title}

{excerpt}

Fonte: {source}.

Três paralelos documentados: março de 2020, Bitcoin caiu 50% em 48 horas e subiu 1.200% nos 13 meses seguintes. Novembro de 2022, colapso FTX mais inflação mais guerra — Bitcoin a $15k, quem comprou ali tem mais de 300% hoje. Em todos os casos: os fundamentos não tinham mudado. Só o sentimento.

Agora o aviso que eu preciso te dar: a história não se repete com as mesmas datas e os mesmos números. O que se repete é o mecanismo — pânico de varejo, acumulação silenciosa, recuperação quando o consenso muda.

Salva esse vídeo. Não pela previsão. Pelo registro histórico."""

    else:  # EDUCATIVO_CONTEXTO
        return f"""Deixa eu te mostrar o contexto que está faltando nessa notícia.

{title}

{excerpt}

Fonte: {source}.

{("O número que muda a leitura: " + num1 + "." + chr(10)) if num1 else ""}O mercado processa informações em camadas: primeiro a manchete — reação emocional, rápida e geralmente exagerada. Depois o contexto — onde estão as decisões que realmente importam. A maioria das pessoas só chega na primeira camada.

Agora o aviso que eu preciso te dar: entender o contexto não é pra você agir impulsivamente. É pra você não agir por medo. A diferença entre quem perde e quem ganha nesse mercado, na maioria das vezes, não é timing — é clareza.

Salva esse vídeo. Vai ser útil quando o medo estiver maior do que está agora."""


def carousel_slides(article: dict, fmt: str) -> list:
    """
    Carrossel 7-9 slides — DNA do guia editorial:

    SLIDE 1 CAPA: contradição ou dado impossível
      → "Quem está perdendo dinheiro AGORA não é quem você pensa"
      → A capa deve fazer o leitor pensar "isso não pode estar certo"
      → NUNCA: "Bitcoin caiu 47%"

    SLIDES 2-3 CONTEXTO: número da mídia vs número real
      → Inclui período exato, valor investido, retorno em reais

    SLIDES 4-6 PROFUNDIDADE:
      → Dados on-chain, histórico de ciclos
      → AVISO HONESTO obrigatório (slide dedicado)
      → Nunca pula o aviso

    SLIDES 7-8 MECANISMO:
      → Por que estrutural, não "vai subir"
      → Foca no que mudou nesse ciclo vs. anteriores

    SLIDE 9 FECHAMENTO:
      → Ação concreta OU pergunta reflexiva
      → Fórmula: "Salva esse carrossel. Não pela análise.
                   Pelo registro de como você estava se sentindo agora."
    """
    title   = article.get("title", "")
    excerpt = article.get("excerpt", article.get("desc", title))[:500]
    source  = article.get("source_name", article.get("src", ""))
    cls     = article.get("_cls", article.get("cls", "edu"))

    import re
    nums = re.findall(r"[\$R\€]?[\d,\.]+\s*(?:%|bilh|trilh|mil|k|m|b)?", title.lower())
    num1 = nums[0].strip() if nums else ""
    num2 = nums[1].strip() if len(nums) > 1 else ""

    def capa(txt, img=""):
        return {"role": "capa",  "t": txt, "img": img, "arrow": False}
    def corpo(txt, img=""):
        return {"role": "corpo", "t": txt + "\n\n👇", "img": img, "arrow": True}
    def aviso(txt):
        return {"role": "aviso", "t": "⚠️ O AVISO HONESTO\n\n" + txt, "img": "", "arrow": True}
    def mecanismo(txt, img=""):
        return {"role": "mecanismo", "t": txt + "\n\n👇", "img": img, "arrow": True}
    def final(txt):
        return {"role": "final", "t": txt, "img": "", "arrow": False}

    # ── ALERTA_MERCADO ────────────────────────────────────────────────────────
    if fmt == "ALERTA_MERCADO":
        return [
            capa(
                f"Quem está ERRANDO agora não é quem você pensa.\n\n**{title}**",
                img="gráfico queda dramática — dark editorial"
            ),
            corpo(
                f"**O que a mídia está dizendo:**\n\n{excerpt}\n\nFonte: {source}.",
                img="print da notícia"
            ),
            corpo(
                f"**O número que quase ninguém está contextualizando:**\n\n"
                f"{'Dado central: ' + num1 + chr(10) + chr(10) if num1 else ''}"
                f"Em março de 2020, Bitcoin caiu **50% em 48 horas**. "
                f"Quem comprou no pânico subiu **+1.200%** nos 13 meses seguintes.\n\n"
                f"Em novembro de 2022, FTX colapsou. Bitcoin a **$15k**. "
                f"Retorno para quem comprou: **+300%** até hoje.\n\n"
                f"Nos dois casos: os fundamentos não tinham mudado. Só o sentimento.",
                img="gráfico histórico BTC ciclos"
            ),
            corpo(
                f"**O que os dados on-chain mostram agora:**\n\n"
                f"Quando grandes players vendem no varejo e acumulam on-chain, "
                f"o movimento de preço e o movimento real de Bitcoin vão em direções opostas.\n\n"
                f"Esse padrão precedeu as duas maiores recuperações documentadas.",
            ),
            aviso(
                f"Isso não significa que vai parar de cair agora.\n\n"
                f"Pode cair mais. Pode demorar mais. Ciclos não têm calendário.\n\n"
                f"O que a história documenta é o mecanismo — não a data.\n\n"
                f"Quem age com certeza em momentos de pânico geralmente está errado."
            ),
            corpo(
                f"**O que monitorar nas próximas 48-72h:**\n\n"
                f"Volume de Bitcoin saindo de exchanges (acumulação ou fuga?).\n\n"
                f"Open interest em futuros (alavancagem acumulada = risco de liquidação).\n\n"
                f"Dominância do BTC vs altcoins (rotação de capital ou saída total?).",
            ),
            mecanismo(
                f"**O mecanismo que se repete:**\n\n"
                f"1. Evento externo gera pânico.\n"
                f"2. Varejo vende. Institucional acumula.\n"
                f"3. Preço vai contra o movimento real de BTC.\n"
                f"4. Quando o consenso muda, o preço ajusta rapidamente.\n\n"
                f"A janela de oportunidade costuma ser de dias, não semanas.",
                img="diagrama ciclo de pânico"
            ),
            final(
                f"Salva esse carrossel.\n\n"
                f"Não pela análise.\n\n"
                f"**Pelo registro de como você estava se sentindo agora.**\n\n"
                f"Daqui a 4 anos, quando você olhar pra esse momento, vai querer lembrar o que escolheu fazer com o medo.\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── CORRENTE_IMPACTO ──────────────────────────────────────────────────────
    elif fmt == "CORRENTE_IMPACTO":
        return [
            capa(
                f"Parece distante. Não é.\n\n**{title}**\n\nDeixa eu te mostrar onde isso chega.",
                img="mapa geopolítico dark com linhas de conexão"
            ),
            corpo(
                f"**O que aconteceu:**\n\n{excerpt}\n\nFonte: {source}.",
                img="imagem do evento"
            ),
            corpo(
                f"**Elo 1 — Energia e inflação:**\n\n"
                f"Instabilidade em regiões produtoras pressiona o barril.\n\n"
                f"Petróleo caro encarece logística, produção, tudo.\n\n"
                f"Fed, que estava prestes a cortar juros, hesita.\n\n"
                f"**Cortar juros com inflação subindo seria um erro histórico.**",
                img="gráfico petróleo vs inflação"
            ),
            corpo(
                f"**Elo 2 — Mercados de risco:**\n\n"
                f"A alta dos mercados foi alimentada pela expectativa de cortes.\n\n"
                f"Quando essa expectativa recua, o dinheiro institucional sai.\n\n"
                f"Ações de tech caem. Nasdaq corrige. **Bitcoin vai junto** — "
                f"não porque os fundamentos mudaram, mas porque os algoritmos "
                f"ainda classificam BTC como ativo de risco.",
                img="gráfico Nasdaq vs BTC correlação"
            ),
            corpo(
                f"**Elo 3 — O Brasil:**\n\n"
                f"Turbulência global = dólar forte = real fraco.\n\n"
                f"Quem compra Bitcoin em reais **paga duas vezes**:\n\n"
                f"Quando o BTC cai em dólar — e quando o dólar sobe em reais.\n\n"
                f"Esse duplo efeito é ignorado por quem só olha o preço em dólar.",
                img="gráfico USD/BRL"
            ),
            aviso(
                f"Essa corrente pode se desfazer mais rápido do que se formou.\n\n"
                f"Quando o mercado percebe que os fundamentos cripto não mudaram, "
                f"a recuperação costuma ser mais rápida do que a queda.\n\n"
                f"Isso não é previsão. É o registro histórico de como esse mecanismo funciona."
            ),
            mecanismo(
                f"**O que mudou nesse ciclo vs. anteriores:**\n\n"
                f"ETFs de Bitcoin aprovados = demanda institucional estrutural.\n\n"
                f"Halving de 2024 = redução de oferta já precificada no long run.\n\n"
                f"Adoção corporativa crescente = base de suporte mais alta a cada ciclo.\n\n"
                f"**O contexto macro muda o preço de curto prazo.\n"
                f"Os fundamentos determinam o piso de longo prazo.**",
                img="timeline ciclos BTC com ETFs"
            ),
            final(
                f"Entender a corrente inteira é o que separa quem reage de quem antecipa.\n\n"
                f"**O evento aconteceu lá fora. O impacto chega aqui.**\n\n"
                f"Salva esse carrossel. Vai ser útil quando o próximo evento aparecer.\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── ANGULO_BRASIL ─────────────────────────────────────────────────────────
    elif fmt == "ANGULO_BRASIL":
        return [
            capa(
                f"Ninguém está te contando o que isso significa **em reais**.\n\n**{title}**",
                img="mapa Brasil + tela Bloomberg dark"
            ),
            corpo(
                f"**O que aconteceu:**\n\n{excerpt}\n\nFonte: {source}.",
                img="print da notícia"
            ),
            corpo(
                f"**O número que a análise em inglês ignora:**\n\n"
                f"Um Bitcoin que sobe **20% em dólar**, mas o dólar cai **15%** contra o real "
                f"= só **5% de ganho** pra você.\n\n"
                f"O contrário também é verdade: BTC estável em dólar + dólar subindo "
                f"= você lucrou sem nenhum movimento do ativo.\n\n"
                f"**A maioria dos iniciantes em cripto no Brasil nunca calculou isso.**",
            ),
            corpo(
                f"**Três variáveis que o investidor BR precisa monitorar:**\n\n"
                f"**1.** Preço do BTC em reais, não só em dólar.\n\n"
                f"**2.** Selic: a renda fixa compete diretamente com cripto pelo mesmo capital. "
                f"Com Selic acima de 10%, o custo de oportunidade é real.\n\n"
                f"**3.** IOF + taxas: aumentam seu custo de entrada em até 6% antes de qualquer movimento.",
            ),
            aviso(
                f"Isso não é pessimismo sobre o cripto.\n\n"
                f"É a realidade de operar em país de moeda fraca com ativo dolarizado.\n\n"
                f"Ignorar essa equação não faz ela desaparecer.\n\n"
                f"Entendê-la é uma vantagem competitiva real frente a quem só lê análise em inglês."
            ),
            mecanismo(
                f"**O que os melhores investidores BR fazem diferente:**\n\n"
                f"Acompanham o preço do BTC **em reais** como dado primário.\n\n"
                f"Usam DCA em reais com disciplina — não tentam acertar câmbio e BTC ao mesmo tempo.\n\n"
                f"Mantêm parte em stablecoins dolarizadas para aproveitar oportunidades "
                f"quando real e BTC estão simultaneamente favoráveis.",
            ),
            final(
                f"O investidor brasileiro que ignora o contexto cambial e de juros "
                f"está tomando decisão com metade das informações.\n\n"
                f"**Salva esse carrossel. Vai mudar como você lê qualquer análise de cripto.**\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── CONTRAINTUITIVO ───────────────────────────────────────────────────────
    elif fmt == "CONTRAINTUITIVO":
        return [
            capa(
                f"Parece ruim. Os dados dizem o oposto.\n\n**{title}**",
                img="gráfico aparentemente negativo com seta verde"
            ),
            corpo(
                f"**O que todo mundo está dizendo:**\n\n{excerpt}\n\nFonte: {source}.",
            ),
            corpo(
                f"**O número que quase ninguém está contextualizando:**\n\n"
                f"{'Dado central: ' + num1 + chr(10) + chr(10) if num1 else ''}"
                f"Em novembro de 2018, narrativa idêntica. Bitcoin a $3.200. "
                f"12 meses depois: $13.000.\n\n"
                f"Em março de 2020, narrativa idêntica. Bitcoin a $4.000. "
                f"12 meses depois: $58.000.\n\n"
                f"**Nos dois casos, o mercado estava errado sobre o que os dados mostravam.**",
            ),
            corpo(
                f"**Por que o consenso erra nesses momentos:**\n\n"
                f"O mercado precifica o que já é consenso — e o consenso é sempre atrasado.\n\n"
                f"O que está acontecendo agora ainda não é consenso. Ainda não está nos preços.\n\n"
                f"Quando virar consenso, a oportunidade já terá passado para a maioria.",
            ),
            aviso(
                f"Dados históricos não são garantia de repetição.\n\n"
                f"O Bitcoin pode cair mais. O ciclo pode demorar mais.\n\n"
                f"O que a história documenta é o **mecanismo** — não o calendário.\n\n"
                f"Quem age com certeza absoluta em qualquer direção geralmente paga por isso."
            ),
            mecanismo(
                f"**O mecanismo por trás do contraintuitivo:**\n\n"
                f"1. Evento negativo → narrativa pessimista dominante.\n"
                f"2. Varejo vende. Smart money observa fundamentos.\n"
                f"3. Se fundamentos intactos → divergência entre preço e valor.\n"
                f"4. Convergência: rápida, quando o consenso finalmente muda.\n\n"
                f"**A pergunta certa: os fundamentos mudaram ou só o sentimento?**",
            ),
            final(
                f"Salva esse carrossel.\n\n"
                f"Não pela conclusão.\n\n"
                f"**Pelo registro de como o mercado estava se sentindo agora.**\n\n"
                f"Daqui a alguns anos, vai ser útil ver esse momento de fora.\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── PREVISAO_ACERTADA ─────────────────────────────────────────────────────
    elif fmt == "PREVISAO_ACERTADA":
        return [
            capa(
                f"Ele disse isso meses atrás. O mercado ignorou. Aconteceu.\n\n**{title}**",
                img="print da previsão + gráfico confirmando"
            ),
            corpo(
                f"**O contexto completo:**\n\n{excerpt}\n\nFonte: {source}.",
                img="print da análise original"
            ),
            corpo(
                f"**Por que bom histórico importa:**\n\n"
                f"Analistas com track record não são sortudos.\n\n"
                f"Eles enxergam conexões que o mercado ainda não precificou — "
                f"e agem antes do consenso se formar.\n\n"
                f"{'O dado específico apontado: ' + num1 + chr(10) + chr(10) if num1 else ''}"
                f"É exatamente nessa janela — entre o insight e o consenso — "
                f"que estão os maiores retornos documentados.",
            ),
            aviso(
                f"Bom histórico não é garantia de acerto futuro.\n\n"
                f"Nenhum analista acerta 100% do tempo.\n\n"
                f"O que importa entender é **o raciocínio por trás** — não só a conclusão.\n\n"
                f"Seguir cegamente qualquer analista, independente do histórico, é tão perigoso "
                f"quanto ignorá-los completamente."
            ),
            corpo(
                f"**O que você deve fazer com essa informação:**\n\n"
                f"Não copiar. Entender.\n\n"
                f"Pegar o raciocínio, verificar os dados na fonte, e então decidir "
                f"se faz sentido **para a sua situação específica**.\n\n"
                f"Portfólio é pessoal. Contexto é universal.",
            ),
            mecanismo(
                f"**O padrão que analistas com bom histórico têm em comum:**\n\n"
                f"Ignoram o consenso quando os dados apontam outra direção.\n\n"
                f"Dão mais peso a dados on-chain do que a sentimento de mercado.\n\n"
                f"Fazem previsões impopulares quando o momento exige — e ficam quietos "
                f"quando não têm convicção.",
            ),
            final(
                f"Você não precisa concordar com tudo que especialistas dizem.\n\n"
                f"Mas precisa saber o que estão dizendo.\n\n"
                f"**Salva esse carrossel. A pergunta certa não é 'ele está certo?'\n"
                f"É 'qual o raciocínio dele e ele bate com os dados?'**\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── COMPARACAO_HISTORICA ──────────────────────────────────────────────────
    elif fmt == "COMPARACAO_HISTORICA":
        return [
            capa(
                f"Isso já aconteceu antes. Exatamente assim.\n\n**{title}**\n\nDeixa eu te mostrar o que veio depois.",
                img="gráfico histórico longo prazo BTC"
            ),
            corpo(
                f"**O evento de hoje:**\n\n{excerpt}\n\nFonte: {source}.",
            ),
            corpo(
                f"**Março de 2020:**\n\nCOVID. Lockdown global. Pânico total.\n\n"
                f"Bitcoin caiu **-50% em 48 horas**. Narrativa: 'acabou'.\n\n"
                f"13 meses depois: **+1.200%** do fundo.\n\n"
                f"Quem comprou no pânico multiplicou por 12.",
                img="gráfico BTC março 2020"
            ),
            corpo(
                f"**Novembro de 2022:**\n\nColapso FTX + inflação + guerra.\n\n"
                f"Bitcoin a **$15.000**. Narrativa: 'crypto morreu'.\n\n"
                f"Resultado para quem comprou entre $15k e $20k: **+300%** hoje.\n\n"
                f"**Nos dois casos: fundamentos intactos. Só o sentimento mudou.**",
                img="gráfico BTC novembro 2022"
            ),
            aviso(
                f"A história não se repete com as mesmas datas e os mesmos números.\n\n"
                f"Pode cair mais. Pode demorar mais. Pode ser diferente dessa vez.\n\n"
                f"O que se repete é o **mecanismo**: pânico de varejo, acumulação silenciosa, "
                f"recuperação quando o consenso muda.\n\n"
                f"Isso não é previsão. É o registro histórico documentado."
            ),
            mecanismo(
                f"**O que mudou nesse ciclo vs. anteriores:**\n\n"
                f"ETFs spot aprovados = demanda institucional que não existia em 2020 ou 2022.\n\n"
                f"Halving de 2024 = pressão de oferta estrutural.\n\n"
                f"Adoção corporativa crescente = piso de suporte mais alto a cada ciclo.\n\n"
                f"**O contexto macro muda o timing. Os fundamentos determinam a direção.**",
                img="comparativo ciclos BTC"
            ),
            final(
                f"Salva esse carrossel.\n\n"
                f"Não pela análise.\n\n"
                f"**Pelo registro de como você estava se sentindo agora.**\n\n"
                f"Daqui a 4 anos, quando você olhar pra esse momento, vai querer ter feito algo com o medo.\n\n"
                f"@criptobrasilofc"
            ),
        ]

    # ── EDUCATIVO_CONTEXTO ────────────────────────────────────────────────────
    else:
        return [
            capa(
                f"O número que quase ninguém está contextualizando.\n\n**{title}**",
                img="infográfico dark com dado central em destaque"
            ),
            corpo(
                f"**O contexto que está faltando:**\n\n{excerpt}\n\nFonte: {source}.",
            ),
            corpo(
                f"**O número da mídia vs. o número que importa:**\n\n"
                f"{'Dado central: ' + num1 + chr(10) + chr(10) if num1 else ''}"
                f"A mídia usa o número que chama atenção. "
                f"O analista usa o número que explica o que está acontecendo.\n\n"
                f"São quase sempre números diferentes.",
            ),
            corpo(
                f"**O mecanismo por trás do evento:**\n\n"
                f"Eventos como esse se movem em camadas:\n\n"
                f"Primeira camada: o que aparece na manchete.\n"
                f"Segunda camada: o que os dados on-chain mostram.\n"
                f"Terceira camada: o impacto real no preço — que vem com atraso de dias ou semanas.\n\n"
                f"A maioria das pessoas reage na primeira camada.",
            ),
            aviso(
                f"Entender o contexto não significa que você sabe o que vai acontecer.\n\n"
                f"Significa que você vai errar menos por impulso e mais por decisão consciente.\n\n"
                f"Isso já é uma vantagem enorme frente a quem age só pela manchete."
            ),
            mecanismo(
                f"**O que fazer com essa informação:**\n\n"
                f"Não agir com pressa. Verificar os dados na fonte.\n\n"
                f"Perguntar: os fundamentos de longo prazo mudaram?\n\n"
                f"Se a resposta for não — o que você está vendo é ruído.\n\n"
                f"**Ruído com oportunidade embutida.**",
            ),
            final(
                f"Salva esse carrossel.\n\n"
                f"**2 minutos lendo isso vai mudar como você lê as próximas 100 notícias de cripto.**\n\n"
                f"@criptobrasilofc"
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
