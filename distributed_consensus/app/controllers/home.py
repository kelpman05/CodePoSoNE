from .. import app
from ..context import Config,config,global_config
from flask import render_template,current_app,request

@app.route('/')
@app.route('/index')
def index():
    local = config.local_node
    nodes = config.node_manager.nodes()
    black_nodes = config.node_manager.block_nodes()
    black_list = [
      f'Community {node.name}'
      for node in black_nodes
    ]
    black = "empty" if len(black_list)==0 else ",".join(black_list)
    state = global_config.get_state()
    current_value = global_config.get_current_value()
    round = current_value.get("round")
    running = current_value.get("running")
    price = current_value.get("price")
    demand = current_value.get("demand")
    nodes = sorted(nodes,key=lambda x:x.id)
    heat_index = int((local.id+3)/4)
    return render_template('index.html',local = local,nodes = nodes,heat_index=heat_index,black_list=black,round=round,running=running,price=price,demand=demand)