"""Titik masuk Vercel (Python serverless, ASGI). Data berasal dari snapshot saat build (lihat vercel.json)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db  # noqa: E402
from app.main import app  # noqa: E402,F401

db.init()  # lifespan tidak dijamin berjalan di serverless
