## dev

- docker build -t deepseek-ocr-api:latest .

```bash
# 1. 构建镜像
docker build -t deepseek-ocr-api:latest .

# 2. 后台启动容器
docker run --rm --gpus all -d --name ocr-test-container deepseek-ocr-api:latest
docker run --rm --gpus all -it --name ocr-test-container deepseek-ocr-api:latest  // 前台启动
docker run --rm --gpus all -d -v docker_cache:/root/.cache/huggingface --name ocr-test-container deepseek-ocr-api:latest

#  local test
docker run --rm --gpus all -it -p 8000:8000 --name ocr-test-container -v docker_cache:/root/.cache/huggingface  deepseek-ocr-api:latest



# (确保 test_payload.json 文件已创建)

# 3. 发送作业
runpodctl send job ocr-test-container test_payload.json

# 4. 查看日志结果
docker logs ocr-test-container

# 5. 停止并清理容器
docker stop ocr-test-container
```
# 删除悬空镜像
> docker image prune

构建镜像时加上明确 tag，避免产生 <none> 镜像：
> docker build -t deepseek-ocr-api:v1 .

## code
- https://github.com/Bogdanovich77/DeekSeek-OCR---Dockerized-API/blob/main/start_server.py

docker run \
  --rm \
  --gpus all \
  -d \
  --name ocr-test-container \
  -v ~/huggingface_cache:/root/.cache/huggingface \
  deepseek-ocr-api:latest


curl -X POST http://localhost:8000/process  -H "Content-Type: application/json" -d @test_input.json
     docker run --rm --gpus all -it -p 8000:8000  -v docker_cache:/root/.cache/huggingface --name ocr-test-container deepseek-ocr-api:latest
docker run --rm --gpus all -it -p 8000:8000 --name ocr-test-container -v docker_cache:/root/.cache/huggingface  deepseek-ocr-api:latest
        // "value": "https://raw.githubusercontent.com/deepseek-ai/DeepSeek-OCR/refs/heads/main/assets/fig1.png"
nvidia-container-cli: requirement error: unsatisfied condition: cuda>=12.8, please update your driver to a newer version, or use an earlier cuda container: unknown

error starting container: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error running hook #0: error running hook: exit status 1, stdout: , stderr: Auto-detected mode as 'legacy'
nvidia-container-cli: requirement error: unsatisfied condition: cuda>=12.8, please update your driver to a newer version, or use an earlier cuda container: unknown
