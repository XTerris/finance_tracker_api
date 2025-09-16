from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .routers import users, transactions, auth, categories, accounts, goals, reminders


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(goals.router)
app.include_router(reminders.router)


@app.get("/")
async def main():
    # Redirect to /docs (relative URL)
    return RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)
