class UserProfile:
    def __init__(
        self,
        id: str = None,
        name: str = None,
        allow_tracking: bool = None
    ):
        self.id = id
        self.name = name
        self.allow_tracking = allow_tracking
