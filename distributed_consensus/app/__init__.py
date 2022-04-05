from flask import Flask ,render_template
from flask_socketio import SocketIO
from .ws_manager import WebSocketManage
app = Flask(import_name=__name__,
template_folder='templates',static_folder='static')
socketio = SocketIO(app,ping_timeout=5)
socket_manager = WebSocketManage(socketio)
# ctx = app.app_context()
# ctx.push()
from .controllers import home,evil,message,running
