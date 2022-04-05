from ..config import Config

class AppConfig():
  config:None
  def __init__(self,config:Config):
    super().__init__()
    self.config = config
  