#  Sistema Web de Agendamentos para Lava Rápido

Aplicação web desenvolvida com **Django** (backend) e **JavaScript moderno** (frontend interativo) para gerenciamento completo e agendamento de serviços de um Lava Rápido.

---

##  Funcionalidades Principais

### 1.  Área do Cliente (Pública)
- **Visualização Dinâmica de Horários Livres**:
  - Navegação intuitiva pelos próximos 14 dias (pílulas com dias da semana e status).
  - Consulta assíncrona (`fetch` / AJAX) dos horários livres em tempo real.
  - Bloqueio automático de datas passadas, horários já decorridos e dias fechados (ex: domingos).
  - Cálculo de capacidade em tempo real (exibição de vagas disponíveis por horário).
- **Formulário de Agendamento Completo**:
  - Seleção do serviço desejado com exibição de preço e tempo estimado.
  - Dados solicitados: **Modelo do Carro**, **Nome Completo** e **Contato (WhatsApp)** com máscara automática `(11) 99999-9999`.
  - Campo opcional para **Placa do Carro** e **Observações**.
  - Resumo em tempo real do agendamento antes da confirmação.
- **Comprovante de Reserva**:
  - Geração de código único da reserva (ex: `LR-B74A89`).
  - Botão com link direto para enviar mensagem de confirmação no WhatsApp do Lava Rápido.
  - Botão para imprimir/salvar comprovante.
- **Consulta de Agendamento**:
  - Modal para o cliente consultar o status da sua reserva a qualquer momento digitando o código ou seu número de telefone.

### 2.  Área do Dono do Lava Rápido (Painel Administrativo)
- **Autenticação Segura**:
  - Login e Logout protegidos pelo Django Authentication.
  - Acesso padrão inicial:
    - **Usuário:** `admin`
    - **Senha:** `admin123`
- **Dashboard de Gestão**:
  - **Métricas em Tempo Real**: Total de agendamentos hoje, pendentes de confirmação, confirmados, concluídos e faturamento estimado do dia e do mês.
  - **Filtros Rápidos**: Hoje, Amanhã, Esta Semana, Este Mês, Todos ou seletor de data específica.
  - **Filtro por Status**: Pendente, Confirmado, Concluído e Cancelado.
  - **Busca Rápida**: Pesquisa instantânea por nome do cliente, modelo do carro, placa, telefone ou código.
  - **Ações Rápidas via JavaScript (AJAX)**:
    - Confirmar agendamento pendente com 1 clique.
    - Marcar como concluído.
    - Alterar status para qualquer valor sem recarregar a tela inteira.
    - Botão direto para abrir conversa no WhatsApp com o cliente.
    - Exclusão de agendamentos.
- **Agendamento Manual**:
  - Modal para o próprio dono cadastrar agendamentos recebidos por telefone ou presencialmente no balcão.
- **Gerenciamento de Serviços**:
  - Cadastro, ativação/desativação e exclusão de serviços com preço, duração e ícones.
- **Configuração de Horários e Regras**:
  - Horário de abertura e fechamento.
  - Intervalo entre agendamentos (em minutos).
  - Capacidade / Vagas simultâneas (quantos carros podem ser lavados ao mesmo tempo).
  - Intervalo de almoço.
  - Seleção dos dias de funcionamento da semana.

---

##  Estrutura do Projeto

```text
agendamentos/
│
├── manage.py
├── requirements.txt
├── README.md
├── Dockerfile                   # Configuração da imagem Docker da aplicação
├── docker-compose.yml           # Orquestração do Django + PostgreSQL
├── .dockerignore                # Arquivos ignorados no build da imagem
├── dados_agendamentos.json      # Dados exportados para carga inicial
├── db.sqlite3                   # Banco SQLite (para execução local sem Docker)
│
├── lavarapido_project/          # Configurações do Projeto Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Suporte a PostgreSQL (Docker) e SQLite (Local)
│   ├── urls.py                  # Roteamento global
│   └── wsgi.py
│
└── agendamentos/                # App de Agendamentos
    ├── admin.py                 # Painel nativo do Django Admin
    ├── apps.py
    ├── forms.py                 # Formulários validados (Cliente e Admin)
    ├── models.py                # Modelos: Servico, ConfiguracaoLavaRapido, Agendamento
    ├── services.py / utils.py   # Lógica de cálculo de horários livres e vagas
    ├── tests.py                 # 7 Testes unitários e de integração automatizados
    ├── urls.py                  # Rotas públicas, administrativas e APIs
    ├── views.py                 # Views e endpoints JSON
    │
    ├── management/
    │   └── commands/
    │       └── seed_data.py     # Script para popular dados iniciais e admin
    │
    ├── static/                  # Arquivos Estáticos
    │   ├── css/
    │   │   └── custom.css       # Estilos visuais, cards e badges
    │   └── js/
    │       ├── agendamento.js   # Interatividade do agendamento e chamadas à API
    │       └── dashboard.js     # Interatividade do painel do dono (AJAX)
    │
    └── templates/               # Templates HTML
        ├── base.html            # Layout mestre com Bootstrap 5 e navbar responsiva
        └── agendamentos/
            ├── index.html       # Página principal de agendamento do cliente
            ├── sucesso.html     # Comprovante de agendamento confirmado
            ├── login.html       # Tela de login do dono
            ├── dashboard.html   # Painel de controle do dono
            ├── servicos.html    # Gerenciamento de serviços
            └── configuracoes.html # Configuração de regras e horários
```

---

##  Como Executar o Projeto

Você pode executar o projeto de duas formas:
1. **Com Docker e PostgreSQL (Recomendado)**: Não requer Python nem PostgreSQL instalados na máquina host.
2. **Localmente com Python e SQLite**: Execução tradicional para desenvolvimento simples.

---

###  Opção 1: Executando com Docker e PostgreSQL (Recomendado)

#### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução no Windows/Mac/Linux.

#### 1. Iniciar os Containers (Django + PostgreSQL)
No terminal, dentro da pasta do projeto:
```powershell
docker compose up -d --build
```
> O comando acima baixa a imagem do PostgreSQL 16, constrói a imagem da aplicação Python e inicia ambos os serviços em segundo plano.

#### 2. Executar as Migrações do Banco de Dados
Crie as tabelas dentro do banco PostgreSQL:
```powershell
docker compose exec web python manage.py migrate
```

#### 3. Popular os Dados Iniciais
Você pode carregar os serviços pré-cadastrados de duas formas:

**Opção A (Carga completa via Fixture - Recomendada):**
```powershell
docker compose exec web python manage.py loaddata dados_agendamentos.json
```

**Opção B (Via script de seed):**
```powershell
docker compose exec web python manage.py seed_data
```
> Usuário administrador gerado pelo seed:
> - **Login:** `admin`
> - **Senha:** `admin123`

#### 4. Criar um Superusuário Administrador (Opcional)
Se preferir criar suas próprias credenciais de acesso ao painel:
```powershell
docker compose exec web python manage.py createsuperuser
```

#### 5. Acessar a Aplicação
Abra no navegador:
- **Página de Agendamentos (Clientes):** [http://localhost:8000/](http://localhost:8000/)
- **Área do Dono / Login:** [http://localhost:8000/login/](http://localhost:8000/login/)
- **Painel de Controle:** [http://localhost:8000/painel/](http://localhost:8000/painel/)
- **Django Admin:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

####  Comandos Úteis do Docker

- **Verificar status dos containers:**
  ```powershell
  docker compose ps
  ```

- **Acompanhar logs em tempo real:**
  ```powershell
  docker compose logs -f web
  ```

- **Parar os containers:**
  ```powershell
  docker compose down
  ```

- **Reiniciar os containers:**
  ```powershell
  docker compose restart
  ```

- **Acessar o terminal interativo do PostgreSQL (psql):**
  ```powershell
  docker compose exec db psql -U lavarapido_user -d lavarapido_db
  ```

- **Executar consulta SQL rápida diretamente pelo terminal:**
  ```powershell
  docker compose exec db psql -U lavarapido_user -d lavarapido_db -c "SELECT id, nome, preco FROM agendamentos_servico;"
  ```

- **Executar os testes automatizados dentro do container:**
  ```powershell
  docker compose exec web python manage.py test
  ```

---

###  Opção 2: Executando Localmente (sem Docker, usando SQLite)

#### Pré-requisitos
- Python 3.10 ou superior instalado.

#### 1. Criar e Ativar o Ambiente Virtual
No terminal, dentro da pasta do projeto:

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Instalar as Dependências
```bash
pip install -r requirements.txt
```

#### 3. Aplicar as Migrações
```bash
python manage.py migrate
```

#### 4. Popular os Dados Iniciais
```bash
python manage.py seed_data
```

#### 5. Iniciar o Servidor
```bash
python manage.py runserver
```

Acesse: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

##  Executando os Testes Automatizados

O projeto conta com testes unitários cobrindo:
- Cálculo e geração dinâmica de horários livres.
- Bloqueio de datas passadas e dias fechados.
- Prevenção de overbooking / esgotamento de vagas por horário.
- Fluxo de agendamento com dados de cliente, veículo e serviço.
- Consulta de agendamentos pela API.
- Proteção de acesso e atualização de status pelo painel do dono.

Para rodar os testes:
```bash
python manage.py test
```
Resultado: **7 testes passaram (OK)!**
