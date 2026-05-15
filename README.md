# HSA Patrimon.IA — Guia para Iniciantes

Tudo pelo navegador. Não precisa instalar nada nem usar terminal.

⏱️ **Tempo:** ~30 minutos
💰 **Custo:** ~$45/mês ($20 Vercel + ~$25 Anthropic)

---

## ⚠️ Antes de começar — leia isto

A extração de PDFs leva 30-90 segundos. O Vercel **gratuito** desliga depois de 10 segundos, então não vai funcionar. Você precisa pagar o plano **Pro** ($20/mês) desde o começo.

Se quer economizar, use **Render** em vez de Vercel — fica $7/mês em vez de $20. Mas se quer Vercel mesmo, segue.

---

## Parte 1 — GitHub (10 minutos)

GitHub é onde o código vai morar. É grátis.

### 1.1. Crie sua conta

1. Vá em <https://github.com/signup>
2. Use seu email do trabalho
3. Escolha um username (algo curto, vai aparecer no URL)
4. Confirme o email

### 1.2. Crie o repositório

1. Faça login no GitHub
2. Clique no **+** no canto superior direito → **New repository**
3. Preencha:
   - **Repository name:** `hsa-patrimonia`
   - **Description:** deixa vazio
   - Marque **Private** (importante — vai ter chave de API ali)
   - **NÃO** marque "Add a README", "Add .gitignore" nem "Add a license"
4. Clica em **Create repository**

Vai abrir uma página com várias instruções de terminal. **Ignore tudo.** Mantenha essa aba aberta.

### 1.3. Suba os arquivos pelo navegador

1. Na página do repositório, clique no link **"uploading an existing file"** que aparece no meio da tela.
   - Se não achar, vai direto pra: `https://github.com/SEUUSERNAME/hsa-patrimonia/upload/main`
2. **Descompacte o arquivo `hsa-patrimonia-vercel.zip`** no seu computador (clique direito → "Extrair tudo" / "Unzip").
3. Abra a pasta descompactada. Você vai ver:
   - Pasta `api`
   - Pasta `public`
   - Arquivo `vercel.json`
   - Arquivo `.gitignore`
   - Arquivo `.env.example`
4. **Selecione tudo** e arraste para a área de upload do GitHub (a caixa grande com tracejado).
   - **Importante:** arraste o **conteúdo** da pasta, não a pasta inteira. Se aparecer `hsa-patrimonia-vercel/api/...` em vez de só `api/...`, refaça arrastando os itens internos.
5. Espera o upload (uns 30s — o `deck_builder.py` é grande).
6. Lá embaixo, em **Commit changes**, escreva: `setup inicial`
7. Clica no botão verde **Commit changes**.

### 1.4. Confere

A página do repo deve mostrar as pastas `api/` e `public/` no topo. Se mostrou, terminou a parte 1.

---

## Parte 2 — Chave da Anthropic (5 minutos)

A Anthropic é quem cobra pra ler os PDFs com IA.

### 2.1. Cria a conta

1. <https://console.anthropic.com> → **Sign up**
2. Usa o mesmo email

### 2.2. Adiciona crédito

1. No painel da Anthropic, no menu lateral, clica em **Billing**
2. **Add payment method** → cartão de crédito
3. **Add credits** → adiciona **$25** (dá pra umas 50 extrações)

### 2.3. Cria a chave

1. Menu lateral → **API Keys**
2. Botão **Create Key**
3. **Name:** `hsa-vercel`
4. Workspace e key type: deixa o padrão
5. **Create Key**
6. **COPIE A CHAVE AGORA.** Vai aparecer uma string longa começando com `sk-ant-`. Ela só aparece uma vez.
7. Cola num bloco de notas temporário, vai usar daqui a 5 minutos.

---

## Parte 3 — Vercel (10 minutos)

### 3.1. Cria a conta

1. <https://vercel.com/signup>
2. Clica em **Continue with GitHub** (vai conectar tua conta GitHub à Vercel)
3. Autoriza o acesso

### 3.2. Upgrade pro plano Pro

**Faça isso antes de tentar o deploy** — senão vai dar timeout e você vai ficar puxando os cabelos.

1. <https://vercel.com/account/plans>
2. Escolhe **Pro** ($20/mês)
3. Adiciona cartão
4. Confirma

### 3.3. Importa o projeto

1. <https://vercel.com/new>
2. Vai listar teus repos do GitHub. Acha **hsa-patrimonia** e clica em **Import**.
   - Se não aparecer: clica no link **Adjust GitHub App Permissions** e dá acesso ao repo.

3. Tela de configuração aparece. Preencha exatamente assim:
   - **Project Name:** `hsa-patrimonia` (vai virar parte do URL)
   - **Framework Preset:** **Other**
   - **Root Directory:** deixa `./`
   - **Build and Output Settings:** **NÃO MEXA**. Deixa todos os campos vazios.

4. **Environment Variables** — clica pra expandir essa seção. Adiciona **uma de cada vez** clicando em **Add Another** depois de cada uma:

   Variável 1:
   - **Key:** `ANTHROPIC_API_KEY`
   - **Value:** cola aquela chave `sk-ant-...` que você copiou na parte 2.3

   Variável 2:
   - **Key:** `HSA_PASSWORD`
   - **Value:** escolhe uma senha pro escritório (qualquer coisa, mínimo 8 caracteres). **Anota** porque os advogados vão precisar dela pra entrar.

   Variável 3:
   - **Key:** `ANTHROPIC_MODEL`
   - **Value:** `claude-sonnet-4-20250514`

   Variável 4:
   - **Key:** `CORS_ORIGINS`
   - **Value:** `*`

5. Clica em **Deploy**.

### 3.4. Aguarda

Vai mostrar logs de build em tempo real. **3-5 minutos.**

Vai aparecer "Installing dependencies", depois "Build completed". No fim, **um confete colorido** e o URL do site.

### 3.5. Testa

1. Clica no card de preview ou no URL `hsa-patrimonia-XXX.vercel.app`
2. Vai pedir senha → digita a `HSA_PASSWORD` que você definiu
3. Faz upload dos 2 PDFs de teste
4. Confere se gera Excel + PowerPoint

Se tudo funcionou, terminou. **Compartilha o URL e a senha com o escritório.**

---

## Parte 4 — Domínio customizado (opcional)

Se quer `patrimonia.hsa.adv.br` em vez do `hsa-patrimonia-XXX.vercel.app`:

1. No painel da Vercel, clica no projeto → aba **Settings** → menu lateral **Domains**
2. **Add** → digita `patrimonia.hsa.adv.br`
3. Vercel vai mostrar um valor CNAME (algo como `cname.vercel-dns.com`)
4. Vai no painel do seu provedor de DNS (Registro.br, Cloudflare, GoDaddy, o que for) e cria um registro:
   - **Tipo:** CNAME
   - **Nome:** `patrimonia`
   - **Valor:** o que a Vercel mostrou
5. Espera 10 minutos. Vercel emite o certificado SSL sozinho.

---

## Como atualizar o site depois

Se eu te entregar um arquivo novo (ex: `deck_builder.py` atualizado), **tudo pelo navegador, no GitHub:**

### Trocar um arquivo existente

1. Vai pro teu repo no GitHub
2. Navega até o arquivo que quer trocar (ex: clica em `api` → `deck_builder.py`)
3. Clica no **ícone de lápis** ✏️ no canto superior direito
4. **Apaga tudo** que tá lá (Ctrl+A → Delete)
5. Abre o arquivo novo no teu computador, copia o conteúdo, cola no GitHub
6. Vai pra baixo da página, em **Commit changes**:
   - **Commit message:** descreve o que mudou
   - Clica **Commit changes**
7. **Vercel detecta automaticamente** e faz redeploy em 2 minutos.

### Adicionar um arquivo novo

1. Página do repo → botão **Add file** → **Upload files**
2. Arrasta o arquivo
3. **Commit changes**

### Apagar um arquivo

1. Abre o arquivo no GitHub
2. Ícone de **lixeira** 🗑️ no canto superior direito
3. **Commit changes**

---

## Quando der erro

### "Function execution timed out"
Você não fez upgrade pro Vercel Pro. Faz agora ou nada vai funcionar.

### "ANTHROPIC_API_KEY not set"
Esqueceu de adicionar a env var. Vai em Vercel → projeto → Settings → Environment Variables → adiciona → depois precisa redeploy manual: vai em Deployments → 3 pontinhos do último deploy → Redeploy.

### "Invalid or missing password"
A senha que você tá digitando no site não bate com `HSA_PASSWORD`. Confere no painel da Vercel.

### Página fica em branco / "Cannot GET /"
Provavelmente fez upload errado dos arquivos — arrastou a pasta `hsa-patrimonia-vercel` em vez do conteúdo dela. **Apaga o repo no GitHub** (Settings → Delete repository, lá embaixo) e refaz a parte 1.

### Anthropic retorna erro 401
Sua API key tá errada. Gera nova em <https://console.anthropic.com> → API Keys, atualiza no painel da Vercel, redeploy.

### "Out of credits" da Anthropic
Acabou o crédito. Vai em <https://console.anthropic.com> → Billing → Add credits.

---

## Resumo das senhas que você precisa guardar

- **GitHub:** sua conta
- **Anthropic:** sua conta (a chave fica salva na Vercel)
- **Vercel:** sua conta (conecta via GitHub)
- **HSA_PASSWORD:** senha que o escritório usa pra entrar no site

---

## Custo mensal

- Vercel Pro: **$20**
- Anthropic API: **~$25** (~50 extrações)
- GitHub: **grátis**
- **Total: ~$45/mês**
