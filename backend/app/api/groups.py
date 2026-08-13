from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.groups import GroupCreate, GroupRead, GroupTree, GroupUpdate
from app.services.errors import ConflictError, NotFoundError
from app.services.groups import service

router = APIRouter(prefix="/groups", tags=["groups"])


def service_error(error: NotFoundError | ConflictError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if isinstance(error, NotFoundError) else status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=str(error))


@router.get("", response_model=list[GroupRead])
def list_groups(db: Session = Depends(get_db)) -> list[GroupRead]:
    return service.list_groups(db)


@router.get("/tree", response_model=list[GroupTree])
def get_group_tree(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return service.group_tree(service.list_groups(db))


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, db: Session = Depends(get_db)) -> GroupRead:
    try:
        return service.create_group(db, payload)
    except (NotFoundError, ConflictError) as error:
        raise service_error(error) from error


@router.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, db: Session = Depends(get_db)) -> GroupRead:
    try:
        return service.get_group(db, group_id)
    except NotFoundError as error:
        raise service_error(error) from error


@router.patch("/{group_id}", response_model=GroupRead)
def update_group(group_id: int, payload: GroupUpdate, db: Session = Depends(get_db)) -> GroupRead:
    try:
        return service.update_group(db, group_id, payload)
    except (NotFoundError, ConflictError) as error:
        raise service_error(error) from error


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        service.delete_group(db, group_id)
    except (NotFoundError, ConflictError) as error:
        raise service_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
