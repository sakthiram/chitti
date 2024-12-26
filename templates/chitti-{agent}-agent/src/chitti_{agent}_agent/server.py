"""Agent server implementation"""

from fastapi import FastAPI
from .agent import CustomAgent

app = FastAPI(title="Chitti Custom Agent")
agent = CustomAgent()
app.include_router(agent.router) 