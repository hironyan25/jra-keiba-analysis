"""
データベース接続モジュール
"""
import os
import yaml
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_connection_string():
    """環境変数またはyamlファイルから接続情報を取得"""
    if os.getenv('DB_URI'):
        return os.getenv('DB_URI')
    
    # ディレクトリ構造を考慮したパス取得
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'database.yml')
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f).get('development', {})
        
        # データベース接続情報を取得
        host = config.get('host', '127.0.0.1')
        port = config.get('port', '5432')
        database = config.get('database', 'pckeiba')
        user = config.get('user', 'postgres')
        password = config.get('password', 'postgres')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    except Exception as e:
        logging.error(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        # デフォルト値を使用
        return "postgresql://postgres:postgres@127.0.0.1:5432/pckeiba"

def get_engine():
    """SQLAlchemy engineを取得"""
    conn_string = get_connection_string()
    return create_engine(conn_string)

def get_session():
    """SQLAlchemy sessionを取得"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
