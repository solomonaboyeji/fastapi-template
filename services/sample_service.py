from typing import Union
from schemas.sample import Item
from schemas.user import User


class ItemService:

    def __init__(self, db, requesting_user: User | None = None) -> None:
        self.db = db
        self.cursor = self.db.cursor()
        self.requesting_user = requesting_user

    @staticmethod
    def create_item(item: Item, current_user: User) -> Union[Item, Exception]:
        # You can access current_user here to check scopes
        return Item(name=item.name)

    @staticmethod
    def delete_item(item_id: int, current_user: User) -> Union[dict, Exception]:
        # You can access current_user here to check scopes
        return {"message": f"Item {item_id} deleted"}

    @staticmethod
    def update_item(
        item_id: int, item: Item, current_user: User
    ) -> Union[Item, Exception]:
        # You can access current_user here to check scopes
        return Item(name=item.name)
