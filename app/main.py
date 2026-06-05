from fastapi import FastAPI
from app.routers import chat_router

# Inicialização do FastAPI
app = FastAPI(
    title="Microserviço de Comunicação - Raiz do Bem",
    description="Backend em Python aplicando SOLID e Clean Architecture para o chat da ONG",
    version="1.0.0"
)


app.include_router(chat_router.router)

# Rota básica de saúde do sistema (Health Check)
@app.get("/")
def home():
    return {"status": "Backend rodando perfeitamente!"}