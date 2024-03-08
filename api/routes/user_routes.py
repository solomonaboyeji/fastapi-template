from fastapi import APIRouter, Depends, Security
from core.database import get_db
from schemas.sample import Item
from schemas.user import ListUsers, User
from services.user_service import UserService
from utils.dependencies import has_required_scopes
from utils.scopes import UserScope
from utils.security import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=ListUsers)
async def list_users(
    current_user: User = Security(get_current_user, scopes=[UserScope.list_]),
    db=Depends(get_db),
    page_count: int = 10,
    offset: int = 0,
):
    """Lists out all the users in the database."""

    result = UserService(db, requesting_user=current_user).get_users(offset, page_count)

    if isinstance(result, ListUsers):
        return result
    else:
        raise result


# @router.post("/items/", response_model=Item)
# async def create_item(
#     item: Item, current_user: User = Security(has_required_scopes(["create_item"]))
# ):
#     """Creates a new item into the database"""
#     ItemService.create_item(item, current_user)
#     return item


# @router.delete("/items/{item_id}", status_code=200)
# async def delete_item(
#     item_id: int, current_user: User = Depends(has_required_scopes(["delete_item"]))
# ):
#     """Deletes an item from the database"""
#     ItemService.delete_item(item_id, current_user)
#     return {"message": f"Item {item_id} deleted"}


# @router.put(
#     "/items/{item_id}",
#     response_model=Item,
#     description="Updates the item in the database.",
# )
# async def update_item(
#     item_id: int,
#     item: Item,
#     current_user: User = Security(
#         has_required_scopes(["update_item"]), scopes=["update_item", "create_item"]
#     ),
# ):
#     ItemService.update_item(item_id, item, current_user)
#     return item
