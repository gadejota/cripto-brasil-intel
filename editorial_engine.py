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
    Roteiro de reel 20-35 segundos. 4 partes obrigatórias:

    [ABERTURA 5s]    — 1 frase: dado/contradição que prende
    [DESENVOLVIMENTO 20s] — 3 dados concretos com período e número real
                            (não despeja excerpt bruto — SINTETIZA)
    [AVISO HONESTO 5s] — "Agora o aviso que eu preciso te dar..."
    [FECHAMENTO 5s]  — reflexão/ação, nunca CTA de compra

    Proibido: "vai subir", "moon", dados sem período, excerpt cru.
    Obrigatório: "historicamente", período exato (mês/ano), valores em R$.
    Total: ~100-150 palavras (35s falado a 4 palavras/segundo).
    """
    title  = article.get("title", "")
    desc   = article.get("excerpt", article.get("desc", ""))
    source = article.get("source_name", article.get("src", ""))
    cls    = article.get("_cls", article.get("cls", "edu"))

    import re
    # Extrai números reais do título e desc para o desenvolvimento
    raw_nums = re.findall(
        r"(?:US\$|R\$|\$|€)?\s*[\d]+(?:[,\.][\d]+)*\s*(?:bilh(?:ões|ao)?|trilh(?:ões|ao)?|milh(?:ões|ao)?|mil|k|m|b|%)?",
        (title + " " + desc).lower()
    )
    nums = [n.strip() for n in raw_nums if n.strip() and len(n.strip()) > 1][:3]
    n1 = nums[0] if nums else ""
    n2 = nums[1] if len(nums) > 1 else ""
    n3 = nums[2] if len(nums) > 2 else ""

    # ── ABERTURA: 1 frase que prende, extrai o dado central do título ─────────
    def abertura(hook: str) -> str:
        return hook

    # ── DESENVOLVIMENTO: 3 dados com período — sintetiza da notícia ──────────
    # Ciclos históricos reais para contextualizar
    historico_bear = (
        "Novembro de 2018: Bitcoin a $3.200. Doze meses depois: $13.000. "
        "Março de 2020: Bitcoin a $4.000. Treze meses depois: $58.000. "
        "Novembro de 2022: Bitcoin a $15.000. Hoje: mais de 300% acima."
    )

    historico_etf = (
        "Desde a aprovação dos ETFs spot em janeiro de 2024, "
        "mais de $35 bilhões entraram via BlackRock e Fidelity. "
        "Isso é demanda estrutural — não especulativa."
    )

    historico_br = (
        "Quem compra Bitcoin em reais paga duas vezes: quando o BTC cai em dólar "
        "e quando o dólar sobe em reais. "
        "Com Selic acima de 10%, a renda fixa compete pelo mesmo capital."
    )

    # ── AVISO HONESTO ─────────────────────────────────────────────────────────
    aviso_base = "Agora o aviso que eu preciso te dar:"

    # ─────────────────────────────────────────────────────────────────────────
    if fmt == "ALERTA_MERCADO":
        num_dado = f"O dado central aqui: {n1}." if n1 else "O contexto é o que muda tudo."
        return f"""Deixa eu te mostrar o número que a mídia não contextualizou.

{num_dado}

Primeiro dado: {historico_bear}

Segundo dado: nos três casos, os fundamentos on-chain não mudaram antes da recuperação. Só o sentimento mudou.

Terceiro dado: a janela entre o pânico máximo e a recuperação foi de dias — não meses. Quem esperou certeza entrou mais caro.

{aviso_base} isso não significa que o fundo foi agora. Pode cair mais. Ciclos não têm calendário. O que a história documenta é o mecanismo — não a data.

Salva esse vídeo. Não pela previsão. Pelo lembrete de como você estava se sentindo quando o medo estava alto."""

    elif fmt == "CORRENTE_IMPACTO":
        abertura_txt = "Isso aconteceu lá fora. Vou te mostrar exatamente onde isso chega no seu bolso."
        dado_br = f"E no Brasil: dólar sobe, real cai. {historico_br}" if cls in ("br","geo","macro") else ""
        return f"""{abertura_txt}

Primeiro dado: conflito ou incerteza global pressiona petróleo. Petróleo caro eleva inflação. Inflação alta faz o Fed hesitar em cortar juros.

Segundo dado: quando o Fed hesita, dinheiro institucional sai de ativos de risco. Nasdaq corrige. Bitcoin vai junto — não porque os fundamentos cripto mudaram, mas porque algoritmos ainda classificam BTC como risco.

Terceiro dado: {dado_br if dado_br else "desde 2020, a correlação entre Bitcoin e Nasdaq em momentos de stress macro é de 0,7 — mais alta do que o mercado espera."}

{aviso_base} essa corrente pode se desfazer em semanas. Historicamente, quando o mercado percebe que os fundamentos cripto não mudaram, a recuperação é mais rápida que a queda.

Salva esse vídeo. Não pela previsão. Pelo mecanismo."""

    elif fmt == "ANGULO_BRASIL":
        return f"""O número que quase ninguém está contextualizando pra quem investe no Brasil.

Primeiro dado: {historico_br}

Segundo dado: um Bitcoin que sobe 20% em dólar, mas o dólar cai 15% contra o real, significa só 5% de ganho pra você. O inverso também é verdade — e a maioria dos iniciantes nunca calculou isso.

Terceiro dado: IOF mais taxas de conversão aumentam seu custo de entrada em até 6% antes de qualquer movimento do ativo.

{aviso_base} isso não é pessimismo sobre o cripto. É a realidade de operar em país de moeda fraca com ativo dolarizado. Quem ignora essa equação toma decisão com metade das informações.

Daqui a dois anos, quando você olhar pra esse momento, vai querer ter entendido isso antes."""

    elif fmt == "CONTRAINTUITIVO":
        num_dado = f"O dado central: {n1}. Parece ruim. O histórico diz outra coisa." if n1 else "A narrativa dominante está errada. Os dados dizem o oposto."
        return f"""{num_dado}

Primeiro dado: {historico_bear}

Segundo dado: nos três casos, o que diferenciou quem ganhou de quem perdeu não foi timing. Foi a resposta a uma pergunta simples: os fundamentos do ativo mudaram?

Terceiro dado: on-chain, nos três fundos históricos, a acumulação de wallets de longo prazo aumentou enquanto o preço caía. Demanda silenciosa antes da recuperação pública.

{aviso_base} isso não significa que vai repetir agora. Significa que a pergunta certa não é "vai subir?" — é "os fundamentos mudaram?"

Salva esse vídeo. Vai ser útil quando o medo estiver maior do que está agora."""

    elif fmt == "PREVISAO_ACERTADA":
        num_dado = f"O dado específico apontado: {n1}." if n1 else ""
        return f"""Isso aconteceu 3 vezes na história. Vou te contar o que veio depois.

{num_dado}

Primeiro dado: analistas com bom track record não são sortudos — eles enxergam conexões antes do mercado precificar. A janela entre o insight e o consenso é onde estão os maiores retornos documentados.

Segundo dado: {historico_etf}

Terceiro dado: historicamente, quando análise vai contra o consenso e o consenso está errado, a correção de preço é proporcional ao tamanho da divergência.

{aviso_base} bom histórico não é garantia. Nenhum analista acerta 100% do tempo. O que importa é entender o raciocínio — não seguir cegamente.

O que você vai querer ter feito daqui a 4 anos quando olhar pra esse momento?"""

    elif fmt == "COMPARACAO_HISTORICA":
        return f"""Isso já aconteceu antes. Deixa eu te contar exatamente o que veio depois.

Primeiro dado: março de 2020 — Bitcoin caiu 50% em 48 horas. Treze meses depois: alta de 1.200% do fundo. Quem comprou no pânico multiplicou por 12.

Segundo dado: novembro de 2022 — colapso FTX, inflação, guerra. Bitcoin a $15.000. Hoje, quem comprou entre $15k e $20k tem mais de 300%. Em ambos os casos: fundamentos intactos, só o sentimento tinha mudado.

Terceiro dado: {historico_etf}

{aviso_base} a história não se repete com as mesmas datas e os mesmos números. O que se repete é o mecanismo: pânico de varejo, acumulação silenciosa, recuperação quando o consenso muda.

Salva esse vídeo. Não pela previsão. Pelo registro histórico."""

    else:  # EDUCATIVO_CONTEXTO
        num_dado = f"O número que muda a leitura: {n1}." if n1 else "O contexto que está faltando nessa notícia."
        return f"""Deixa eu te mostrar o contexto que quase ninguém está contextualizando.

{num_dado}

Primeiro dado: o mercado processa informações em camadas. Primeiro a manchete — reação emocional, rápida e exagerada. Depois o contexto — onde estão as decisões que realmente importam. A maioria das pessoas só chega na primeira camada.

Segundo dado: {historico_etf}

Terceiro dado: historicamente, quando narrativa e fundamentos divergem, os fundamentos sempre vencem — com atraso de dias ou semanas. É nessa defasagem que estão as oportunidades documentadas.

{aviso_base} entender o contexto não é pra você agir impulsivamente. É pra você não agir por medo.

Salva esse vídeo. Vai ser útil quando o medo estiver maior do que está agora."""


def carousel_slides(article: dict, fmt: str) -> list:
    """
    Carrossel 7-9 slides. Estrutura do guia editorial:

    SLIDE 1 — CAPA: contradição ou dado impossível
      ✅ "Quem está perdendo dinheiro AGORA não é quem você pensa"
      ❌ "Bitcoin caiu 47%"
      Regra: deve fazer o leitor pensar "isso não pode estar certo"

    SLIDES 2-3 — CONTEXTO QUE FALTA
      Número da mídia VS número que importa. Período exato. Retorno em R$.

    SLIDES 4-6 — PROFUNDIDADE HONESTA
      Dados on-chain, histórico de ciclos.
      AVISO HONESTO em slide dedicado — OBRIGATÓRIO, nunca pulado.

    SLIDES 7-8 — MECANISMO
      Por que estrutural — não "vai subir". O que mudou nesse ciclo.

    SLIDE 9 — FECHAMENTO
      "Salva esse carrossel. Não pela análise.
       Pelo registro de como você estava se sentindo agora."
    """
    title   = article.get("title", "")
    desc    = article.get("excerpt", article.get("desc", ""))
    source  = article.get("source_name", article.get("src", ""))
    cls     = article.get("_cls", article.get("cls", "edu"))

    import re
    raw_nums = re.findall(
        r"(?:US\$|R\$|\$|€)?\s*[\d]+(?:[,\.][\d]+)*\s*(?:bilh(?:ões|ao)?|trilh(?:ões|ao)?|milh(?:ões|ao)?|mil|k|m|b|%)?",
        (title + " " + desc).lower()
    )
    nums = [n.strip() for n in raw_nums if n.strip() and len(n.strip()) > 1][:3]
    n1 = nums[0] if nums else ""
    n2 = nums[1] if len(nums) > 1 else ""

    def capa(txt, img=""):
        return {"role": "capa",  "t": txt, "img": img, "arrow": False}
    def corpo(txt, img=""):
        return {"role": "corpo", "t": txt + "\n\n👇", "img": img, "arrow": True}
    def aviso(txt):
        return {"role": "aviso", "t": "⚠️ O AVISO HONESTO\n\n" + txt + "\n\n👇", "img": "", "arrow": True}
    def mecanismo(txt, img=""):
        return {"role": "mecanismo", "t": txt + "\n\n👇", "img": img, "arrow": True}
    def final(txt):
        return {"role": "final",  "t": txt, "img": "", "arrow": False}

    # Contextos históricos reutilizáveis (dados reais, com período)
    H_BEAR = (
        "**Março de 2020:** BTC −50% em 48h → +1.200% nos 13 meses seguintes.\n\n"
        "**Novembro de 2022:** FTX + inflação + guerra → BTC a $15k → +300% hoje.\n\n"
        "Nos dois casos: fundamentos intactos. Só o sentimento tinha mudado."
    )
    H_ETF = (
        "Desde a aprovação dos ETFs spot em **janeiro de 2024**, mais de "
        "**$35 bilhões** entraram via BlackRock e Fidelity.\n\n"
        "Demanda estrutural — não especulativa."
    )
    H_BR = (
        "Você compra BTC em dólar, mas investe em reais.\n\n"
        "BTC +20% em dólar + dólar −15% em reais = só **+5% pra você**.\n\n"
        "Com Selic acima de 10%, a renda fixa compete pelo mesmo capital."
    )

    # ── ALERTA_MERCADO ────────────────────────────────────────────────────────
    if fmt == "ALERTA_MERCADO":
        num_ctx = f"O dado central: **{n1}**." if n1 else ""
        return [
            capa(
                "Quem está ERRANDO agora não é quem você pensa.\n\n"
                f"**{title}**",
                img="gráfico queda — dark editorial, vermelho"
            ),
            corpo(
                "**O número que a mídia está usando:**\n\n"
                f"{num_ctx}\n\n"
                f"Fonte: {source}.\n\n"
                "Esse é o número que chama atenção. Não é o número que importa.",
                img="print da notícia"
            ),
            corpo(
                "**O número que realmente importa:**\n\n"
                + H_BEAR,
                img="gráfico histórico BTC ciclos"
            ),
            corpo(
                "**O que os dados on-chain mostram:**\n\n"
                "Quando grandes wallets acumulam enquanto o varejo vende, "
                "o movimento de preço e o movimento real de Bitcoin vão em "
                "direções opostas.\n\n"
                "Esse padrão precedeu as duas maiores recuperações documentadas.\n\n"
                "Os dados on-chain são o que o preço ainda não refletiu."
            ),
            aviso(
                "Isso não significa que o fundo foi agora. Pode cair mais.\n\n"
                "Ciclos não têm calendário e a história não se repete com as mesmas datas.\n\n"
                "O que se documenta é o **mecanismo** — não o timing.\n\n"
                "Quem age com certeza absoluta em momentos de pânico, "
                "nos dois lados, geralmente paga por isso."
            ),
            corpo(
                "**O que monitorar nas próximas 48-72h:**\n\n"
                "• Saída de BTC das exchanges (acumulação ou fuga de capital?)\n\n"
                "• Open interest em futuros (alavancagem acumulada = risco de cascata)\n\n"
                "• Dominância BTC vs altcoins (rotação de capital ou saída total?)\n\n"
                "Esses três dados dizem mais do que qualquer manchete."
            ),
            mecanismo(
                "**O mecanismo que se repete em todos os ciclos:**\n\n"
                "1 — Evento externo → narrativa negativa dominante\n"
                "2 — Varejo vende com medo. Smart money observa fundamentos.\n"
                "3 — Preço diverge do valor real do ativo.\n"
                "4 — Convergência: rápida quando o consenso finalmente muda.\n\n"
                "**A pergunta que separa quem ganha de quem perde: os fundamentos mudaram?**",
                img="diagrama ciclo pânico/acumulação"
            ),
            final(
                "Salva esse carrossel.\n\n"
                "Não pela análise.\n\n"
                "**Pelo registro de como você estava se sentindo agora.**\n\n"
                "Daqui a 4 anos, quando você olhar pra esse momento, "
                "vai querer lembrar o que escolheu fazer com o medo.\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── CORRENTE_IMPACTO ──────────────────────────────────────────────────────
    elif fmt == "CORRENTE_IMPACTO":
        return [
            capa(
                "Parece distante. Não é.\n\n"
                f"**{title}**\n\n"
                "Deixa eu te mostrar onde isso chega.",
                img="mapa geopolítico dark — linhas de conexão, azul"
            ),
            corpo(
                "**O que a mídia está cobrindo:**\n\n"
                f"Fonte: {source}.\n\n"
                "Esse é o evento. Agora o contexto que está faltando.",
                img="imagem do evento"
            ),
            corpo(
                "**Elo 1 — energia e inflação:**\n\n"
                "Instabilidade em regiões produtoras pressiona o barril.\n\n"
                "Petróleo caro encarece logística, produção, tudo.\n\n"
                "Fed, que estava prestes a cortar juros, hesita.\n\n"
                "**Cortar juros com inflação subindo seria um erro histórico — "
                "e o Fed sabe disso.**",
                img="gráfico petróleo vs CPI"
            ),
            corpo(
                "**Elo 2 — mercados de risco:**\n\n"
                "A alta de 2023-2024 foi alimentada pela expectativa de cortes.\n\n"
                "Quando essa expectativa recua, dinheiro institucional sai.\n\n"
                "Nasdaq corrige. **Bitcoin vai junto** — não pelos fundamentos, "
                "mas porque algoritmos ainda classificam BTC como ativo de risco.\n\n"
                "Correlação Bitcoin/Nasdaq em stress macro: **0.7**.",
                img="gráfico BTC vs Nasdaq correlação"
            ),
            corpo(
                "**Elo 3 — o Brasil:**\n\n"
                + H_BR,
                img="gráfico USD/BRL"
            ),
            aviso(
                "Essa corrente pode se desfazer mais rápido do que se formou.\n\n"
                "Historicamente, quando o mercado percebe que os fundamentos "
                "cripto não mudaram, a recuperação é mais rápida que a queda.\n\n"
                "Isso não é previsão. É o registro de como esse mecanismo "
                "funcionou em 2020 e 2022."
            ),
            mecanismo(
                "**O que mudou nesse ciclo vs. anteriores:**\n\n"
                + H_ETF + "\n\n"
                "Halving de 2024 = redução estrutural de oferta.\n\n"
                "**Contexto macro muda o timing. Fundamentos determinam o piso.**",
                img="timeline ciclos BTC"
            ),
            final(
                "Entender a corrente inteira é o que separa quem reage de quem antecipa.\n\n"
                "**Salva esse carrossel. Vai ser útil quando o próximo evento aparecer.**\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── ANGULO_BRASIL ─────────────────────────────────────────────────────────
    elif fmt == "ANGULO_BRASIL":
        return [
            capa(
                "Ninguém está te contando o que isso significa **em reais**.\n\n"
                f"**{title}**",
                img="mapa Brasil + tela Bloomberg dark, verde/amarelo"
            ),
            corpo(
                "**O número que a análise em inglês usa:**\n\n"
                f"{f'Dado central: **{n1}**.' if n1 else 'O número em dólar.'}\n\n"
                f"Fonte: {source}.\n\n"
                "Esse é o número que todo mundo está lendo. "
                "Mas ele ignora 3 variáveis críticas pra quem está no Brasil.",
                img="print da análise em inglês"
            ),
            corpo(
                "**O número que realmente importa pra você:**\n\n"
                + H_BR,
            ),
            corpo(
                "**As 3 variáveis que a análise em inglês ignora:**\n\n"
                "**1.** Câmbio: você compra em dólar, investe em reais.\n\n"
                "**2.** Selic: com juros a dois dígitos, renda fixa compete "
                "diretamente com cripto pelo mesmo capital.\n\n"
                "**3.** IOF + taxas: aumentam seu custo de entrada em **até 6%** "
                "antes de qualquer movimento do ativo."
            ),
            aviso(
                "Isso não é pessimismo sobre o cripto.\n\n"
                "É a realidade de operar num país de moeda fraca "
                "com ativo dolarizado.\n\n"
                "Ignorar essa equação não faz ela desaparecer.\n\n"
                "Entendê-la é uma **vantagem competitiva real** "
                "frente a quem só lê análise em inglês."
            ),
            mecanismo(
                "**O que os melhores investidores BR fazem diferente:**\n\n"
                "Acompanham o preço do BTC **em reais** — não só em dólar.\n\n"
                "Usam DCA em reais com disciplina — sem tentar acertar câmbio e BTC ao mesmo tempo.\n\n"
                "Mantêm parte em stablecoins dolarizadas para aproveitar "
                "quando real e BTC estão simultaneamente favoráveis.",
            ),
            final(
                "O investidor brasileiro que ignora o contexto cambial "
                "está tomando decisão com metade das informações.\n\n"
                "**Salva esse carrossel. Vai mudar como você lê qualquer análise de cripto.**\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── CONTRAINTUITIVO ───────────────────────────────────────────────────────
    elif fmt == "CONTRAINTUITIVO":
        num_ctx = f"O dado central: **{n1}**. Parece ruim." if n1 else "Parece ruim."
        return [
            capa(
                f"{num_ctx} Os dados dizem o oposto.\n\n**{title}**",
                img="gráfico aparentemente negativo com reversão — dark, amarelo"
            ),
            corpo(
                "**O que todo mundo está dizendo:**\n\n"
                f"Fonte: {source}.\n\n"
                "Esse é o consenso. Agora o contexto que o consenso ignora.",
            ),
            corpo(
                "**O número que a mídia usa vs. o número que importa:**\n\n"
                + H_BEAR,
                img="gráfico histórico BTC"
            ),
            corpo(
                "**Por que o consenso erra nesses momentos:**\n\n"
                "O mercado precifica o que já é consenso — e consenso é sempre atrasado.\n\n"
                "O que está acontecendo agora ainda não está nos preços.\n\n"
                "Quando virar consenso, a oportunidade já terá passado para a maioria."
            ),
            aviso(
                "Dados históricos não são garantia de repetição.\n\n"
                "Pode cair mais. Pode demorar mais. Pode ser diferente dessa vez.\n\n"
                "O que a história documenta é o **mecanismo** — não o calendário.\n\n"
                "Quem age com certeza absoluta em qualquer direção geralmente paga por isso."
            ),
            mecanismo(
                "**O mecanismo do contraintuitivo:**\n\n"
                "1 — Evento negativo → narrativa pessimista dominante.\n"
                "2 — Varejo vende. Quem tem tese observa fundamentos.\n"
                "3 — Se fundamentos intactos → divergência entre preço e valor.\n"
                "4 — Convergência: rápida, quando o consenso finalmente muda.\n\n"
                "**A pergunta que separa as decisões: os fundamentos mudaram ou só o sentimento?**",
                img="diagrama divergência preço/valor"
            ),
            final(
                "Salva esse carrossel.\n\n"
                "Não pela conclusão.\n\n"
                "**Pelo registro de como o mercado estava se sentindo agora.**\n\n"
                "Daqui a alguns anos, vai ser útil ver esse momento de fora.\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── PREVISAO_ACERTADA ─────────────────────────────────────────────────────
    elif fmt == "PREVISAO_ACERTADA":
        num_ctx = f"O dado específico apontado: **{n1}**." if n1 else ""
        return [
            capa(
                "Ele disse isso quando o mercado não queria ouvir. Aconteceu.\n\n"
                f"**{title}**\n\nAgora está dizendo algo novo.",
                img="print da previsão + gráfico confirmando — dark, verde"
            ),
            corpo(
                f"**O contexto:**\n\n{num_ctx}\n\nFonte: {source}.\n\n"
                "Antes de você continuar, deixa eu te contar o histórico.",
                img="print da análise original"
            ),
            corpo(
                "**Por que bom histórico importa:**\n\n"
                "Analistas com track record não são sortudos.\n\n"
                "Eles enxergam conexões que o mercado ainda não precificou.\n\n"
                "A janela entre o insight e o consenso é onde estão "
                "os maiores retornos documentados da história do cripto.",
            ),
            corpo(
                "**O contexto atual:**\n\n"
                + H_ETF,
                img="gráfico fluxo ETFs"
            ),
            aviso(
                "Bom histórico não é garantia de acerto futuro.\n\n"
                "Nenhum analista acerta 100% do tempo.\n\n"
                "O que importa é entender o **raciocínio por trás** — não só a conclusão.\n\n"
                "Seguir cegamente qualquer analista, independente do histórico, "
                "é tão perigoso quanto ignorá-los completamente."
            ),
            mecanismo(
                "**O padrão dos analistas com bom histórico:**\n\n"
                "Ignoram o consenso quando dados apontam outra direção.\n\n"
                "Dão mais peso a dados on-chain do que a sentimento de mercado.\n\n"
                "Fazem previsões impopulares quando o momento exige.\n\n"
                "**Raramente estão certos toda vez. Mas quando estão, a margem é grande.**",
            ),
            final(
                "Você não precisa concordar com tudo que especialistas dizem.\n\n"
                "Mas precisa saber o que estão dizendo.\n\n"
                "**A pergunta certa: qual o raciocínio dele e ele bate com os dados?**\n\n"
                "Salva esse carrossel.\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── COMPARACAO_HISTORICA ──────────────────────────────────────────────────
    elif fmt == "COMPARACAO_HISTORICA":
        return [
            capa(
                "Isso já aconteceu antes. Exatamente assim.\n\n"
                f"**{title}**\n\n"
                "Deixa eu te mostrar o que veio depois.",
                img="gráfico histórico longo prazo BTC — dark, cinza/amarelo"
            ),
            corpo(
                f"**O evento de hoje:**\n\nFonte: {source}.\n\n"
                "Antes de reagir, veja o padrão histórico.",
            ),
            corpo(
                "**Março de 2020 — paralelo 1:**\n\n"
                "COVID. Lockdown global. Pânico total.\n\n"
                "Bitcoin: **−50% em 48 horas**. Narrativa: 'acabou'.\n\n"
                "13 meses depois: **+1.200%** do fundo.\n\n"
                "Quem comprou no pânico multiplicou por 12.",
                img="gráfico BTC março 2020"
            ),
            corpo(
                "**Novembro de 2022 — paralelo 2:**\n\n"
                "Colapso FTX + inflação + guerra.\n\n"
                "Bitcoin a **$15.000**. Narrativa: 'crypto morreu'.\n\n"
                "Retorno para quem comprou entre $15k e $20k: **+300%** hoje.\n\n"
                "**Nos dois casos: fundamentos intactos. Só o sentimento mudou.**",
                img="gráfico BTC novembro 2022"
            ),
            aviso(
                "A história não se repete com as mesmas datas e os mesmos números.\n\n"
                "Pode cair mais. Pode demorar mais. Pode ser diferente dessa vez.\n\n"
                "O que se repete é o **mecanismo**: pânico de varejo, "
                "acumulação silenciosa, recuperação quando o consenso muda.\n\n"
                "Isso não é previsão. É o registro histórico documentado."
            ),
            mecanismo(
                "**O que mudou nesse ciclo vs. 2020 e 2022:**\n\n"
                + H_ETF + "\n\n"
                "Halving de 2024: pressão de oferta estrutural que não existia antes.\n\n"
                "**Contexto macro muda o timing. Fundamentos determinam a direção.**",
                img="comparativo ciclos BTC"
            ),
            final(
                "Salva esse carrossel.\n\n"
                "Não pela análise.\n\n"
                "**Pelo registro de como você estava se sentindo agora.**\n\n"
                "Daqui a 4 anos, quando você olhar pra esse momento, "
                "vai querer ter feito algo com o medo.\n\n"
                "@criptobrasilofc"
            ),
        ]

    # ── EDUCATIVO_CONTEXTO ────────────────────────────────────────────────────
    else:
        num_ctx = f"O dado central: **{n1}**." if n1 else "O contexto que está faltando."
        return [
            capa(
                f"O número que quase ninguém está contextualizando.\n\n**{title}**",
                img="infográfico dark — dado central em destaque, amarelo"
            ),
            corpo(
                f"**O contexto:**\n\n{num_ctx}\n\nFonte: {source}.\n\n"
                "O número da manchete vs. o número que realmente importa.",
            ),
            corpo(
                "**O que a mídia usa vs. o que importa:**\n\n"
                "A mídia usa o número que chama atenção.\n\n"
                "O analista usa o número que explica o que está acontecendo.\n\n"
                "São quase sempre números diferentes — e a diferença muda tudo.",
            ),
            corpo(
                "**O mecanismo por trás:**\n\n"
                "Eventos como esse se movem em camadas:\n\n"
                "**Camada 1:** manchete — reação emocional, rápida e exagerada.\n\n"
                "**Camada 2:** dados on-chain — o que está acontecendo de verdade.\n\n"
                "**Camada 3:** impacto real no preço — vem com atraso de dias ou semanas.\n\n"
                "A maioria reage na camada 1."
            ),
            aviso(
                "Entender o contexto não significa que você sabe o que vai acontecer.\n\n"
                "Significa que você vai errar menos por impulso "
                "e mais por decisão consciente.\n\n"
                "Isso já é uma vantagem enorme frente a quem age só pela manchete."
            ),
            mecanismo(
                "**O que fazer com essa informação:**\n\n"
                + H_ETF + "\n\n"
                "Quando o contexto macro e os fundamentos divergem, "
                "os fundamentos sempre vencem — com atraso.\n\n"
                "**Ruído de curto prazo. Sinal de longo prazo.**",
            ),
            final(
                "Salvas esse carrossel.\n\n"
                "**2 minutos lendo isso vai mudar como você lê "
                "as próximas 100 notícias de cripto.**\n\n"
                "@criptobrasilofc"
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
        # Viral score (injetado pelo server.py, passado adiante)
        "viral_class":    article.get("viral_class", ""),
        "viral_gatilhos": article.get("viral_gatilhos", {}),
        "viral_tier":     article.get("viral_tier", 1.0),
    }
