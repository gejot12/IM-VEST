# Konteks build = root repo (butuh ../../seed). Dipakai render.yaml; lokal: docker build -f apps/api/Dockerfile .
FROM python:3.12-slim
RUN pip install --no-cache-dir uv
WORKDIR /srv/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps/api/app ./app
COPY seed /srv/seed
ENV PATH="/srv/apps/api/.venv/bin:$PATH" IMVEST_ENV=production IMVEST_DB=/tmp/imvest.db
# DB kosong diisi otomatis di latar saat start (lihat main._bootstrap); disk gratis bersifat sementara.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
