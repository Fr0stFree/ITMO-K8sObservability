from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service_analyzer.src.db.repo import AnalyzerRepository


def new_repository() -> "AnalyzerRepository":
    from service_analyzer.src.db.repo import AnalyzerRepository

    return AnalyzerRepository()
