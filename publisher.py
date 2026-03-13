"""
CRIPTO BRASIL INTEL — Publisher Autônomo
=========================================
Agendador + publicador que roda independente do dashboard.

Fluxo:
  1. Scraper busca notícias (via server.py)
  2. Publisher seleciona as melhores pelo horário + categoria
  3. Gera conteúdo completo via editorial_engine.py
  4. Coloca na fila com horário ideal
  5. Publica via Instagram Graph API (ou exporta para aprovação manual)

Modos:
  - AUTO_APPROVE=True  → publica automaticamente sem intervenção
  - AUTO_APPROVE=False → gera conteúdo + aguarda aprovação no dashboard

Rodar:
  python publisher.py          → modo daemon (roda sempre)
  python publisher.py --once   → roda uma vez e sai
  python publisher.py --status → mostra fila atual
"""

import asyncio
import json
import os
import sys
import argparse
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

# Pega do ambiente ou preenche aqui
INSTAGRAM_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID      = os.getenv("IG_USER_ID", "")
BACKEND_URL            = os.getenv("BACKEND_URL", "http://localhost:8000")
AUTO_APPROVE           = os.getenv("AUTO_APPROVE", "false").lower() == "true"

# Arquivo de estado da fila (persiste entre reinicializações)
QUEUE_FILE = Path("publisher_queue.json")
PUBLISHED_FILE = Path("published_history.json")

# ── HORÁRIOS IDEAIS POR DIA/CATEGORIA ─────────────────────────────────────────
# Baseado em performance típica de conteúdo cripto/financeiro no Instagram BR
# (horários em BRT = UTC-3)

SCHEDULE = {
    # Dia da semana (0=segunda, 6=domingo): [(hora, minuto, categorias_preferidas)]
    0: [(8,0,["geo","macro"]), (12,30,["bull","bear"]), (18,0,["geo","macro","edu"]), (21,0,["bull","bear","br"])],
    1: [(8,0,["macro","geo"]), (12,0,["bull","bear"]), (17,30,["edu","br"]),          (20,30,["geo","macro"])],
    2: [(8,30,["geo","macro"]),(11,30,["bull","bear"]),(17,0,["edu","br"]),            (20,0,["bear","bull"])],
    3: [(8,0,["geo","macro"]), (12,0,["bull","bear"]), (17,30,["macro","edu"]),        (21,0,["geo","br"])],
    4: [(8,0,["macro","geo"]), (12,30,["bear","bull"]),(17,0,["edu","br"]),            (20,30,["geo","macro"])],
    5: [(9,0,["geo","macro"]), (13,0,["bull","bear"]), (17,30,["edu","br"]),           (22,0,["bull","macro"])],
    6: [(10,0,["geo","edu"]),  (14,0,["bull","bear"]), (17,0,["macro","br"]),          (21,0,["edu","geo"])],
}

# Quantos posts por dia no máximo
MAX_POSTS_PER_DAY = 4

# Intervalo mínimo entre posts (horas)
MIN_INTERVAL_HOURS = 3

# ── ESTADO DA FILA ────────────────────────────────────────────────────────────

def load_queue() -> list:
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text())
        except:
            return []
    return []

def save_queue(queue: list):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, default=str))

def load_history() -> list:
    if PUBLISHED_FILE.exists():
        try:
            return json.loads(PUBLISHED_FILE.read_text())
        except:
            return []
    return []

def save_history(history: list):
    PUBLISHED_FILE.write_text(json.dumps(history[-500:], indent=2, default=str))  # max 500

def article_hash(article: dict) -> str:
    key = article.get("title","")[:60]
    return hashlib.md5(key.encode()).hexdigest()[:12]

# ── SELEÇÃO DE CONTEÚDO ───────────────────────────────────────────────────────

def pick_best_for_slot(articles: list, preferred_cats: list, published_hashes: set) -> dict | None:
    """Escolhe o melhor artigo para um slot de horário."""
    # Filtra já publicados
    available = [a for a in articles if article_hash(a) not in published_hashes]
    if not available:
        return None

    # Prioriza categorias preferidas do slot
    preferred = [a for a in available if a.get("cls","") in preferred_cats]
    pool = preferred if preferred else available

    # Ordena por viral score
    pool.sort(key=lambda x: x.get("viral", 0), reverse=True)
    return pool[0] if pool else None


def get_next_slots(n: int = 4) -> list:
    """Retorna os próximos N slots de publicação."""
    now = datetime.now(timezone.utc) - timedelta(hours=3)  # BRT
    slots = []
    day = now.weekday()
    today_slots = SCHEDULE[day]

    for h, m, cats in today_slots:
        slot_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if slot_time > now and len(slots) < n:
            slots.append((slot_time, cats))

    # Adiciona slots de amanhã se necessário
    tomorrow = (day + 1) % 7
    for h, m, cats in SCHEDULE[tomorrow]:
        if len(slots) >= n:
            break
        slot_time = (now + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
        slots.append((slot_time, cats))

    return slots


# ── INSTAGRAM API ─────────────────────────────────────────────────────────────

async def create_instagram_container(client: httpx.AsyncClient, caption: str, image_url: str) -> str | None:
    """Cria container de mídia no Instagram (passo 1 de 2)."""
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
        return None
    try:
        r = await client.post(
            f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media",
            params={
                "image_url":    image_url,
                "caption":      caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15.0,
        )
        data = r.json()
        return data.get("id")
    except Exception as e:
        print(f"  ❌ Instagram container error: {e}")
        return None

async def publish_instagram_container(client: httpx.AsyncClient, container_id: str) -> bool:
    """Publica container criado (passo 2 de 2)."""
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_USER_ID:
        return False
    try:
        r = await client.post(
            f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish",
            params={
                "creation_id":  container_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15.0,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"  ❌ Instagram publish error: {e}")
        return False

async def try_publish(client: httpx.AsyncClient, item: dict) -> bool:
    """
    Tenta publicar no Instagram.
    Se não tiver token configurado, salva como 'pronto para aprovar'.
    """
    caption = item.get("cap", item.get("title", ""))

    if not INSTAGRAM_ACCESS_TOKEN:
        # Sem API configurada — marca como pronto pra aprovação manual
        item["status"] = "READY_TO_APPROVE"
        item["approval_note"] = "IG_ACCESS_TOKEN não configurado. Configure e republique."
        return False

    # Precisaria de URL de imagem gerada (DALL-E ou imagem existente)
    # Por ora, exporta o conteúdo como pronto
    image_url = item.get("image_url", "")
    if not image_url:
        item["status"] = "MISSING_IMAGE"
        item["approval_note"] = "Falta URL de imagem. Gere via DALL-E e adicione."
        return False

    container_id = await create_instagram_container(client, caption, image_url)
    if not container_id:
        return False

    # Aguarda 10s (Instagram precisa processar)
    await asyncio.sleep(10)

    success = await publish_instagram_container(client, container_id)
    if success:
        item["status"] = "PUBLISHED"
        item["published_at"] = datetime.now(timezone.utc).isoformat()
        print(f"  ✅ Publicado: {item['title'][:60]}")
    return success


# ── BUSCA NOTÍCIAS ────────────────────────────────────────────────────────────

async def fetch_news(client: httpx.AsyncClient) -> list:
    """Busca notícias do backend."""
    try:
        r = await client.get(
            f"{BACKEND_URL}/api/news?limit=20&cripto=8&macro=5&geo=3",
            timeout=20.0,
        )
        if r.status_code == 200:
            return r.json().get("news", [])
    except Exception as e:
        print(f"  ⚠ Não conseguiu buscar notícias: {e}")
    return []


# ── GERA FILA ─────────────────────────────────────────────────────────────────

async def build_queue():
    """
    Busca notícias, seleciona as melhores para os próximos slots
    e constrói a fila de publicação.
    """
    print("\n📡 Publisher — construindo fila...")

    async with httpx.AsyncClient() as client:
        articles = await fetch_news(client)

    if not articles:
        print("  ⚠ Nenhuma notícia disponível")
        return

    history  = load_history()
    pub_hashes = {h["hash"] for h in history}
    queue    = load_queue()
    queued_hashes = {item["hash"] for item in queue}
    used_hashes = pub_hashes | queued_hashes

    slots = get_next_slots(MAX_POSTS_PER_DAY)
    added = 0

    for slot_time, preferred_cats in slots:
        # Verifica se já tem algo agendado nesse slot
        slot_str = slot_time.strftime("%Y-%m-%d %H:%M")
        already_scheduled = any(item.get("scheduled_for","")[:16] == slot_str for item in queue)
        if already_scheduled:
            continue

        best = pick_best_for_slot(articles, preferred_cats, used_hashes)
        if not best:
            continue

        h = article_hash(best)
        queue_item = {
            "hash":           h,
            "title":          best["title"],
            "cls":            best.get("cls","edu"),
            "viral":          best.get("viral",0),
            "source":         best.get("srcN",""),
            "source_url":     best.get("srcUrl",""),
            "editorial_fmt":  best.get("editorial_format","EDUCATIVO_CONTEXTO"),
            "editorial_desc": best.get("editorial_format_desc",""),
            "hook":           best.get("hook",""),
            "cap":            best.get("cap",""),
            "reel_script":    best.get("reel",{}).get("script",""),
            "reel_music":     best.get("reel",{}).get("music",""),
            "slides":         best.get("slides",[]),
            "dalle":          best.get("dalle",""),
            "tweet":          best.get("tweet",""),
            "post_feed":      best.get("post_feed",""),
            "cta":            best.get("cta",""),
            "scheduled_for":  slot_time.isoformat(),
            "scheduled_brt":  (slot_time).strftime("%d/%m %H:%M BRT"),
            "status":         "SCHEDULED",
            "created_at":     datetime.now(timezone.utc).isoformat(),
            "auto_approve":   AUTO_APPROVE,
        }

        queue.append(queue_item)
        used_hashes.add(h)
        added += 1
        print(f"  📅 {queue_item['scheduled_brt']} | [{best.get('cls','?').upper():5}] | {best['title'][:55]}")

    save_queue(queue)
    print(f"  ✅ {added} itens adicionados à fila. Total: {len(queue)} agendados.\n")


# ── PROCESSA FILA ─────────────────────────────────────────────────────────────

async def process_queue():
    """Verifica fila e publica itens no horário."""
    queue   = load_queue()
    history = load_history()
    now     = datetime.now(timezone.utc)

    due = [
        item for item in queue
        if item["status"] == "SCHEDULED"
        and datetime.fromisoformat(item["scheduled_for"]) <= now
    ]

    if not due:
        return

    print(f"\n⏰ {len(due)} item(ns) no horário para publicar...")

    async with httpx.AsyncClient() as client:
        for item in due:
            if AUTO_APPROVE:
                success = await try_publish(client, item)
            else:
                # Modo manual: apenas marca como pronto para aprovação
                item["status"] = "READY_TO_APPROVE"
                success = False
                print(f"  ✋ Aguardando aprovação: {item['title'][:55]}")

            history.append({
                "hash":        item["hash"],
                "title":       item["title"],
                "status":      item["status"],
                "cls":         item["cls"],
                "scheduled":   item["scheduled_for"],
                "processed_at": now.isoformat(),
            })

    # Remove publicados e aprovados da fila ativa
    queue = [
        item for item in queue
        if item["status"] not in ("PUBLISHED",)
    ]

    save_queue(queue)
    save_history(history)


# ── STATUS ────────────────────────────────────────────────────────────────────

def print_status():
    """Imprime status atual da fila."""
    queue   = load_queue()
    history = load_history()

    print("\n═══════════════════════════════════════")
    print("  CRIPTO BRASIL INTEL — FILA DE POSTS")
    print("═══════════════════════════════════════")

    if not queue:
        print("  Fila vazia. Rode sem --status pra construir.")
    else:
        print(f"\n  📋 AGENDADOS ({len([q for q in queue if q['status']=='SCHEDULED'])}):")
        for item in sorted(queue, key=lambda x: x.get("scheduled_for","")):
            status_icon = {"SCHEDULED":"📅","READY_TO_APPROVE":"✋","MISSING_IMAGE":"🖼","PUBLISHED":"✅"}.get(item["status"],"❓")
            print(f"    {status_icon} {item.get('scheduled_brt','?')} | [{item['cls'].upper():5}] | {item['title'][:50]}")
            print(f"       Formato: {item.get('editorial_fmt','?')} | Score: {item.get('viral',0)}")

    recent = history[-5:] if history else []
    if recent:
        print(f"\n  📚 ÚLTIMOS PUBLICADOS:")
        for h in reversed(recent):
            print(f"    ✅ {h.get('title','?')[:55]} [{h.get('status','?')}]")

    print(f"\n  ⚙  AUTO_APPROVE: {'✅ Ativo' if AUTO_APPROVE else '✋ Manual (aguarda aprovação no dashboard)'}")
    print(f"  🌐 BACKEND: {BACKEND_URL}")
    print(f"  📸 INSTAGRAM: {'✅ Configurado' if INSTAGRAM_ACCESS_TOKEN else '⚠ Token não configurado'}")
    print()


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

async def main(once: bool = False):
    print("🚀 Publisher Autônomo iniciado")
    print(f"   Modo: {'AUTO PUBLISH' if AUTO_APPROVE else 'MANUAL (aprovação no dashboard)'}")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Instagram: {'✅' if INSTAGRAM_ACCESS_TOKEN else '⚠ sem token — modo exportação'}")
    print()

    while True:
        # Verifica se tem algo pra publicar
        await process_queue()

        # A cada hora, reconstrói a fila com notícias novas
        now = datetime.now(timezone.utc)
        if now.minute < 5:  # primeiros 5 min de cada hora
            await build_queue()

        if once:
            await build_queue()
            print_status()
            break

        # Verifica a cada 5 minutos
        await asyncio.sleep(300)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cripto Brasil Intel Publisher")
    parser.add_argument("--once",   action="store_true", help="Roda uma vez e sai")
    parser.add_argument("--status", action="store_true", help="Mostra status da fila")
    parser.add_argument("--build",  action="store_true", help="Só reconstrói a fila")
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.build:
        asyncio.run(build_queue())
        print_status()
    else:
        asyncio.run(main(once=args.once))
