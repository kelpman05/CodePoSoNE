from typing import Callable

StateChange = Callable[[bool,float], None]
GetState = Callable[[None],bool]
CurrentValue = Callable[[None],object]
class GlobalConfig():
  state_change_invoke: StateChange
  state_send_invoke: StateChange
  get_state_invoke: GetState
  get_current_value_invoke: CurrentValue
  def __init__(self):
    super().__init__()
  def change_state(self,state:bool,time_span:float):
    if self.state_change_invoke:
      self.state_send_invoke(state,time_span)
      self.state_change_invoke(state,time_span)
  def get_state(self) -> bool:
    if self.get_state_invoke:
      return self.get_state_invoke()
    return False
  def get_current_value(self):
    if self.get_current_value_invoke:
      return self.get_current_value_invoke()
    return None