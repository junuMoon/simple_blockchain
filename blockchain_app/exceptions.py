class InvalidHashError(Exception):
    def __init__(self, target_hash, registered_hash, block_index):
        self.target_hash = target_hash
        self.registered_hash = registered_hash
        self.msg = f"\nBlock has invalid hash\nHash: {self.registered_hash[:20]} -> {self.target_hash[:20]}"
        super().__init__(self.msg)


class OverSpentError(Exception):
    def __init__(self, sender, amount):
        self.sender = sender
        self.amount = amount
        self.msg = f"\n{self.sender} overspends {amount} coins"
        super().__init__(self.msg)