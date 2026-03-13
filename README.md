# 🇧🇷 Cripto Brasil Intel — v9

Dashboard de inteligência cripto para criadores de conteúdo brasileiros.
DNA: **@defiverso** + **@criptobrasilofc**

**[Abrir o Dashboard →](https://SEU_USUARIO.github.io/cripto-brasil-intel)**

---

## O que é

Ferramenta de inteligência editorial para criadores de conteúdo cripto no Brasil. Funciona 100% no browser — sem backend obrigatório.

### Funcionalidades

- **Feed Viral** — 24 notícias com viral scoring, filtros por categoria (Alta / Baixa / Edu / BR / Macro / Geo)
- **Carrosséis Autorais** — 13 carrosséis completos com slides, roteiros de reel e prompts DALL·E
- **98 Fontes** — Bloomberg, Reuters, Glassnode, Santiment, CryptoQuant, Cointimes, Livecoins, Banco Central BR, e mais
- **Preços ao Vivo** — via Kraken, CoinGecko, CoinCap (sem API key)
- **Eventos** — calendário de eventos macro com impacto em BTC
- **Publisher** — fila de publicação integrada ao backend (Railway/Render)

---

## Deploy em 2 minutos — GitHub Pages

### 1. Fork ou clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/cripto-brasil-intel.git
cd cripto-brasil-intel
```

### 2. Ative o GitHub Pages

1. Vá em **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / pasta: **/ (root)**
4. Clique em **Save**

Pronto. Em 1-2 minutos o site está em:
`https://SEU_USUARIO.github.io/cripto-brasil-intel`

### 3. (Opcional) Configure o backend

Para dados ao vivo com varredura real de fontes, rode o backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn server:main --reload
```

Ou faça deploy gratuito no Railway:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

Depois de deploy, clique em **"Configurar Backend"** no dashboard e cole a URL do Railway.

---

## Estrutura do projeto

```
cripto-brasil-intel/
├── index.html          ← Dashboard completo (single-file)
├── backend/            ← Backend FastAPI (opcional)
│   ├── server.py
│   ├── editorial_engine.py
│   ├── publisher.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   └── render.yaml
├── README.md
└── .gitignore
```

---

## Backend — Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/health` | GET | Status do servidor |
| `/api/news` | GET | Notícias ao vivo com viral score |
| `/api/queue` | GET | Fila de publicação |
| `/api/queue/approve` | POST | Aprovar post da fila |
| `/api/queue/reject` | POST | Remover post da fila |

---

## Fontes monitoradas (98)

### Notícias Cripto
CoinDesk · Cointelegraph · Cointelegraph BR · Decrypt · The Block · Bitcoin Magazine · Bitcoinist · Crypto Briefing · NewsBTC · AMBCrypto · CoinGape · ZyCrypto · BeInCrypto · Cryptonews · CryptoSlate · Blockworks · DLNews

### Brasil
Livecoins · CriptoFácil · CriptoBR · Mercado Bitcoin Blog · Foxbit Blog · Hashdex Blog · Portal do Bitcoin · InfoMoney Cripto · Estadão Cripto

### Macro / Global Finance
Bloomberg · Reuters Finance · Financial Times · The Economist · Wall Street Journal · Zero Hedge · MacroVoices · Real Vision · ARK Invest Research · Grayscale Research · VanEck Research · Fidelity Digital Assets · Bernstein Research

### On-Chain & Dados
Glassnode · Santiment · CryptoQuant · Nansen · Messari · Kaiko Research · K33 Research · 21Shares Research · Equilibrium Research · Rekt.news

### Banco Central & Regulação
Banco Central do Brasil · IBGE · Tesouro Nacional · Agência Senado

### YouTube / Podcasts BR
Bruno Perini · Nathalia Arcuri · Thiago Nigro · Fernando Ulrich

### Instagram BR — Referência
@defiverso · @area.bitcoin · @vaultcapitaloficial · @ri.cred · @criptofacil · @criptobrasilofc · @mestredasc · @cryptomanuela · @investindoemcripto

---

## Licença

MIT — use, modifique e distribua livremente.

---

Feito por **@defiverso** + **@criptobrasilofc** · Cripto Brasil Intel v9
