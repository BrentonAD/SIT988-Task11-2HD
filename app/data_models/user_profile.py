from typing import Optional, List

class UserProfile:
    def __init__(
        self,
        id: str = None,
        name: str = None,
        allergies: Optional[List[str]] = None,
        allow_tracking: bool = None
    ):
        self.id = id
        self.name = name
        self.allergies = allergies
        self.allow_tracking = allow_tracking
