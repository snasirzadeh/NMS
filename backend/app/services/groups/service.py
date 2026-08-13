from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Group
from app.schemas.groups import GroupCreate, GroupUpdate
from app.services.errors import ConflictError, NotFoundError


def get_group(db: Session, group_id: int) -> Group:
    group = db.get(Group, group_id)
    if group is None:
        raise NotFoundError("Group not found")
    return group


def ensure_parent(db: Session, parent_id: int | None, current_id: int | None = None) -> Group | None:
    if parent_id is None:
        return None
    parent = get_group(db, parent_id)
    seen: set[int] = set()
    cursor: Group | None = parent
    while cursor is not None:
        if cursor.id in seen or cursor.id == current_id:
            raise ConflictError("A group cannot be its own ancestor")
        seen.add(cursor.id)
        cursor = cursor.parent
    return parent


def list_groups(db: Session) -> list[Group]:
    return list(db.scalars(select(Group).order_by(Group.name, Group.id)).all())


def create_group(db: Session, payload: GroupCreate) -> Group:
    ensure_parent(db, payload.parent_id)
    group = Group(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group_id: int, payload: GroupUpdate) -> Group:
    group = get_group(db, group_id)
    values = payload.model_dump(exclude_unset=True)
    if "parent_id" in values:
        ensure_parent(db, values["parent_id"], current_id=group_id)
    for key, value in values.items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group_id: int) -> None:
    group = get_group(db, group_id)
    if group.children or group.devices:
        raise ConflictError("Group must be empty before it can be deleted")
    db.delete(group)
    db.commit()


def group_tree(groups: list[Group]) -> list[dict[str, object]]:
    nodes = {
        group.id: {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "parent_id": group.parent_id,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "children": [],
            "device_count": len(group.devices),
        }
        for group in groups
    }
    roots: list[dict[str, object]] = []
    for group in groups:
        node = nodes[group.id]
        if group.parent_id is None:
            roots.append(node)
        elif group.parent_id in nodes:
            nodes[group.parent_id]["children"].append(node)  # type: ignore[union-attr]
    return roots
