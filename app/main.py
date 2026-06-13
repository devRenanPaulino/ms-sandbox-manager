from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import chat_router
from fastapi.middleware.cors import CORSMiddleware
import traceback

# Inicialização do FastAPI
app = FastAPI(
    title="Microserviço de Comunicação - Raiz do Bem",
    description="Backend em Python aplicando SOLID e Clean Architecture para o chat da ONG",
    version="1.0.0"
)

# CORSMiddleware deve ser adicionado ANTES dos routers.
# Ele envolve toda a aplicação ASGI e injeta os headers em TODAS as respostas,
# incluindo as geradas pelos exception_handlers abaixo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://raiz-do-bem.vercel.app",  # Produção - Vercel
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Handler global para exceções não tratadas.
# Retornar JSONResponse aqui garante que o CORSMiddleware consiga injetar
# os headers Access-Control-* mesmo em respostas de erro 500, evitando que
# o browser mascare o erro real como "CORS error".
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"[ERRO NÃO TRATADO] {request.method} {request.url}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno do servidor: {str(exc)}"},
    )


app.include_router(chat_router.router)


# Rota básica de saúde do sistema (Health Check)
@app.api_route("/", methods=["GET", "HEAD"])
def home():
    return {"status": "Backend rodando perfeitamente!"}