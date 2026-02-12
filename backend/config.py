"""
Bamboo 配置文件
集中管理应用配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""

    # Flask 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # 服务器配置
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))

    # DeepSeek API 配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

    # CORS 配置 - 前端开发服务器地址
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    CORS_ORIGINS = [
        'http://localhost:5173',  # Vite 默认端口
        'http://localhost:3000',   # CRA 默认端口
        FRONTEND_URL
    ]

    # 文件路径配置 - 统一使用 static 目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
    DOCS_DIR = os.path.join(STATIC_DIR, 'docs')
    VIDEOS_DIR = os.path.join(STATIC_DIR, 'videos')

    # 确保目录存在
    @staticmethod
    def ensure_directories():
        """确保所有必要的目录存在"""
        # 确保 static 目录存在
        os.makedirs(Config.STATIC_DIR, exist_ok=True)
        # 确保子目录存在
        dirs = [Config.IMAGES_DIR, Config.DOCS_DIR, Config.VIDEOS_DIR]
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)

# 在导入时确保目录存在
Config.ensure_directories()
