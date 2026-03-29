#!/bin/bash
# 数据库迁移验证脚本
# 用法: bash scripts/verify_migrations.sh
# 或在 Docker 容器内: docker-compose exec app bash /app/scripts/verify_migrations.sh

set -e

echo "========================================"
echo "开始验证 Alembic 数据库迁移..."
echo "========================================"

# 切换到 app 目录
cd /app || cd "$(dirname "$0")/.."

# 检查 alembic.ini 是否存在
if [ ! -f "alembic.ini" ] && [ ! -f "app/alembic.ini" ]; then
    echo "警告: alembic.ini 未找到，尝试使用 app/alembic"
fi

# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH:-}/app"

echo ""
echo "执行数据库迁移 (alembic upgrade head)..."
alembic upgrade head

echo ""
echo "========================================"
echo "✅ 数据库迁移验证成功!"
echo "========================================"

# 可选：显示当前版本
echo ""
echo "当前数据库版本:"
alembic current || true

echo ""
echo "迁移历史:"
alembic history --limit=5 || true
