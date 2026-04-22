@echo off
REM start.bat - Windows 启动脚本

echo 启动 Docker 服务...
docker-compose up -d

echo 等待后端启动...
timeout /t 10 /nobreak

echo 重启前端以确保连接...
docker restart amazon_frontend

echo 服务已启动！
echo 前端: http://localhost:8880
echo 后端: http://localhost:8888
pause