from .loader import Config
from ..global_config import GlobalConfig
import contextvars
from ..scene.consensus.poo_solve import PooSolve

config: contextvars.ContextVar[Config] = contextvars.ContextVar('config')
global_config: contextvars.ContextVar[GlobalConfig] = contextvars.ContextVar('global_config')
poo_solv = PooSolve()