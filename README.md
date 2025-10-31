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
docker run --rm --gpus all -it -p 8000:8000 --name ocr-test-container -v docker_cache:/workspace/.cache/huggingface  deepseek-ocr-api:latest
# local test in back
docker run --rm --gpus all -d -p 8000:8000 --name ocr-test-container -v docker_cache:/workspace/.cache/huggingface  deepseek-ocr-api:latest



# (确保 test_payload.json 文件已创建)

# 4. 查看日志结果
docker logs ocr-test-container

# 5. 停止并清理容器
docker stop ocr-test-container

# curl test
curl -X POST http://localhost:8000/process  -H "Content-Type: application/json" -d @test_fastapi.json

# 并发测试
hey -n 5 -c 5 -m POST -t 150 -H "Content-Type: application/json" -d "$(cat test_fastapi.json)" http://localhost:8000/process

# 进入bash
docker exec -it ocr-test-container  /bin/bash
```
# 删除悬空镜像
> docker image prune


构建镜像时加上明确 tag，避免产生 <none> 镜像：
> docker build -t deepseek-ocr-api:v1 .

## code
- https://github.com/Bogdanovich77/DeekSeek-OCR---Dockerized-API/blob/main/start_server.py


curl -X POST http://localhost:8000/process  -H "Content-Type: application/json" -d @test_input.json
     docker run --rm --gpus all -it -p 8000:8000  -v docker_cache:/root/.cache/huggingface --name ocr-test-container deepseek-ocr-api:latest
