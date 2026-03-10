"""Knowledge router — query knowledge atoms."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from agentml.runtime.lab import LabEnvironment

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _get_lab(request: Request) -> LabEnvironment:
    return request.app.state.lab


class KnowledgeResponse(BaseModel):
    """API response for a knowledge atom."""

    id: str
    context: str
    claim: str
    action: str
    confidence: float
    evidence_ids: list[str] = []


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge(request: Request) -> list[KnowledgeResponse]:
    """List all knowledge atoms."""
    lab = _get_lab(request)
    atoms = await lab.memory_store.list()
    return [
        KnowledgeResponse(
            id=atom.id,
            context=atom.context,
            claim=atom.claim,
            action=atom.action,
            confidence=atom.confidence,
            evidence_ids=atom.evidence_ids,
        )
        for atom in atoms
    ]


@router.get("/relevant", response_model=list[KnowledgeResponse])
async def search_knowledge(
    request: Request, query: str = "", limit: int = 10
) -> list[KnowledgeResponse]:
    """Search for relevant knowledge atoms."""
    lab = _get_lab(request)
    atoms = await lab.memory_store.search(query, limit=limit)
    return [
        KnowledgeResponse(
            id=atom.id,
            context=atom.context,
            claim=atom.claim,
            action=atom.action,
            confidence=atom.confidence,
            evidence_ids=atom.evidence_ids,
        )
        for atom in atoms
    ]
