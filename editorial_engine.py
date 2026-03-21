"""
Vault Capital — Editorial Engine v15
Gera carrosseis, reels e posts de alta qualidade SEM Claude API.
Baseado nos autorais de sucesso: narrativa, dados históricos, aviso honesto.
"""
import re
import random
from datetime import datetime

# ── DADOS HISTÓRICOS REAIS PARA CONTEXTUALIZAR ───────────────────────────────
HISTORICO = {
    "btc_fundos": [
        {"data": "Março de 2020", "preco": "$3.800", "preco_brl": "R$ 22.000", "contexto": "Pandemia COVID"},
        {"data": "Junho de 2022", "preco": "$15.500", "preco_brl": "R$ 80.000", "contexto": "Colapso Luna + FTX"},
        {"data": "Novembro de 2018", "preco": "$3.200", "preco_brl": "R$ 12.000", "contexto": "Fim do ciclo 2017"},
    ],
    "btc_topos": [
        {"data": "Novembro de 2021", "preco": "$69.000", "preco_brl": "R$ 380.000"},
        {"data": "Outubro de 2025", "preco": "$126.000", "preco_brl": "R$ 655.000"},
        {"data": "Dezembro de 2017", "preco": "$19.800", "preco_brl": "R$ 65.000"},
    ],
    "fear_greed": {
        "extremo_medo": {"fundo_2020": 5, "fundo_2022": 6, "atual": 19},
        "retorno_18m": "+516% médio histórico após atingir abaixo de 10",
    },
    "etf": {
        "lancamento": "Janeiro de 2024",
        "blackrock_aum": "$52 bilhões",
        "total_etfs": "$115 bilhões",
    },
    "halvings": [
        {"ano": 2012, "preco_antes": "$12", "preco_pico": "$1.163", "retorno": "+9.345%"},
        {"ano": 2016, "preco_antes": "$650", "preco_pico": "$19.800", "retorno": "+2.943%"},
        {"ano": 2020, "preco_antes": "$8.821", "preco_pico": "$69.000", "retorno": "+682%"},
        {"ano": 2024, "preco_antes": "$63.800", "status": "em curso"},
    ],
    "brasil": {
        "ipca_10anos": "75%",
        "real_depreciacao": "87% vs dólar desde 2016",
        "volume_cripto": "3º maior mercado cripto da América Latina",
    },
}

# ── FECHAMENTOS PADRÃO ────────────────────────────────────────────────────────
FECHAMENTOS = [
    "Salva esse carrossel. Não pela análise. Pelo registro de como você estava se sentindo agora.",
    "Guarda esse post. Daqui a 12 meses você vai querer lembrar o que estava achando hoje.",
    "Manda pra alguém que precisa ver esse contexto agora. Às vezes é isso que muda uma decisão.",
]

AVISOS_HONESTOS = [
    "Antes de continuar: isso não é conselho de investimento. É análise de dados históricos. O passado não garante o futuro. Nenhum analista sabe quando exatamente o ciclo vai virar.",
    "O aviso que eu preciso dar antes de fechar: dados históricos não são previsão. Essa análise pode estar errada. O mercado pode fazer coisas que nenhum modelo prevê.",
    "Honestidade antes do fechamento: o padrão histórico existe, mas cada ciclo tem variáveis novas. Dimensione sua posição para uma realidade onde você pode estar errado.",
]

# ── UTILS ─────────────────────────────────────────────────────────────────────
def clean(text: str, max_chars: int = 400) -> str:
    """Limpa HTML e trunca texto."""
    text = re.sub(r'<[^>]+>', '', text or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]

def extract_numbers(text: str) -> list:
    """Extrai números e percentuais do texto."""
    patterns = [
        r'\$[\d,\.]+[BMK]?',
        r'R\$[\d,\.]+[BMK]?',
        r'[\d,\.]+%',
        r'[\d,\.]+ bilh[õo]',
        r'[\d,\.]+ milh[õo]',
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, re.IGNORECASE))
    return found[:5]

def get_categoria_label(cls: str, br: bool) -> str:
    labels = {
        "bull": "Alta", "bear": "Baixa", "edu": "Educativo",
        "br": "Brasil 🇧🇷", "macro": "Macro", "geo": "Geopolítica",
        "cri": "Cripto", "trd": "Trade",
    }
    if br: return "Brasil 🇧🇷"
    return labels.get(cls, "Cripto")

# ── GERADOR DE CARROSSEL ──────────────────────────────────────────────────────
def generate_carousel_slides(article: dict, fmt: str) -> list:
    title   = clean(article.get("title", ""), 200)
    desc    = clean(article.get("desc", "") or article.get("excerpt", ""), 500)
    source  = article.get("name", "") or article.get("source_name", "")
    cls     = article.get("cls", "edu")
    br      = article.get("br", False)
    nums    = extract_numbers(title + " " + desc)
    cat_label = get_categoria_label(cls, br)
    fundo   = random.choice(HISTORICO["btc_fundos"])
    topo    = random.choice(HISTORICO["btc_topos"])
    halving = HISTORICO["halvings"][2]  # 2020

    # ── CAPA ─────────────────────────────────────────────────────────────────
    # Lógica: gera uma contradição ou dado absurdo baseado na notícia
    if cls == "bear":
        capa_txt = (
            f"**{title}**\n\n"
            f"Isso parece catastrófico. Mas você sabe o que aconteceu as 3 últimas vezes que o mercado pareceu assim?\n\n"
            f"Os dados vão surpreender você. 👇"
        )
    elif cls == "bull":
        capa_txt = (
            f"**{title}**\n\n"
            f"Esse movimento não saiu do nada. Tem um padrão histórico por trás disso que a maioria não está vendo.\n\n"
            f"Vou te mostrar o contexto completo. 👇"
        )
    elif br:
        capa_txt = (
            f"**{title}**\n\n"
            f"Isso muda diretamente o que o investidor brasileiro precisa saber agora.\n\n"
            f"Contexto completo em {7 if len(desc) > 200 else 5} slides. 👇"
        )
    elif fmt == "CONTRAINTUITIVO":
        capa_txt = (
            f"A maioria vai ler essa notícia e tirar a conclusão errada.\n\n"
            f"**{title}**\n\n"
            f"O ângulo que ninguém está mostrando. 👇"
        )
    else:
        capa_txt = (
            f"**{title}**\n\n"
            f"Tem um detalhe nessa notícia que muda completamente como você deve interpretar o mercado agora.\n\n"
            f"Contexto histórico completo. 👇"
        )

    slides = [{"role": "capa", "t": capa_txt}]

    # ── SLIDE 2: CONTEXTO ─────────────────────────────────────────────────────
    contexto_txt = f"**O que aconteceu:**\n\n{desc}\n\nFonte: {source}.\n\n👇👇"
    if len(desc) < 50:
        contexto_txt = (
            f"**O que está acontecendo:**\n\n"
            f"Bitcoin está no centro de uma mudança de narrativa que o mercado ainda não precificou completamente.\n\n"
            f"Em {fundo['data']}, o Bitcoin estava a {fundo['preco']} com o mundo em pânico por causa de {fundo['contexto']}. "
            f"O que veio depois foi a maior alta do ciclo.\n\n"
            f"👇👇"
        )
    slides.append({"role": "corpo", "t": contexto_txt})

    # ── SLIDE 3: DADO HISTÓRICO ───────────────────────────────────────────────
    historico_txt = (
        f"**O padrão histórico que conecta isso:**\n\n"
        f"Nos 3 halvings anteriores do Bitcoin:\n\n"
        f"**{HISTORICO['halvings'][0]['ano']}:** Saiu de {HISTORICO['halvings'][0]['preco_antes']} para {HISTORICO['halvings'][0]['preco_pico']} — {HISTORICO['halvings'][0]['retorno']}\n\n"
        f"**{HISTORICO['halvings'][1]['ano']}:** Saiu de {HISTORICO['halvings'][1]['preco_antes']} para {HISTORICO['halvings'][1]['preco_pico']} — {HISTORICO['halvings'][1]['retorno']}\n\n"
        f"**{HISTORICO['halvings'][2]['ano']}:** Saiu de {HISTORICO['halvings'][2]['preco_antes']} para {HISTORICO['halvings'][2]['preco_pico']} — {HISTORICO['halvings'][2]['retorno']}\n\n"
        f"O 4º halving foi em Abril de 2024. O ciclo ainda está em andamento.\n\n"
        f"👇👇"
    )
    slides.append({"role": "corpo", "t": historico_txt})

    # ── SLIDE 4: ANÁLISE ──────────────────────────────────────────────────────
    if cls == "bear":
        analise_txt = (
            f"**Por que o bear market atual é diferente dos anteriores:**\n\n"
            f"Em 2022, o colapso foi causado por fraude real — Luna, FTX, Celsius. "
            f"Estrutura destruída de dentro.\n\n"
            f"A queda atual não tem nenhum desses elementos. "
            f"É realização de lucro de atores legítimos + correlação com macro.\n\n"
            f"O Bear de 2022 destruiu confiança. O atual está testando paciência.\n\n"
            f"São coisas completamente diferentes.\n\n"
            f"👇👇"
        )
    elif cls == "bull":
        analise_txt = (
            f"**O que está mudando estruturalmente:**\n\n"
            f"Pela primeira vez na história, ETFs institucionais acumularam mais de {HISTORICO['etf']['blackrock_aum']} em Bitcoin "
            f"(só BlackRock). Total de todos os ETFs: {HISTORICO['etf']['total_etfs']}.\n\n"
            f"Isso não existia em nenhum ciclo anterior. "
            f"A base de compradores mudou — e isso muda o piso estrutural do mercado.\n\n"
            f"👇👇"
        )
    elif br:
        analise_txt = (
            f"**Por que o investidor brasileiro precisa ver isso de um ângulo diferente:**\n\n"
            f"Desde 2016, o real perdeu {HISTORICO['brasil']['real_depreciacao']} frente ao dólar. "
            f"A inflação acumulada no período foi de {HISTORICO['brasil']['ipca_10anos']}.\n\n"
            f"Quem ficou em reais perdeu poder de compra de duas formas simultâneas. "
            f"Quem tinha Bitcoin capturou tanto a valorização do ativo quanto a proteção cambial.\n\n"
            f"👇👇"
        )
    else:
        analise_txt = (
            f"**O que isso muda para o investidor:**\n\n"
            f"O mercado de cripto está passando por uma transformação que não aparece nos gráficos de curto prazo.\n\n"
            f"Institucionalização, ETFs com {HISTORICO['etf']['total_etfs']} em AUM, reserva estratégica americana de Bitcoin — "
            f"são variáveis que nenhum ciclo anterior tinha.\n\n"
            f"A análise técnica de 2022 não se aplica diretamente ao contexto atual.\n\n"
            f"👇👇"
        )
    slides.append({"role": "corpo", "t": analise_txt})

    # ── SLIDE 5: DETALHE/DADO ESPECÍFICO ─────────────────────────────────────
    detalhe_txt = (
        f"**O dado que a maioria está ignorando:**\n\n"
        f"O Fear & Greed Index ficou abaixo de 10 apenas 3 vezes na história do Bitcoin:\n\n"
        f"**{HISTORICO['btc_fundos'][0]['data']}:** {HISTORICO['btc_fundos'][0]['preco']} — {HISTORICO['btc_fundos'][0]['contexto']}\n\n"
        f"**{HISTORICO['btc_fundos'][1]['data']}:** {HISTORICO['btc_fundos'][1]['preco']} — {HISTORICO['btc_fundos'][1]['contexto']}\n\n"
        f"**{HISTORICO['btc_fundos'][2]['data']}:** {HISTORICO['btc_fundos'][2]['preco']} — {HISTORICO['btc_fundos'][2]['contexto']}\n\n"
        f"Retorno médio 18 meses depois: {HISTORICO['fear_greed']['retorno_18m']}.\n\n"
        f"Não é previsão. É o registro histórico do que já aconteceu.\n\n"
        f"👇👇"
    )
    slides.append({"role": "corpo", "t": detalhe_txt})

    # ── SLIDE 6: AVISO HONESTO ────────────────────────────────────────────────
    aviso_txt = (
        f"⚠️ **O AVISO HONESTO**\n\n"
        f"{random.choice(AVISOS_HONESTOS)}\n\n"
        f"Em 2022, o Fear & Greed ficou em medo extremo por 3 meses seguidos. "
        f"Quem tentou acertar o dia exato do fundo perdeu a janela. "
        f"Quem comprou sistematicamente durante o período ficou com o melhor custo médio.\n\n"
        f"DCA não é sobre acertar o fundo. É sobre não precisar acertar.\n\n"
        f"👇👇"
    )
    slides.append({"role": "aviso", "t": aviso_txt})

    # ── SLIDE 7: MECANISMO ────────────────────────────────────────────────────
    mecanismo_txt = (
        f"**Como isso funciona na prática:**\n\n"
        f"Bear market não é o fim da tese. É onde a posição do próximo ciclo é construída.\n\n"
        f"Quem fez DCA durante o bear de 2022 — comprando de {HISTORICO['btc_fundos'][1]['preco_brl']} por Bitcoin — "
        f"viu o ativo chegar a {HISTORICO['btc_topos'][1]['preco_brl']} no topo do ciclo seguinte.\n\n"
        f"Isso não é promessa de repetição. É o padrão documentado em 3 ciclos consecutivos.\n\n"
        f"A pergunta não é se o mercado vai se recuperar. É em qual preço você vai estar posicionado quando isso acontecer."
    )
    slides.append({"role": "corpo", "t": mecanismo_txt})

    # ── SLIDE 8: FECHAMENTO ───────────────────────────────────────────────────
    slides.append({
        "role": "final",
        "t": random.choice(FECHAMENTOS) + f"\n\n@vaultcapitaloficial"
    })

    return slides


# ── GERADOR DE REEL ───────────────────────────────────────────────────────────
def generate_reel_script(article: dict, fmt: str) -> str:
    title   = clean(article.get("title", ""), 150)
    desc    = clean(article.get("desc", "") or article.get("excerpt", ""), 300)
    source  = article.get("name", "") or ""
    cls     = article.get("cls", "edu")
    br      = article.get("br", False)
    fundo   = random.choice(HISTORICO["btc_fundos"])
    topo    = HISTORICO["btc_topos"][1]
    halving = HISTORICO["halvings"]

    if cls == "bear":
        abertura = f"Vou te contar o que os dados dizem que a maioria das pessoas não consegue ver quando o mercado está caindo."
        dev_1    = f"Em {fundo['data']}, o Bitcoin estava a {fundo['preco']} — {fundo['contexto']} tinha acabado de chegar. Todo mundo achava que ia a zero."
        dev_2    = f"Dezoito meses depois, quem comprou naquele momento de pânico máximo tinha multiplicado o capital por mais de quatro vezes."
        dev_3    = f"O mesmo padrão apareceu em {HISTORICO['btc_fundos'][1]['data']}: {HISTORICO['btc_fundos'][1]['preco']}, contexto de destruição total de confiança. O que veio depois foi {topo['preco']} em {topo['data']}."
        aviso    = f"Agora o aviso que eu preciso te dar porque seria desonesto não dar: isso não significa que vai repetir agora. Pode cair mais. O timing é incerto. O que não é incerto é o padrão histórico de três de três."
        fecha    = f"Salva esse vídeo. Não pela previsão. Pelo lembrete do que os dados dizem quando você estiver com medo demais pra pesquisar."

    elif cls == "bull":
        abertura = f"Tem um movimento acontecendo no mercado que a maioria das pessoas não está contextualizando direito."
        dev_1    = f"Notícia de hoje: {title}. Fonte: {source}."
        dev_2    = f"O que conecta isso ao histórico: nos últimos {len(halving)-1} halvings do Bitcoin, o preço atingiu um novo máximo histórico entre doze e dezoito meses depois de cada evento."
        dev_3    = f"O quarto halving aconteceu em Abril de 2024. O ETF da BlackRock já tem {HISTORICO['etf']['blackrock_aum']} em Bitcoin — uma variável que não existia em nenhum ciclo anterior."
        aviso    = f"O aviso honesto: cada ciclo tem variáveis novas que os modelos históricos não capturam. Dimensione sua posição para o cenário onde você pode estar errado."
        fecha    = f"Salva esse vídeo. Não pela análise. Pelo registro de como o mercado estava se comportando agora."

    elif br:
        abertura = f"Uma notícia que saiu hoje muda como o investidor brasileiro deve pensar sobre cripto agora. Deixa eu contextualizar."
        dev_1    = f"{title}. Isso vem de {source}."
        dev_2    = f"Para entender o impacto: desde 2016, o real perdeu {HISTORICO['brasil']['real_depreciacao']} frente ao dólar. A inflação acumulada foi de {HISTORICO['brasil']['ipca_10anos']}."
        dev_3    = f"Quem tinha Bitcoin capturou tanto a valorização do ativo quanto a proteção cambial. Não porque era sortudo — porque entendeu o contexto macroeconômico brasileiro."
        aviso    = f"O aviso: isso não significa que você deve investir tudo em cripto. Significa que ignorar completamente o contexto é tão arriscado quanto investir demais."
        fecha    = f"Manda esse vídeo pra alguém que acha que cripto é só especulação. O contexto macro BR muda completamente essa conversa."

    elif fmt in ("PREVISAO_ACERTADA", "CONTRAINTUITIVO"):
        abertura = f"Tem um take sobre essa notícia que quase ninguém está fazendo. E eu acho que é o mais importante."
        dev_1    = f"O que aconteceu: {title}. Fonte: {source}."
        dev_2    = f"O take contraintuitivo: o mercado está precificando isso como negativo. Mas olha o que aconteceu nas três últimas vezes que o sentimento ficou nesse nível."
        dev_3    = f"Em {HISTORICO['btc_fundos'][0]['data']}: {HISTORICO['btc_fundos'][0]['preco']}. Em {HISTORICO['btc_fundos'][1]['data']}: {HISTORICO['btc_fundos'][1]['preco']}. Retorno médio dezoito meses depois: mais de quinhentos por cento."
        aviso    = f"O aviso que eu preciso dar: esses dados não são garantia. São o registro histórico. O futuro pode ser diferente. Mas ignorar o padrão também é uma decisão."
        fecha    = f"Salva esse vídeo. Quando o ciclo virar, você vai querer lembrar o que estava achando hoje."

    else:
        abertura = f"Vou te dar o contexto que falta na cobertura dessa notícia."
        dev_1    = f"O que saiu: {title}. Fonte: {source}."
        dev_2    = f"O que isso conecta historicamente: o Bitcoin passou por quatro ciclos completos desde 2012. Em cada um, o ativo que parecia morto num momento específico foi o que mais valorizou nos dezoito meses seguintes."
        dev_3    = f"Os números: halving de {halving[0]['ano']} gerou {halving[0]['retorno']}. Halving de {halving[1]['ano']} gerou {halving[1]['retorno']}. Halving de {halving[2]['ano']} gerou {halving[2]['retorno']}. O padrão existe."
        aviso    = f"Antes de fechar: dados históricos não são garantia de futuro. Cada ciclo tem variáveis novas. Dimensione sempre para o cenário onde você pode estar errado."
        fecha    = f"Salva esse vídeo. Não pela informação. Pelo lembrete de como estava o mercado hoje."

    script = f"{abertura}\n\n{dev_1}\n\n{dev_2}\n\n{dev_3}\n\n{aviso}\n\n{fecha}"
    return script


# ── GERADOR DE POST ───────────────────────────────────────────────────────────
def generate_post_content(article: dict, fmt: str) -> dict:
    title   = clean(article.get("title", ""), 150)
    desc    = clean(article.get("desc", "") or article.get("excerpt", ""), 300)
    source  = article.get("name", "") or ""
    cls     = article.get("cls", "edu")
    br      = article.get("br", False)

    tags_map = {
        "bull":  "#Bitcoin #Alta #CriptoBR #Bull #Mercado #VaultCapital",
        "bear":  "#Bitcoin #Baixa #CriptoBR #Bear #Contexto #VaultCapital",
        "edu":   "#Bitcoin #Educação #CriptoBR #Análise #VaultCapital",
        "br":    "#Bitcoin #Brasil #CriptoBR #Regulação #VaultCapital",
        "macro": "#Bitcoin #Macro #Federal #Juros #CriptoBR #VaultCapital",
        "geo":   "#Bitcoin #Geopolítica #CriptoBR #Global #VaultCapital",
    }
    cls_key = "br" if br else cls
    tags = tags_map.get(cls_key, "#Bitcoin #CriptoBR #VaultCapital")

    fundo = random.choice(HISTORICO["btc_fundos"])

    hook = f"{title}\n\nContexto que falta na maioria das análises:"
    if cls == "bear":
        hook = f"Parece ruim. Os dados dizem algo diferente.\n\n{title}"
    elif cls == "bull":
        hook = f"Não é coincidência. É padrão.\n\n{title}"
    elif br:
        hook = f"O investidor brasileiro precisa ver isso.\n\n{title}"

    post = (
        f"{desc}\n\n"
        f"O que o histórico mostra: em {fundo['data']}, com Bitcoin a {fundo['preco']}, "
        f"o cenário parecia exatamente assim. "
        f"Quem comprou naquele momento de pânico máximo multiplicou o capital nos 18 meses seguintes.\n\n"
        f"Não é promessa de repetição. É o padrão documentado.\n\n"
        f"Fonte: {source}."
    )

    cta_opts = [
        "Salva esse post. Vai ser útil quando o ciclo virar.",
        "Manda pra alguém que precisa ver esse contexto hoje.",
        "Comenta o que você acha — discordar também é válido.",
    ]
    cta = random.choice(cta_opts)
    caption = f"{hook}\n\n{cta}\n\n{tags}"

    return {
        "hook":    hook,
        "post":    post,
        "cta":     cta,
        "caption": caption,
        "tags":    tags,
    }


# ── DETECT FORMAT ─────────────────────────────────────────────────────────────
def detect_format(article: dict) -> str:
    text = (article.get("title","") + " " + article.get("desc","")).lower()

    if any(w in text for w in ["acertou","previu","estava certo","previsão confirmada","predicted"]):
        return "PREVISAO_ACERTADA"
    if article.get("br") or any(w in text for w in ["brasil","real","selic","bacen","receita"]):
        return "ANGULO_BRASIL"
    if any(w in text for w in ["geopolítica","guerra","sanção","embargo","conflito"]):
        return "CORRENTE_IMPACTO"
    if any(w in text for w in ["mas","apesar","mesmo assim","embora","porém","however"]):
        return "CONTRAINTUITIVO"
    if any(w in text for w in ["urgente","alerta","breaking","hoje","agora"]):
        return "ALERTA_MERCADO"
    if any(w in text for w in ["história","ciclo","halving","padrão","2020","2021","2022"]):
        return "COMPARACAO_HISTORICA"

    return "EDUCATIVO_CONTEXTO"


# ── MUSIC SUGGESTIONS ─────────────────────────────────────────────────────────
def get_music(cls: str, fmt: str) -> str:
    music_map = {
        "bear":  "Dramatic tension build — Hans Zimmer 'Time'",
        "bull":  "Epic rising — orchestral building momentum",
        "edu":   "Lo-fi analytical — calm focused beat",
        "br":    "Brazilian bass — serious accessible tone",
        "macro": "Corporate institutional — dark professional",
        "geo":   "Geopolitical tension — cinematic Hans Zimmer style",
    }
    return music_map.get(cls, "Minimal dark electronic — data visualization")


# ── DALLE PROMPT ──────────────────────────────────────────────────────────────
def get_dalle(article: dict, fmt: str) -> str:
    cls  = article.get("cls","edu")
    br   = article.get("br", False)
    base = "Dark editorial financial visualization, yellow accent #FFBA08, dark background #0F1117"

    prompts = {
        "bear":  f"Bitcoin price chart showing decline with historical recovery arrows, {base} --ar 9:16",
        "bull":  f"Bitcoin price chart breaking upward with institutional buyers, {base} --ar 9:16",
        "edu":   f"Data visualization showing Bitcoin historical cycles with dates, {base} --ar 9:16",
        "br":    f"Brazilian flag with Bitcoin symbol, financial data overlay in Portuguese, {base} --ar 9:16",
        "macro": f"Federal Reserve building with Bitcoin chart correlation, {base} --ar 9:16",
        "geo":   f"World map with Bitcoin adoption heatmap, geopolitical context, {base} --ar 9:16",
    }
    return prompts.get("br" if br else cls, f"Bitcoin editorial dark visualization, {base} --ar 9:16")


# ── ENRICH ARTICLE (ponto de entrada principal) ───────────────────────────────
def enrich_article(article: dict) -> dict:
    fmt = detect_format(article)

    slides  = generate_carousel_slides(article, fmt)
    script  = generate_reel_script(article, fmt)
    post    = generate_post_content(article, fmt)
    music   = get_music(article.get("cls","edu"), fmt)
    dalle   = get_dalle(article, fmt)

    article["fmt"]              = fmt
    article["slides"]           = slides
    article["reel"]             = {"script": script, "dur": "35s", "music": music, "cap": post["caption"]}
    article["hook"]             = post["hook"]
    article["post_feed"]        = post["post"]
    article["cta"]              = post["cta"]
    article["caption"]          = post["caption"]
    article["dalle"]            = dalle
    article["dalleVars"]        = [dalle.replace("9:16","1:1"), dalle.replace("9:16","4:5")]

    return article
