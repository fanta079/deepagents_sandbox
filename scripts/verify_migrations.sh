#!/bin/bash
# 数据库迁移验证脚本
# 用法: bash scripts/verify_migrations.sh
# 或在 Docker 容器内: docker-compose exec app bash /app/scripts/verify_migrations.sh

set -e

echo "========================================"
echo "开始验证 Alembic 数据库迁移..."
echo "========================================"

# 记录脚本所在目录并切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH:-}${PYTHONPATH:+:}${PROJECT_ROOT}"

echo "项目根目录: $PROJECT_ROOT"
echo ""

# 检查 alembic.ini 或 app/alembic.ini 是否存在
if [ -f "alembic.ini" ]; then
    echo "找到 alembic.ini（根目录）"
elif [ -f "app/alembic.ini" ]; then
    echo "找到 app/alembic.ini"
elif [ -f "app/alembic/alembic.ini" ]; then
    echo "找到 app/alembic/alembic.ini"
else
    echo "警告: alembic.ini 未找到，alembic 将尝试自动定位"
fi

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
echo "迁移历史 (最近 5 条):"
alembic history --limit=5 || true
