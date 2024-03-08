from typing import List

from fastapi import HTTPException


def has_required_scopes(required_scopes: List[str], user_current_scopes: List[str]):

    for scope in required_scopes:
        if scope not in user_current_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
