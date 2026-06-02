FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
COPY baracap_backend/requirements.txt /workspace/baracap_backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

COPY baracap_backend /workspace/baracap_backend
COPY main.py /workspace/main.py

WORKDIR /workspace

EXPOSE 8000

CMD ["python", "main.py"]
