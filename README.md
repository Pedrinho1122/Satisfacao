# Sistema de Avaliação de Satisfação

Aplicação web para registo de avaliações de satisfação com dashboard de estatísticas em tempo real.

## Características

- 3 Botões de Avaliação com Emojis:
  - 😀 Muito Satisfeito (Verde)
  - 🙂 Satisfeito (Azul)
  - 😞 Insatisfeito (Vermelho)

- Dashboard com:
  - Estatísticas em tempo real
  - Gráficos de barras
  - Histórico completo
  - Atualização automática

- Base de Dados:
  - SQLite localmente
  - PostgreSQL em cloud
  - Contador sequencial diário

## Deploy em Cloud Gratuito

### Render (Recomendado)

1. Criar conta em [Render.com](https://render.com)
2. Clicar "New" → "Web Service"
3. Conectar repositório GitHub
4. Configurações:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Adicionar PostgreSQL Database (opcional)
6. Deploy!

### Railway

1. Criar conta em [Railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Selecionar repositório
4. Adicionar PostgreSQL (opcional)
5. Deploy automático!

## Instalação Local

```bash
pip install -r requirements.txt
python app.py
```

Aceda a `http://localhost:5000`

## Estrutura

```
Satisfacao/
├── app.py                 # Backend Flask
├── requirements.txt       # Dependências
├── templates/
│   ├── index.html        # Página de avaliação
│   └── dashboard.html    # Dashboard
└── static/
    ├── style.css         # Estilos principais
    ├── dashboard.css     # Estilos dashboard
    ├── script.js         # JS principal
    └── dashboard.js      # JS dashboard
```

## Tecnologias

- Python 3 + Flask
- SQLite / PostgreSQL
- HTML5 + CSS3 + JavaScript
- Gunicorn (servidor de produção)

## Licença

Projeto educacional - ATD e LP
