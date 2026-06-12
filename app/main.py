from fastapi import FastAPI
from app.routers import chat_router
from fastapi.middleware.cors import CORSMiddleware

# Inicialização do FastAPI
app = FastAPI(
    title="Microserviço de Comunicação - Raiz do Bem",
    description="Backend em Python aplicando SOLID e Clean Architecture para o chat da ONG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Porta local do seu Vite/React
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite todos os headers (Content-Type, etc.)
)


app.include_router(chat_router.router)

# Rota básica de saúde do sistema (Health Check)
@app.get("/", methods=["GET", "HEAD"])
def home():
    return {"status": "Backend rodando perfeitamente!"}