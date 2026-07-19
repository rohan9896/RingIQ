release: alembic upgrade head
web: uvicorn apps.api.ringiq_api.main:app --host 0.0.0.0 --port $PORT
worker: python -m apps.worker.main
voice: python -m apps.voice_worker.agent start
