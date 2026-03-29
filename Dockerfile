# ——— 第一阶段：构建依赖 ——————————————————————————————————————————
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装编译依赖（psycopg2 等需要编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ——— 第二阶段：运行镜像 ——————————————————————————————————————————
FROM python:3.11-slim

# 安全：非 root 用户
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash appuser

WORKDIR /app

# 从 builder 复制已安装的包
COPY --from=builder /root/.local /home/appuser/.local

# 复制项目代码
COPY --chown=appuser:appgroup . .

# 创建上传目录
RUN mkdir -p app/uploads && chown appuser:appgroup app/uploads

# 设置 PYTHONPATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 切换非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令：支持优雅关闭（接受 SIGTERM）
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
