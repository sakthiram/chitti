"""Bash agent server"""

from fastapi import FastAPI
from .agent import BashAgent

app = FastAPI(title="Chitti Bash Agent")
agent = BashAgent()
app.include_router(agent.router) 