FROM python:3.11-slim
WORKDIR /app
COPY 1251254-llm-bridge-core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY 1251254-llm-bridge-core /app
CMD ["python","-m","pytest","-q","tests"]
