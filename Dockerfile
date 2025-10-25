# 1. Use a validated, working base image
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2204

# 2. Set working directory
WORKDIR /app

# 设置Hugging Face的缓存目录
ENV HF_HOME="/runpod-volume/.cache/huggingface"

# 3. Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY handler.py .
COPY fastapi_server.py .
COPY test_input.json .

#### LOCAL TEST
# 5. Expose the port FastAPI will use
# EXPOSE 8000

# 6. CRITICAL CHANGE: Do not start the service.
#    Instead, start a bash shell so the user can start the service manually.
# CMD ["bash"]
##### LOCAL TEST END

# 5. 设置容器启动时要执行的命令
# 这会启动Runpod的serverless worker，并监听请求
CMD ["python", "handler.py"]
