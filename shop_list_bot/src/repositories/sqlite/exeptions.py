class InvalidFilterKeyError(ValueError):
    """Custom exception for invalid filter keys."""

    def __init__(self, key: str):
        super().__init__(f"Invalid filter key: {key}")
        self.key = key
