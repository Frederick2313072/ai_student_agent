# 费曼学习系统 Docker配置
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/

# 暴露端口
EXPOSE 8005

# 启动命令
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
