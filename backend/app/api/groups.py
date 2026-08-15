from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.groups import GroupCreate, GroupRead, GroupTree, GroupUpdate
from app.schemas.topology import TopologyDiscoveryResponse, TopologyEdge, TopologyNode, TopologyResponse
from app.services.cisco import CiscoConnectionService
from app.services.errors import ConflictError, NotFoundError
from app.services.groups import service
from app.services.topology import discover_group, normalize_hostname, topology_for_group

from app.api.dependencies import require_authenticated

router = APIRouter(prefix="/groups", tags=["groups"], dependencies=[Depends(require_authenticated)])
cisco_service = CiscoConnectionService()


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


def topology_response(db: Session, group_id: int) -> TopologyResponse:
    nodes, links = topology_for_group(db, group_id)
    node_models = [TopologyNode(id=node.id, label=node.label, hostname=node.hostname, managed=node.managed, device_id=node.device_id) for node in nodes]
    edges: list[TopologyEdge] = []
    for link in links:
        target = f"device:{link.destination_device_id}" if link.destination_device_id else f"unmanaged:{normalize_hostname(link.destination_hostname)}"
        edges.append(TopologyEdge(id=f"link:{link.id}", source=f"device:{link.source_device_id}", target=target, source_interface=link.source_interface, destination_interface=link.destination_interface, protocol=link.discovery_protocol, discovered_at=link.last_discovered_at))
    return TopologyResponse(group_id=group_id, nodes=node_models, edges=edges)


@router.get("/{group_id}/topology", response_model=TopologyResponse)
def get_topology(group_id: int, db: Session = Depends(get_db)) -> TopologyResponse:
    try:
        return topology_response(db, group_id)
    except NotFoundError as error:
        raise service_error(error) from error


@router.post("/{group_id}/topology/discover", response_model=TopologyDiscoveryResponse)
def discover_topology(group_id: int, db: Session = Depends(get_db)) -> TopologyDiscoveryResponse:
    try:
        refreshed_devices, skipped_devices = discover_group(db, group_id, cisco_service)
        result = topology_response(db, group_id)
        return TopologyDiscoveryResponse(**result.model_dump(), refreshed_devices=refreshed_devices, skipped_devices=skipped_devices)
    except NotFoundError as error:
        raise service_error(error) from error
