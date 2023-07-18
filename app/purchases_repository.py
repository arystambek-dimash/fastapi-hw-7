from pydantic import BaseModel


class Purchase(BaseModel):
    user_id: int = 0
    flower_id: int = 0



class PurchasesRepository:
    purchases: list[Purchase]

    def __init__(self):
        self.purchases = []

    def save(self,purchases):
        self.purchases.append(purchases)
