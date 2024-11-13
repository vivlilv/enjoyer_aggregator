from enum import Enum
from typing import Optional
from .base_handler import BaseHandler

class ProjectMode(Enum):
    GRADIENT = "gradient"
    DAWN = "dawn"

class ProjectManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_mode = None
            cls._instance.current_handler = None
            cls._instance.handlers = {}
        return cls._instance
    
    def switch_mode(self, mode: ProjectMode, user_id: int):
        # Lazy import to avoid circular dependencies
        if mode == ProjectMode.GRADIENT:
            from gradient.core.gradient_handler import GradientHandler
            self.current_handler = GradientHandler(user_id)
        elif mode == ProjectMode.DAWN:
            from dawn.core.dawn_handler import DawnHandler
            self.current_handler = DawnHandler(user_id)
        self.current_mode = mode
    
    @property
    def handler(self) -> Optional[BaseHandler]:
        if not self.current_handler:
            raise Exception("No project mode selected")
        return self.current_handler