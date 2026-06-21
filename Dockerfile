# Application image for the financial management back-end.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies from the pinned lock file for reproducible builds.
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt

# Application sources (run via --app-dir src, so no package install is needed).
COPY src ./src
COPY migrations ./migrations

# Pre-install the DuckDB extensions so the container does not download them on
# first request.
RUN python -c "import duckdb; c = duckdb.connect(); c.execute('INSTALL iceberg'); c.execute('INSTALL httpfs')"

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
