FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 5000

ENV FLASK_APP=src/main.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run"]
