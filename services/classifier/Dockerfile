FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY services/classifier/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY libs /app/libs

# Copy service code
COPY services/classifier/src /app/src

# Set Python path to include root for libs imports
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]
