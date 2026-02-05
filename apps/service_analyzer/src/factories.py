from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from service_analyzer.src.db.repo import Repository
    from service_crawler.src.grpc.servicer import RPCServicer


def new_repository() -> "Repository":
    from service_analyzer.src.db.repo import Repository

    return Repository()


def new_rpc_servicer() -> "RPCServicer":
    from service_analyzer.src.grpc.servicer import RPCServicer

    return RPCServicer()
