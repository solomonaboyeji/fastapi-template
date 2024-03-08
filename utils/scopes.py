from enum import Enum, StrEnum


class UserScope(StrEnum):
    create = "users.create"
    delete = "users.delete"
    update = "users.update"
    list_ = "users.list"


class ItemScope(StrEnum):
    create = "items.create"
    delete = "items.delete"
    update = "ietms.update"
    list_ = "items.list"
