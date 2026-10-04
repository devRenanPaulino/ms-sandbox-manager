# Microserviço de Comunicação - Raiz do Bem

> Backend em Python com arquitetura limpa (Clean Architecture) e princípios SOLID para gerenciar comunicações via WhatsApp

## Índice

- [Sobre](#sobre)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Como Executar](#como-executar)
- [Endpoints da API](#endpoints-da-api)
- [Exemplos de Uso](#exemplos-de-uso)
- [Estrutura de Diretórios](#estrutura-de-diretórios)
- [Padrões e Conceitos](#padrões-e-conceitos)
- [Testes](#testes)

---

## Sobre

Este é um **microserviço de comunicação** desenvolvido para a ONG **Raiz do Bem**. A API gerencia conversas de chat via **WhatsApp** (integrado através da **Twilio**), permitindo que colaboradores da ONG se comuniquem com clientes/usuários.

### Principais Funcionalidades

- **Enviar mensagens de texto** via WhatsApp  
- **Receber mensagens** através de webhooks da Twilio  
- **Iniciar conversas** com templates pré-configurados  
- **Manter histórico** de conversas em banco de dados  
- **Marcar mensagens como lidas**  
- **Listar conversas ativas** com prévia da última mensagem  

---

## Arquitetura

A aplicação segue os princípios de **Clean Architecture** com separação clara de responsabilidades em camadas:

```
┌─────────────────────────────────────────────────────────┐
│           Controllers / Routers (FastAPI)                │
│              (chat_router.py)                            │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│            Business Logic (Services)                      │
│              (chat_service.py)                           │
├─────────────────────────────────────────────────────────┤
│  - Orquestração de lógica de negócio                     │
│  - Coordenação entre Repositories e Gateways            │
│  - Tratamento de exceções de domínio                    │
└──────────────────┬──────────────────────────────────────┘
         ┌─────────┴─────────┐
         │                   │
┌────────▼────────┐   ┌──────▼──────────┐
│ Repositories    │   │ Gateways        │
│ (MongoDB)       │   │ (Twilio)        │
├─────────────────┤   ├─────────────────┤
│ - Save message  │   │ - Send text     │
│ - Get history   │   │ - Send template │
│ - Mark as read  │   │ - Webhook parse │
└────────┬────────┘   └────────┬────────┘
         │                     │
┌────────▼─────────────────────▼────────┐
│    External Systems (DB & APIs)        │
├─────────────────────────────────────┤
│  - MongoDB Atlas                      │
│  - Twilio WhatsApp API                │
└─────────────────────────────────────┘
```

### Camadas da Arquitetura

#### 1. **Routers** (`app/routers/`)
- Pontos de entrada HTTP da API
- Validação de requisições com Pydantic
- Definição de respostas (Response Models)
- Injeção de dependências

#### 2. **Services** (`app/services/`)
- Lógica de negócio principal
- Orquestração entre repositories e gateways
- Tratamento de erros de domínio
- Convertendo DTOs para entidades de domínio

#### 3. **Repositories** (`app/repositories/`)
- Abstração do acesso a dados
- Implementação específica para MongoDB
- Queries e operações CRUD
- Isolamento da lógica de persistência

#### 4. **Gateways** (`app/gateways/`)
- Abstração de serviços externos (Twilio)
- Tratamento de erros de integração
- Adaptação de respostas externas para o domínio

#### 5. **Domain Models** (`app/domain/`)
- Modelos de negócio (MessageChat, etc.)
- DTOs de entrada/saída (MessageCreateRequest, MessageResponse)
- Definição de contatos e validações

#### 6. **Core** (`app/core/`)
- Configurações (Config)
- Setup do banco de dados

---

## Pré-requisitos

- **Python 3.9+**
- **MongoDB Atlas** (ou MongoDB local)
- **Twilio Account** (credenciais para WhatsApp)
- **pip** ou **poetry** para gerenciar dependências

---

## Configuração

### 1. Clonar o Repositório

```bash
git clone <seu-repo>
cd ms-sandbox-menager
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt

# Se for desenvolver, instale também as dependências de desenvolvimento
pip install -r requirements-dev.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# MongoDB
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGO_DB_NAME=db_raiz_do_bem

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_NUMBER=whatsapp:+14155238886
TWILIO_TEMPLATE_SID=HXb5b62575e6e4ff6129ad7c8efe1f983e
```

**⚠️ Nunca commit credenciais no repositório!**

### 5. Variáveis de Ambiente Explicadas

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MONGO_URI` | String de conexão do MongoDB Atlas | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `MONGO_DB_NAME` | Nome do banco de dados | `db_raiz_do_bem` |
| `TWILIO_ACCOUNT_SID` | ID da conta Twilio | `ACxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Token de autenticação Twilio | `auth_tokenxxxxxxx` |
| `TWILIO_NUMBER` | Número WhatsApp Twilio | `whatsapp:+14155238886` |
| `TWILIO_TEMPLATE_SID` | ID do template de mensagem | `HXb5b...` |

---

## Como Executar

### Importante: Configurar Túnel para Twilio

Para que a aplicação possa receber webhooks da Twilio e testar a comunicação com sucesso, é necessário configurar um **túnel para expor sua máquina local na internet**. Recomendamos usar **ngrok** ou similar.

**Por que é necessário?** A Twilio precisa fazer requisições HTTP para seu endpoint `/chat/webhook`, mas se sua aplicação estiver rodando em `localhost:8000`, a Twilio não conseguirá acessar. O túnel resolve isso criando uma URL pública que encaminha as requisições para sua máquina local.

**Exemplo com ngrok:**
```bash
# 1. Baixar ngrok: https://ngrok.com/download
# 2. Executar ngrok apontando para a porta 8000
ngrok http 8000

# Você receberá uma URL pública como: https://abc123.ngrok.io
# 3. Configurar na Twilio Console:
#    Webhook URL: https://abc123.ngrok.io/chat/webhook
```

**Sem o túnel configurado, os testes com webhooks não funcionarão!**

---

### Desenvolvimento

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: **http://localhost:8000**

### Documentação Interativa (Swagger)

Acesse: **http://localhost:8000/docs**

### Produção

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Endpoints da API

### Health Check

**GET** `/`

Verifica se a API está funcionando.

```bash
curl http://localhost:8000/
```

**Resposta:**
```json
{
  "status": "Backend rodando perfeitamente!"
}
```

---

### 1. Enviar Mensagem de Texto

**POST** `/chat/send`

Envia uma mensagem de texto via WhatsApp.

**Request Body:**
```json
{
  "tel_client": "+5511999999999",
  "text": "Olá! Como posso ajudar?",
  "id_colaborador": 123
}
```

**Parâmetros:**
- `tel_client` (string, obrigatório): Telefone do cliente com DDI e DDD, ex: `+5511999999999`
- `text` (string, obrigatório): Conteúdo da mensagem
- `id_colaborador` (integer, opcional): ID do colaborador que envia a mensagem

**Resposta (201):**
```json
{
  "status": "Mensagem Enviada com sucesso",
  "id_db": "507f1f77bcf86cd799439011",
  "id_twilio": "SM_xxx"
}
```

**Exemplos de Uso:**
```bash
# cURL
curl -X POST http://localhost:8000/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "tel_client": "+5511987654321",
    "text": "Sua solicitação foi processada!",
    "id_colaborador": 5
  }'

# Python
import requests

url = "http://localhost:8000/chat/send"
payload = {
    "tel_client": "+5511987654321",
    "text": "Sua solicitação foi processada!",
    "id_colaborador": 5
}
response = requests.post(url, json=payload)
print(response.json())
```

---

### 2. Webhook - Receber Mensagens da Twilio

**POST** `/chat/webhook`

Endpoint para receber mensagens via webhook da Twilio.

**Enviado pela Twilio com Form Data:**
```
Body=Olá%2C+tudo+bem%3F
From=whatsapp%3A%2B5511999999999
MessageSid=SM_xxx
```

**Resposta (200):**
```
(vazio - Twilio espera resposta 200)
```

**⚠️ Configuração na Twilio:**
1. Acesse [Twilio Console](https://www.twilio.com/console)
2. Vá para **Messaging** > **WhatsApp Sandbox**
3. Configure o **Webhook URL**: `https://seu-dominio.com/chat/webhook`
4. Método: **POST**

---

### 3. Obter Histórico de Conversas

**GET** `/chat/history/{tel}`

Recupera o histórico de mensagens de um telefone específico.

**Parâmetros:**
- `tel` (string, path): Telefone do cliente, ex: `+5511999999999`
- `skip` (integer, query, default=0): Paginação - quantas mensagens pular
- `limit` (integer, query, default=20): Quantidade máxima de mensagens a retornar

**Resposta (200):**
```json
[
  {
    "id_db": "507f1f77bcf86cd799439011",
    "id_message_twilio": "SM_xxx",
    "tel_client": "+5511999999999",
    "text": "Oi, tudo bem?",
    "id_colaborador": null,
    "direction": "entrada",
    "date_time": "2024-06-05T10:30:00Z"
  },
  {
    "id_db": "507f1f77bcf86cd799439012",
    "id_message_twilio": "SM_yyy",
    "tel_client": "+5511999999999",
    "text": "Tudo ótimo! Como posso ajudar?",
    "id_colaborador": 5,
    "direction": "saida",
    "date_time": "2024-06-05T10:32:00Z"
  }
]
```

**Exemplos de Uso:**
```bash
# Últimas 20 mensagens
curl "http://localhost:8000/chat/history/%2B5511999999999"

# Com paginação
curl "http://localhost:8000/chat/history/%2B5511999999999?skip=20&limit=10"
```

---

### 4. Iniciar Conversa com Template

**POST** `/chat/initiate`

Inicia uma conversa com um cliente usando um template pré-definido na Twilio.

**Request Body:**
```json
{
  "tel_client": "+5511999999999",
  "param_1": "10/06/2024",
  "param_2": "14:30",
  "id_colaborador": 7
}
```

**Parâmetros:**
- `tel_client` (string, obrigatório): Telefone do cliente
- `param_1` (string, obrigatório): Primeiro parâmetro do template
- `param_2` (string, obrigatório): Segundo parâmetro do template
- `id_colaborador` (integer, opcional): ID do colaborador

**Resposta (200):**
```json
{
  "status": "Template enviado e janela de conversa aberta!",
  "id_db": "507f1f77bcf86cd799439013",
  "id_twilio": "SM_zzz"
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/chat/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "tel_client": "+5511999999999",
    "param_1": "15/06/2024",
    "param_2": "09:00",
    "id_colaborador": 3
  }'
```

---

### 5. Obter Conversas Ativas

**GET** `/chat/conversations`

Retorna uma lista de todas as conversas ativas com prévia das últimas mensagens.

**Resposta (200):**
```json
[
  {
    "tel_client": "+5511999999999",
    "text": "Obrigado pela ajuda!",
    "date_time": "2024-06-05T14:15:00Z",
    "direction": "entrada",
    "unread_count": 2
  },
  {
    "tel_client": "+5511988888888",
    "text": "Entendi, vou verificar isso.",
    "date_time": "2024-06-05T13:45:00Z",
    "direction": "saida",
    "unread_count": 0
  }
]
```

**Exemplo:**
```bash
curl http://localhost:8000/chat/conversations
```

---

### 6. Marcar Mensagens como Lidas

**PUT** `/chat/read/{tel}`

Marca todas as mensagens de um telefone como lidas.

**Parâmetros:**
- `tel` (string, path): Telefone do cliente

**Resposta (200):**
```json
{
  "status": "Mensagens marcadas como lidas com sucesso",
  "messagens_updated": 5
}
```

**Exemplo:**
```bash
curl -X PUT "http://localhost:8000/chat/read/%2B5511999999999"
```

---

## Exemplos de Uso

### Fluxo Completo: Iniciar Conversa e Enviar Mensagem

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Iniciar conversa com template
print("1. Iniciando conversa com template...")
initiate_response = requests.post(
    f"{BASE_URL}/chat/initiate",
    json={
        "tel_client": "+5511999999999",
        "param_1": "20/06/2024",
        "param_2": "10:00",
        "id_colaborador": 1
    }
)
print(f"   Status: {initiate_response.status_code}")
print(f"   Resposta: {initiate_response.json()}\n")

# Aguardar um pouco (para garantir que foi persistido)
time.sleep(1)

# 2. Enviar uma mensagem de acompanhamento
print("2. Enviando mensagem de acompanhamento...")
send_response = requests.post(
    f"{BASE_URL}/chat/send",
    json={
        "tel_client": "+5511999999999",
        "text": "Confirme sua presença clicando em responder!",
        "id_colaborador": 1
    }
)
print(f"   Status: {send_response.status_code}")
print(f"   Resposta: {send_response.json()}\n")

# 3. Obter histórico da conversa
print("3. Recuperando histórico da conversa...")
history_response = requests.get(
    f"{BASE_URL}/chat/history/%2B5511999999999"
)
print(f"   Status: {history_response.status_code}")
for msg in history_response.json():
    direction = "SAIDA" if msg["direction"] == "saida" else "ENTRADA"
    print(f"   {direction} {msg['date_time']}: {msg['text']}")
print()

# 4. Marcar como lido
print("4. Marcando como lido...")
read_response = requests.put(
    f"{BASE_URL}/chat/read/%2B5511999999999"
)
print(f"   Status: {read_response.status_code}")
print(f"   Resposta: {read_response.json()}")
```

### Receber Webhooks (Teste Local)

Para testar webhooks localmente, você pode usar uma ferramenta como **ngrok**:

```bash
# 1. Iniciar ngrok (compartilhar localhost na internet)
ngrok http 8000

# Você receberá uma URL como: https://abc123.ngrok.io

# 2. Configurar na Twilio
#    Webhook URL: https://abc123.ngrok.io/chat/webhook

# 3. Rodar a aplicação
uvicorn app.main:app --reload

# 4. Enviar mensagem via WhatsApp para o número da Twilio
#    A mensagem chegará no webhook e será salva no banco!
```

---

## Estrutura de Diretórios

```
ms-sandbox-menager/
│
├── app/
│   ├── __init__.py
│   ├── main.py                           # Aplicação FastAPI principal
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                     # Configurações (variáveis de ambiente)
│   │   └── database.py                   # Setup MongoDB
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   └── models.py                     # DTOs e entidades de domínio
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py            # Interface/contrato
│   │   └── mongo_repository.py           # Implementação MongoDB
│   │
│   ├── gateways/
│   │   ├── __init__.py
│   │   ├── base_gateway.py               # Interface/contrato
│   │   └── twilio_gateway.py             # Implementação Twilio
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── chat_service.py               # Lógica de negócio
│   │
│   └── routers/
│       ├── __init__.py
│       └── chat_router.py                # Endpoints HTTP
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                       # Fixtures pytest
│   └── (testes das funcionalidades)
│
├── .env                                  # Variáveis de ambiente (não commitar!)
├── .env.example                          # Template de .env
├── .gitignore
├── requirements.txt                      # Dependências de produção
├── requirements-dev.txt                  # Dependências de desenvolvimento
├── pytest.ini                            # Configuração do pytest
│
└── README.md                             # Este arquivo
```

---

## Padrões e Conceitos

### Dependency Injection (Injeção de Dependência)

FastAPI usa o sistema de dependências para injetar instâncias:

```python
def get_chat_service(
    db: Database = Depends(get_database),
    gateway: INotificationGateway = Depends(get_twilio_gateway),
) -> ChatService:
    repo = MongoChatRepository(db)
    return ChatService(repo=repo, gateway=gateway, template_sid=settings.TWILIO_TEMPLATE_SID)

@router.post("/send")
def send_message(payload: MessageCreateRequest, service: ChatService = Depends(get_chat_service)):
    return service.send_message(payload)
```

**Benefícios:**
- Fácil de testar (substituir dependências)
- Desacoplamento entre componentes
- Reutilização de instâncias

### Repository Pattern

O padrão Repository abstrai o acesso a dados:

```python
# Interface (contrato)
class IChatRepository(ABC):
    @abstractmethod
    def save_message(self, message: MessageChat) -> str:
        pass

# Implementação
class MongoChatRepository(IChatRepository):
    def save_message(self, message: MessageChat) -> str:
        result = self.db.messages.insert_one(message.dict())
        return str(result.inserted_id)
```

**Vantagens:**
- Fácil trocar de banco de dados (MongoDB → PostgreSQL)
- Testes sem precisar de banco real
- Centraliza lógica de persistência

### Gateway Pattern

O padrão Gateway abstrai serviços externos:

```python
# Interface
class INotificationGateway(ABC):
    @abstractmethod
    def send_text(self, to: str, body: str) -> ExternalMessageResult:
        pass

# Implementação
class TwilioWhatsAppGateway(INotificationGateway):
    def send_text(self, to: str, body: str) -> ExternalMessageResult:
        # Chamada à API Twilio
        message_sent = self._client.messages.create(...)
        return ExternalMessageResult(sid=message_sent.sid, delivered=True)
```

**Vantagens:**
- Trocar provider de SMS é trivial
- Isola falhas externas
- Facilita testes com mocks

### Data Transfer Objects (DTOs)

Separa o que vem do cliente do que é persistido:

```python
# DTO de entrada (validação)
class MessageCreateRequest(BaseModel):
    tel_client: str
    text: Optional[str] = None
    id_colaborador: Optional[int] = None

# Entidade de domínio (persistência)
class MessageChat(BaseModel):
    id_message_twilio: str
    tel_client: str
    text: Optional[str] = None
    direction: str
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = Field(default=True)

# DTO de saída (resposta)
class MessageResponse(BaseModel):
    id_db: str
    id_message_twilio: str
    tel_client: str
    text: Optional[str] = None
    direction: str
    date_time: datetime
```

---

## Testes

### Executar Todos os Testes

```bash
pytest
```

### Executar com Cobertura

```bash
pytest --cov=app --cov-report=html
```

### Executar Testes Específicos

```bash
pytest tests/test_chat_service.py -v
```

### Estrutura de Testes

```python
# tests/test_chat_service.py
from unittest.mock import MagicMock
from app.services.chat_service import ChatService

def test_send_message(mock_repo, mock_gateway):
    # Arrange
    service = ChatService(repo=mock_repo, gateway=mock_gateway, template_sid="SID")
    
    # Act
    result = service.send_message(payload)
    
    # Assert
    assert result["status"] == "Mensagem Enviada com sucesso"
    mock_repo.save_message.assert_called_once()
```

---

## Deploy

### Heroku

```bash
# 1. Criar Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Deploy
git push heroku main
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t chat-api .
docker run -p 8000:8000 --env-file .env chat-api
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `CORS error` no frontend | Adicione a origem do frontend em `CORS allow_origins` no `main.py` |
| `MongoConnectionError` | Verifique `MONGO_URI` e segurança de IP no MongoDB Atlas |
| `Twilio 401 Unauthorized` | Validate `TWILIO_ACCOUNT_SID` e `TWILIO_AUTH_TOKEN` |
| Webhook não recebe mensagens | Verifique URL do webhook na Twilio e se é HTTPS |
| Mensagem não chega ao cliente | A janela de 24h pode ter expirado (Twilio RestrictedPhoneNumber) |

---

**Última atualização**: Outubro 2026  
**Versão da API**: 1.0.0
