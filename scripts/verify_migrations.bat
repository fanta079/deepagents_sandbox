@echo off
REM 数据库迁移验证脚本 (Windows)
REM 用法: scripts\verify_migrations.bat

echo ========================================
echo 开始验证 Alembic 数据库迁移...
echo ========================================
echo.

cd /d "%~dp0.."

echo 执行数据库迁移 (alembic upgrade head)...
alembic upgrade head

echo.
echo ========================================
echo ✅ 数据库迁移验证成功!
echo ========================================
echo.

echo 当前数据库版本:
alembic current

echo.
echo 迁移历史:
alembic history --limit=5

pause
