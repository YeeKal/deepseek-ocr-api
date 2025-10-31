## 使用hey进行并发测试

> sudo apt-get install hey

## 单worker + 6个并发

**参数设置**

- MAX_CONCURRENT_GPU_REQUESTS = 1: gpu 允许并发执行个数
- MAX_QUEUE_SIZE = 5： 最大队列长度
- REQUEST_TIMEOUT_SECONDS = 60： 请求超时时间

**测试结果**

6个并发请求，在60s内：
- 3个正常运行
- 1个超出队列长度，返回429
- 2个请求超时，返回408
- GPU 5070ti 待机内存占用12G/16G
- GPU 5070ti 运行内存占用13G/16G

符合设计，并发请求被串行处理，服务运行正常


**测试打印输出**

```bash
<!-- 共6个请求 6 个并发 -->
hey -n 6 -c 6 -m POST -t 150 -H "Content-Type: application/json" -d "$(cat test_fastapi.json)" http://localhost:8000/process

Summary:
  Total:	60.0032 secs
  Slowest:	60.0030 secs
  Fastest:	0.0034 secs
  Average:	38.5459 secs
  Requests/sec:	0.1000

  Total data:	10091 bytes
  Size/request:	1681 bytes

Response time histogram:
  0.003 [1]	|■■■■■■■■■■■■■
  6.003 [0]	|
  12.003 [0]	|
  18.003 [1]	|■■■■■■■■■■■■■
  24.003 [0]	|
  30.003 [0]	|
  36.003 [0]	|
  42.003 [1]	|■■■■■■■■■■■■■
  48.003 [0]	|
  54.003 [0]	|
  60.003 [3]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


Latency distribution:
  10% in 17.3940 secs
  25% in 37.6850 secs
  50% in 56.1870 secs
  75% in 60.0030 secs
  0% in 0.0000 secs
  0% in 0.0000 secs
  0% in 0.0000 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0005 secs, 0.0034 secs, 60.0030 secs
  DNS-lookup:	0.0002 secs, 0.0000 secs, 0.0005 secs
  req write:	0.0001 secs, 0.0000 secs, 0.0001 secs
  resp wait:	38.5452 secs, 0.0028 secs, 60.0023 secs
  resp read:	0.0001 secs, 0.0000 secs, 0.0001 secs

Status code distribution:
  [200]	3 responses
  [408]	2 responses
  [429]	1 responses
```

## 2 worker + 6 个并发

**参数设置**

- MAX_CONCURRENT_GPU_REQUESTS = 2: gpu 允许并发执行个数
- MAX_QUEUE_SIZE = 5： 最大队列长度
- REQUEST_TIMEOUT_SECONDS = 60： 请求超时时间

**测试结果**

6个并发请求，在60s内：
- 0个正常运行
- 1个超出队列长度，返回429
- 5个请求超时
- GPU 5070ti 待机内存占用12G/16G
- GPU 5070ti 运行内存占用13G/16G

高并发请求打到一个串行处理的 GPU OCR 服务上


**测试打印输出**

```bash
hey -n 6 -c 6 -m POST -t 150 -H "Content-Type: application/json" -d "$(cat test_fastapi.json)" http://localhost:8000/process

Summary:
  Total:	60.0077 secs
  Slowest:	60.0077 secs
  Fastest:	0.0054 secs
  Average:	50.0062 secs
  Requests/sec:	0.1000

  Total data:	521 bytes
  Size/request:	86 bytes

Response time histogram:
  0.005 [1]	|■■■■■■■■
  6.006 [0]	|
  12.006 [0]	|
  18.006 [0]	|
  24.006 [0]	|
  30.007 [0]	|
  36.007 [0]	|
  42.007 [0]	|
  48.007 [0]	|
  54.007 [0]	|
  60.008 [5]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


Latency distribution:
  10% in 60.0041 secs
  25% in 60.0053 secs
  50% in 60.0072 secs
  75% in 60.0077 secs
  0% in 0.0000 secs
  0% in 0.0000 secs
  0% in 0.0000 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0015 secs, 0.0054 secs, 60.0077 secs
  DNS-lookup:	0.0007 secs, 0.0005 secs, 0.0008 secs
  req write:	0.0001 secs, 0.0001 secs, 0.0001 secs
  resp wait:	50.0044 secs, 0.0040 secs, 60.0056 secs
  resp read:	0.0001 secs, 0.0000 secs, 0.0002 secs

Status code distribution:
  [408]	5 responses
  [429]	1 responses
```

## 2 worker + 2个并发

**参数设置**

- MAX_CONCURRENT_GPU_REQUESTS = 2: gpu 允许并发执行个数
- MAX_QUEUE_SIZE = 5： 最大队列长度
- REQUEST_TIMEOUT_SECONDS = 60： 请求超时时间

**测试结果**

2个并发请求，在60s内：
- 6个请求超时
- GPU 5070ti 运行内存占用13G/16G

高并发请求打到一个串行处理的 GPU OCR 服务上


**测试打印输出**

```bash
hey -n 6 -c 2 -m POST -t 150 -H "Content-Type: application/json" -d "$(cat test_fastapi.json)" http://localhost:8000/process

Summary:
  Total:	180.0083 secs
  Slowest:	60.0035 secs
  Fastest:	60.0013 secs
  Average:	60.0023 secs
  Requests/sec:	0.0333

  Total data:	516 bytes
  Size/request:	86 bytes

Response time histogram:
  60.001 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  60.002 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  60.002 [0]	|
  60.002 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  60.002 [0]	|
  60.002 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  60.003 [0]	|
  60.003 [0]	|
  60.003 [0]	|
  60.003 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  60.004 [1]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


Latency distribution:
  10% in 60.0014 secs
  25% in 60.0019 secs
  50% in 60.0024 secs
  75% in 60.0035 secs
  0% in 0.0000 secs
  0% in 0.0000 secs
  0% in 0.0000 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0002 secs, 60.0013 secs, 60.0035 secs
  DNS-lookup:	0.0001 secs, 0.0000 secs, 0.0002 secs
  req write:	0.0001 secs, 0.0000 secs, 0.0003 secs
  resp wait:	60.0019 secs, 60.0012 secs, 60.0031 secs
  resp read:	0.0001 secs, 0.0000 secs, 0.0002 secs

Status code distribution:
  [408]	6 responses
```
