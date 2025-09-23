from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TodoCreate(BaseModel):
    title: str 
    description: Optional[str] = None
    completed: bool = False 

class TodoResponse(BaseModel):
    id: int 
    title: str
    completed: bool 
    description: Optional[str] = None
    created_at: datetime