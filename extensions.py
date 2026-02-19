
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth

# Database
db = SQLAlchemy()

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth'

# SocketIO
# Initialize with same settings as in app.py
socketio = SocketIO(
    cors_allowed_origins="*",    # Allow all origins
    async_mode='threading',       # Compatible mode
    ping_timeout=120,             # 2-minute timeout
    ping_interval=25,             # Keep-alive
    max_http_buffer_size=1e8,     # 100MB
    logger=False,
    engineio_logger=False,
    cookie=None
)

# OAuth
oauth = OAuth()
