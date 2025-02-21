#!/bin/bash

# 1. 更新并安装所需的软件包
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip build-essential

# 2. 安装 pip 和 virtualenv
echo "Installing pip and virtualenv..."
python3.11 -m pip install --upgrade pip
python3.11 -m pip install virtualenv

# 3. 创建并激活虚拟环境
echo "Creating a virtual environment..."
virtualenv -p python3.11 venv
source venv/bin/activate

# 4. 安装项目依赖
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 5. 设置环境变量
export FLASK_APP=app.py  # 假设你的 Flask 应用文件是 app.py，如果是其他文件请修改
export FLASK_ENV=development  # 开发环境配置

# 6. 启动 Flask 服务器
echo "Starting Flask server..."
flask run --host=0.0.0.0 --port=5000

