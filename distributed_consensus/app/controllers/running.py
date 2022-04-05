from .. import app
from ..context import config,global_config
from flask import request,current_app,jsonify
import time,datetime
@app.route('/running/start',methods=['POST'])
def start_bootstrap():
  time_span = time.time()
  global_config.change_state(True,time_span)
  return jsonify({"time_span":time_span})

@app.route('/running/stop',methods=['POST'])
def stop_bootstrap():
  time_span = time.time()
  global_config.change_state(False,time_span)
  return jsonify({"time_span":time_span})