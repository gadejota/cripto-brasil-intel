# DEPLOY.md — Guia de Publicação

## Opção 1: GitHub Pages (recomendado — grátis, sem backend)

### Passo a passo

1. **Crie um repositório no GitHub**
   - Acesse github.com → "New repository"
   - Nome sugerido: `cripto-brasil-intel`
   - Visibilidade: **Public** (obrigatório para Pages gratuito)

2. **Faça o upload dos arquivos**
   ```bash
   git init
   git add .
   git commit -m "Cripto Brasil Intel v9"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/cripto-brasil-intel.git
   git push -u origin main
   ```

3. **Ative o GitHub Pages**
   - Settings → Pages → Source: "Deploy from a branch"
   - Branch: `main`, pasta: `/ (root)`
   - Save

4. **URL do seu site:**
   `https://SEU_USUARIO.github.io/cripto-brasil-intel`

---

## Opção 2: Netlify (grátis, drag & drop)

1. Acesse **netlify.com**
2. "Add new site" → "Deploy manually"
3. Arraste a pasta `cripto-brasil-intel/` para a área de deploy
4. Pronto — URL gerada automaticamente (ex: `seu-site.netlify.app`)

**Para domínio customizado:** Settings → Domain Management → Add custom domain

---

## Opção 3: Vercel (grátis)

```bash
npm i -g vercel
cd cripto-brasil-intel
vercel
```

Segue as instruções do CLI.

---

## Backend (opcional — dados ao vivo)

O dashboard funciona 100% sem backend com dados estáticos curados.

Para ativar varredura ao vivo de fontes, configure o backend:

### Railway (recomendado — grátis até certo limite)

1. Acesse **railway.app**
2. "New Project" → "Deploy from GitHub repo"
3. Selecione o repo → pasta `backend/`
4. Variáveis de ambiente (opcional):
   ```
   IG_ACCESS_TOKEN=seu_token_meta_api
   IG_USER_ID=seu_id_instagram
   ```
5. Copie a URL gerada (ex: `https://meu-app.up.railway.app`)
6. No dashboard, clique em **"Configurar Backend"** e cole a URL

### Render (alternativa gratuita)

1. Acesse **render.com**
2. "New" → "Web Service" → conecte o GitHub
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn server:main --host 0.0.0.0 --port $PORT`

---

## Variáveis de Ambiente (backend)

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `PORT` | Sim | Porta do servidor (Railway/Render injetam automaticamente) |
| `IG_ACCESS_TOKEN` | Não | Token da Meta Graph API para publicação no Instagram |
| `IG_USER_ID` | Não | ID da conta Instagram Business |
| `OPENAI_API_KEY` | Não | Para geração de imagens DALL·E automatizadas |

---

## Atualizar o dashboard

Para atualizar para uma versão futura:

```bash
# Substitua o index.html e faça commit
cp nova-versao.html index.html
git add index.html
git commit -m "Atualiza dashboard v10"
git push
```

GitHub Pages atualiza em ~1-2 minutos automaticamente.
