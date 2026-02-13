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

    # ========== LLM 模型配置 ==========
    # 默认 LLM 提供商
    DEFAULT_LLM_PROVIDER = os.getenv('DEFAULT_LLM_PROVIDER', 'deepseek')

    # DeepSeek 模型配置
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    # Ollama 模型配置
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'deepseek-ocr:latest')

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

    @classmethod
    def get_current_model_config(cls) -> dict:
        """获取当前模型配置"""
        provider = cls.DEFAULT_LLM_PROVIDER

        if provider == 'deepseek':
            return {
                'provider': 'deepseek',
                'model': cls.DEEPSEEK_MODEL,
                'api_key': cls.DEEPSEEK_API_KEY,
                'base_url': 'https://api.deepseek.com',
                'supports_reasoning': 'reasoner' in cls.DEEPSEEK_MODEL
            }
        elif provider == 'ollama':
            return {
                'provider': 'ollama',
                'model': cls.OLLAMA_MODEL,
                'api_key': 'ollama',
                'base_url': cls.OLLAMA_BASE_URL,
                'supports_reasoning': False
            }

        # 默认使用 DeepSeek
        return {
            'provider': 'deepseek',
            'model': cls.DEEPSEEK_MODEL,
            'api_key': cls.DEEPSEEK_API_KEY,
            'base_url': 'https://api.deepseek.com',
            'supports_reasoning': 'reasoner' in cls.DEEPSEEK_MODEL
        }

# 在导入时确保目录存在
Config.ensure_directories()
