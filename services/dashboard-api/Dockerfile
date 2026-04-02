FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/dashboard-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY libs /app/libs

# Copy service code
COPY services/dashboard-api/src /app/src

# Set Python path
ENV PYTHONPATH=/app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
