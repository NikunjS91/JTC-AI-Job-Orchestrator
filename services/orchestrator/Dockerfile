FROM python:3.11-slim

WORKDIR /app

# Copy shared libs
COPY libs /app/libs

# Copy service code
COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/orchestrator/src /app/src

# Set Python path
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]
