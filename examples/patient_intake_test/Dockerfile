FROM python:3.13-slim

LABEL org.opencontainers.image.title="patient_intake"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="HIPAA-compliant patient intake agent for scheduling and insurance verification"

# Non-root user for security
RUN useradd --create-home --shell /bin/bash agent
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R agent:agent /app
USER agent

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "patient_intake.main:app", "--host", "0.0.0.0", "--port", "8080"]
