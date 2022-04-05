from .. import app
from ..context import Config,config
from flask import render_template,current_app,request
from ...core.node_evil import NormalEvil,DelegateEvil



@app.route('/evil/normal', methods=['POST'])
def normal_evil():
  demand_ignore = get_nodes('demand_ignore')
  demand_target = get_nodes('demand_target')
  demand_rate = get_rate('demand_rate')
  evil = NormalEvil(demand_ignore=demand_ignore,demand_target=demand_target,demand_rate=demand_rate)
  config.local_node.normal_evil = evil
  return "success"
@app.route('/evil/delegate', methods=['POST'])
def delegate_evil():
  price_ignore = get_nodes('price_ignore')
  price_target = get_nodes('price_target')
  price_rate = get_rate('price_rate')
  broadcast_ignore = get_nodes('broadcast_ignore')
  broadcast_collusion = get_nodes('broadcast_collusion')
  broadcast_target = get_nodes('broadcast_target')
  broadcast_rate = get_rate('broadcast_rate')
  evil = DelegateEvil(price_ignore=price_ignore,price_target=price_target,price_rate=price_rate,
  broadcast_ignore=broadcast_ignore,broadcast_collusion=broadcast_collusion,broadcast_target=broadcast_target,broadcast_rate=broadcast_rate)
  config.local_node.delegate_evil = evil
  return "success"
def get_nodes(parameter_name:str):
  parameter_str = request.form.get(parameter_name)
  nodes = [
    int(item)
    for item in parameter_str.split(',')
    if item and len(item) > 0 
  ]
  return nodes
def get_rate(parameter_name:str):
  parameter_str = request.form.get(parameter_name)
  rate = float(parameter_str) if parameter_str and len(parameter_str)>0 else None
  return rate
