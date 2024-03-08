from fastapi import APIRouter, Depends, Security
from core.database import get_db
from schemas.sample import Item
from schemas.user import User
from services.sample_service import ItemService
from utils.dependencies import has_required_scopes
from utils.scopes import ItemScope
from utils.security import get_current_user


router = APIRouter(prefix="/items", tags=["Items"])


@router.post("/items/", response_model=Item)
async def create_item(
    item: Item,
    db=Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[ItemScope.create]),
):
    """Creates a new item into the database"""
    ItemService.create_item(item, current_user)
    return item


@router.delete("/items/{item_id}", status_code=200)
async def delete_item(
    item_id: int,
    db=Depends(get_db),
    current_user: User = Security(get_current_user, scopes=[ItemScope.delete]),
):
    """Deletes an item from the database"""
    ItemService.delete_item(item_id, current_user)
    return {"message": f"Item {item_id} deleted"}


@router.put(
    "/items/{item_id}",
    response_model=Item,
    description="Updates the item in the database.",
)
async def update_item(
    item_id: int,
    item: Item,
    db=Depends(get_db),
    current_user: User = Security(
        get_current_user, scopes=[ItemScope.create, ItemScope.update]
    ),
):
    ItemService.update_item(item_id, item, current_user)
    return item
