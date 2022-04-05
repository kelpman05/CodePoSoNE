from .. import app,socketio
from flask import render_template,current_app,request

@socketio.on('start') 
def handle_start():
    print('client start')

@socketio.on('connect')
def handle_connect():
    print('client connect')
@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
@socketio.on('message')
def handle_message(message):
     print('received message: ' + message)
@socketio.on_error_default
def default_error_handler(e):
    print(request.event["message"]) # "my error event"
    print(request.event["args"])    # (data,)
@socketio.on_error()        # Handles the default namespace
def error_handler(e):
    print(request.event["message"]) # "my error event"
    print(request.event["args"])    # (data,)