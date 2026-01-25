# 使用轻量级的 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件并安装（利用缓存机制）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本代码
COPY bot.py .

# 创建一个数据卷目录，防止数据库在容器删除时丢失
VOLUME /app/data

# 修改脚本中的数据库路径（建议在脚本里将 DB_FILE 改为 /app/data/messages.db）
ENV DB_PATH=/app/data/messages.db

# 启动命令
CMD ["python", "bot.py"]

