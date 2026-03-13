"""
CRIPTO BRASIL INTEL — Editorial Engine
========================================
Toda a inteligência de criação de conteúdo em um lugar.

Formats:
  PREVISAO_ACERTADA   → "esse cara acertou X, agora diz Y" (7500 likes)
  CORRENTE_IMPACTO    → geo → macro → cripto → bolso BR
  ANGULO_BRASIL       → localiza notícia global pro contexto BR
  CONTRAINTUITIVO     → take provocativo que vai contra senso comum
  ALERTA_MERCADO      → urgente, financeiro, ação imediata
  EDUCATIVO_CONTEXTO  → explica o que está por baixo do evento
  COMPARACAO_HISTORICA → "isso já aconteceu antes em X, o resultado foi..."
"""

import re
from dataclasses import dataclass, field
from typing import Optional

# ── FORMATOS EDITORIAIS ───────────────────────────────────────────────────────

FORMATS = {

    "PREVISAO_ACERTADA": {
        "desc": "Especialista que acertou previsões anteriores agora diz X",
        "viral_bonus": 18,
        "trigger_kw": [
            "predicted", "forecast", "warned", "analyst says", "expert says",
            "previu", "prevê", "analista diz", "especialista alerta",
            "told us", "was right about", "acertou", "previsão",
        ],
        "hook_template": "Esse {role} fez {n} grandes previsões, acertou — e agora está dizendo {claim}.",
        "structure": ["credencial", "previsoes_anteriores", "previsao_atual", "implicacao_cripto", "cta"],
        "best_for": ["geo", "macro"],
    },

    "CORRENTE_IMPACTO": {
        "desc": "Conecta evento global → impacto em cadeia até o Bitcoin do brasileiro",
        "viral_bonus": 14,
        "trigger_kw": [
            "war", "guerra", "sanction", "tariff", "oil", "fed", "rate",
            "petróleo", "tarifa", "juros", "inflação", "dólar", "crise",
        ],
        "hook_template": "{evento} → {efeito1} → {efeito2} → seu Bitcoin",
        "structure": ["evento", "efeito_macro", "efeito_mercado", "efeito_cripto", "efeito_brasil", "o_que_fazer"],
        "best_for": ["geo", "macro"],
    },

    "ANGULO_BRASIL": {
        "desc": "Pega notícia global e traduz pro impacto específico no investidor BR",
        "viral_bonus": 12,
        "trigger_kw": [
            "global", "world", "international", "dollar", "fed", "oil",
            "mundial", "global", "petróleo", "dólar", "selic",
        ],
        "hook_template": "Enquanto todo mundo fala de {assunto_global}, o que ninguém está te contando é o que isso faz com {impacto_br}.",
        "structure": ["gancho_exclusividade", "contexto_global", "impacto_brasil", "numero_concreto", "cta"],
        "best_for": ["macro", "geo", "br"],
    },

    "CONTRAINTUITIVO": {
        "desc": "Take que vai contra o senso comum — provoca discussão",
        "viral_bonus": 16,
        "trigger_kw": [
            "contrary", "actually", "wrong", "myth", "surprising",
            "contrário", "na verdade", "errado", "mito", "surpreendente",
            "you're wrong", "stop saying", "not what you think",
        ],
        "hook_template": "Todo mundo está {crença_comum}. Eles estão errados — e vou te provar.",
        "structure": ["afirmacao_polarizante", "crenca_popular", "inversao", "prova", "implicacao", "cta"],
        "best_for": ["edu", "bull", "bear"],
    },

    "ALERTA_MERCADO": {
        "desc": "Urgente — evento que exige atenção imediata do investidor",
        "viral_bonus": 15,
        "trigger_kw": [
            "breaking", "urgent", "alert", "crash", "spike", "emergency",
            "urgente", "alerta", "queda", "disparou", "emergência",
            "record", "recorde", "all-time", "historic",
        ],
        "hook_template": "⚠️ {evento} aconteceu agora. Isso afeta diretamente {ativo}.",
        "structure": ["o_que_aconteceu", "numero_concreto", "historico", "impacto_cripto", "o_que_monitorar"],
        "best_for": ["bear", "bull", "macro"],
    },

    "EDUCATIVO_CONTEXTO": {
        "desc": "Aproveita evento para ensinar conceito — evergreen + atual",
        "viral_bonus": 8,
        "trigger_kw": [
            "what is", "why", "how", "explained", "understand",
            "o que é", "por que", "como", "entenda", "explica",
        ],
        "hook_template": "Por que {evento} importa para quem investe em Bitcoin — explicado em {n} pontos.",
        "structure": ["contexto_evento", "conceito_base", "mecanismo", "historico", "implicacao_hoje", "cta"],
        "best_for": ["edu", "br"],
    },

    "COMPARACAO_HISTORICA": {
        "desc": "Conecta evento atual com precedente histórico + resultado",
        "viral_bonus": 13,
        "trigger_kw": [
            "again", "reminds", "similar", "like", "repeat", "history",
            "novamente", "lembra", "parecido", "igual", "repete", "história",
            "2008", "2020", "2022", "covid", "crise", "war",
        ],
        "hook_template": "Isso já aconteceu antes. Em {ano}, {evento_historico}. O resultado foi {resultado}. Hoje...",
        "structure": ["evento_atual", "paralelo_historico", "o_que_aconteceu", "o_que_mudou", "projecao", "cta"],
        "best_for": ["macro", "geo", "edu"],
    },
}

# ── FÓRMULAS DE HOOK POR CATEGORIA ────────────────────────────────────────────

HOOK_FORMULAS = {
    "geo": [
        "O que está acontecendo em {lugar} vai mudar o preço do Bitcoin nas próximas semanas.",
        "Enquanto o mundo discute {conflito}, poucos estão vendo o impacto real nos mercados.",
        "{evento} é a maior ameaça ao mercado global desde {comparacao}.",
        "Esse conflito não é sobre {assunto_aparente}. É sobre {assunto_real}.",
        "Três coisas que vão acontecer com o Bitcoin por causa de {evento}.",
    ],
    "macro": [
        "O Fed fez algo hoje que vai afetar seu Bitcoin por meses.",
        "Petróleo a ${preco} significa {consequencia} pro seu portfólio.",
        "A recessão que ninguém quer falar e o que ela faz com o Bitcoin.",
        "Enquanto a bolsa cai, o Bitcoin {comportamento} — entenda por quê.",
        "O dado econômico de hoje que move todo o mercado cripto.",
    ],
    "bull": [
        "Esse movimento institucional muda o jogo do Bitcoin.",
        "O sinal que apareceu hoje — e que antecedeu os últimos dois bull markets.",
        "Por que {entidade} comprando Bitcoin é diferente dessa vez.",
        "O número que confirmou o que eu estava esperando.",
    ],
    "bear": [
        "Isso que acabou de acontecer é o sinal que eu estava temendo.",
        "Antes de você tomar qualquer decisão hoje, leia isso.",
        "O mercado está errado sobre {assunto} — e vai se arrepender.",
        "Por que eu não estou comprando a queda agora.",
    ],
    "br": [
        "A notícia que vai mudar o cripto no Brasil — e ninguém está falando sobre.",
        "O governo fez algo essa semana que afeta todo brasileiro com cripto.",
        "Por que o dólar a R${valor} é diferente dessa vez pra quem investe em cripto.",
        "Selic + Bitcoin: a relação que todo brasileiro precisa entender.",
    ],
    "edu": [
        "Esse conceito que a maioria dos investidores BR ainda não entendeu.",
        "Por que {conceito} importa mais do que o preço agora.",
        "A diferença entre quem vai ganhar e perder nesse ciclo.",
        "Expliquei isso numa live e todo mundo ficou em silêncio.",
    ],
}

# ── CTA POR INTENÇÃO ──────────────────────────────────────────────────────────

CTAS = {
    "salvar":       "Salva esse post. Você vai querer reler quando {momento_futuro}.",
    "compartilhar": "Manda pra alguém que precisa ver isso antes de tomar qualquer decisão.",
    "comentar":     "Me fala nos comentários: você já viu isso acontecer antes?",
    "seguir":       "Seguindo @criptobrasilofc pra não perder os próximos movimentos.",
    "debater":      "Concorda ou discorda? Me conta abaixo — quero ler sua visão.",
    "urgente":      "Não toma nenhuma decisão de portfólio antes de ler isso até o fim.",
}

# ── MÚSICA POR FORMATO + CATEGORIA ────────────────────────────────────────────

MUSIC_MAP = {
    ("PREVISAO_ACERTADA", "geo"):      "Mysterious tension — Hans Zimmer 'Time' style",
    ("PREVISAO_ACERTADA", "macro"):    "Financial thriller — dark piano",
    ("CORRENTE_IMPACTO", "geo"):       "Breaking news urgency — percussion build",
    ("CORRENTE_IMPACTO", "macro"):     "Wall Street tension — strings + bass",
    ("ALERTA_MERCADO", "bear"):        "Dramatic alarm — Inception-style bass drop",
    ("ALERTA_MERCADO", "bull"):        "Triumphant build — epic orchestral",
    ("ANGULO_BRASIL", "br"):           "Jingle urgente — notícias BR",
    ("EDUCATIVO_CONTEXTO", "edu"):     "Lo-fi focus — analytical calm",
    ("COMPARACAO_HISTORICA", "macro"): "Documentary score — historical gravitas",
    ("CONTRAINTUITIVO", "edu"):        "Suspense reveal — plot twist energy",
    "default":                          "Dark ambient instrumental — neutral tension",
}

# ── DALLE PROMPTS POR CATEGORIA ───────────────────────────────────────────────

DALLE_TEMPLATES = {
    "geo":   "War room map visualization, dark editorial, yellow accent lines, global conflict zones, cinematic --ar 9:16 --style raw",
    "macro": "Financial data terminal, Bloomberg aesthetic, dark background, yellow #FFD600 charts, wall street crisis --ar 9:16",
    "bull":  "Bitcoin rocket chart breaking through resistance, dark cyber background, green #39FF14 laser lines --ar 9:16",
    "bear":  "Bitcoin crashing chart, red data streams, dark terminal, dramatic shadows, data journalism --ar 9:16",
    "br":    "Brazil flag colors meets dark crypto terminal, R$ symbol, Brazilian map outline, editorial --ar 9:16",
    "edu":   "Clean infographic dark mode, yellow accent, data flow diagram, educational tech aesthetic --ar 9:16",
}

# ── ENGINE PRINCIPAL ──────────────────────────────────────────────────────────

def detect_format(article: dict) -> str:
    """Detecta o melhor formato editorial para um artigo."""
    title = article["title"].lower()
    excerpt = article.get("excerpt", "").lower()
    text = title + " " + excerpt
    cls = article.get("_cls", "edu")

    scores = {fmt: 0 for fmt in FORMATS}

    for fmt_name, fmt in FORMATS.items():
        # Keyword match
        for kw in fmt["trigger_kw"]:
            if kw.lower() in text:
                scores[fmt_name] += 2
        # Category preference
        if cls in fmt["best_for"]:
            scores[fmt_name] += 3

    # Desempate: regras contextuais
    if "acertou" in text or "previu" in text or "predicted" in text:
        scores["PREVISAO_ACERTADA"] += 10

    if any(w in text for w in ["war", "guerra", "attack", "ataque", "missile"]):
        scores["CORRENTE_IMPACTO"] += 6
        scores["ALERTA_MERCADO"] += 4

    if "brasil" in text or "brasileiro" in text or "selic" in text or "real" in text:
        scores["ANGULO_BRASIL"] += 8

    if any(w in text for w in ["2008", "2020", "2022", "history", "história", "again"]):
        scores["COMPARACAO_HISTORICA"] += 8

    if any(w in text for w in ["breaking", "urgente", "record", "recorde", "crash"]):
        scores["ALERTA_MERCADO"] += 6

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "EDUCATIVO_CONTEXTO"


def get_music(fmt: str, cls: str) -> str:
    """Retorna a trilha ideal para o formato + categoria."""
    return MUSIC_MAP.get((fmt, cls), MUSIC_MAP.get(("default", ""), MUSIC_MAP["default"]))


def get_dalle(cls: str, title: str) -> str:
    """Gera prompt DALL-E customizado."""
    base = DALLE_TEMPLATES.get(cls, DALLE_TEMPLATES["edu"])
    return f"{title[:60]}, {base}"


def pick_hook(cls: str, article: dict) -> str:
    """Seleciona e personaliza o hook mais forte pra categoria."""
    formulas = HOOK_FORMULAS.get(cls, HOOK_FORMULAS["edu"])
    title = article["title"]
    # Retorna a fórmula mais relevante baseada no título
    for formula in formulas:
        if any(kw in title.lower() for kw in ["war", "guerra", "fed", "crash", "record", "acertou"]):
            return formula
    return formulas[0]


def pick_cta(cls: str, fmt: str) -> str:
    """Escolhe o CTA mais apropriado para classe + formato."""
    if fmt == "ALERTA_MERCADO":
        return CTAS["urgente"]
    if cls in ("geo", "macro"):
        return CTAS["compartilhar"].replace("{}", "")
    if cls == "edu":
        return CTAS["salvar"].replace("{momento_futuro}", "o ciclo virar")
    if cls == "br":
        return CTAS["compartilhar"]
    if cls == "bear":
        return CTAS["urgente"]
    return CTAS["debater"]


def generate_reel_script(article: dict, fmt: str) -> str:
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


def generate_carousel_slides(article: dict, fmt: str) -> list:
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


def generate_post_content(article: dict, fmt: str) -> dict:
    """Gera todo o conteúdo de post para um artigo."""
    cls    = article.get("_cls", "edu")
    title  = article["title"]
    exc    = article.get("excerpt", title)
    source = article.get("source_name", "")

    tags_map = {
        "bull":  "#Bitcoin #Alta #CriptoBR #Bull #Mercado",
        "bear":  "#Bitcoin #Baixa #CriptoBR #Bear #Mercado",
        "edu":   "#Bitcoin #Educação #CriptoBR #Análise",
        "br":    "#CriptoBR #Bitcoin #Brasil #Regulação",
        "macro": "#Macro #Economia #FED #Bitcoin #Mercado #EUA",
        "geo":   "#Geopolítica #Guerra #Bitcoin #Macro #Economia",
    }

    hook = pick_hook(cls, article)
    cta  = pick_cta(cls, fmt)
    tags = tags_map.get(cls, "#Bitcoin #Cripto")
    music = get_music(fmt, cls)
    dalle = get_dalle(cls, title)
    reel  = generate_reel_script(article, fmt)
    slides = generate_carousel_slides(article, fmt)

    return {
        "editorial_format": fmt,
        "editorial_format_desc": FORMATS[fmt]["desc"],
        "hook": hook,
        "tweet": f"{hook}\n\n{title}\n\n🔗 {source}",
        "post_feed": f"{exc[:400]}\n\nFonte: {source}\n\n{cta}",
        "caption": f"{title[:110]}{'…' if len(title)>110 else ''}\n\n{tags}\n\n@defiverso @criptobrasilofc",
        "cta": cta,
        "slides": slides,
        "reel": {
            "dur":    "50-70s",
            "music":  music,
            "cap":    f"{title[:100]}\n\n{tags}\n\n@defiverso @criptobrasilofc",
            "script": reel,
        },
        "dalle":     dalle,
        "dalleVars": [
            f"Alternative: {title[:55]}, dark editorial, cinematic --ar 9:16",
            f"Square version: {title[:55]}, data viz dark mode --ar 1:1",
        ],
    }


def enrich_article(article: dict) -> dict:
    """Enriquece artigo com toda a inteligência editorial."""
    fmt     = detect_format(article)
    content = generate_post_content(article, fmt)
    return {**article, **content}
