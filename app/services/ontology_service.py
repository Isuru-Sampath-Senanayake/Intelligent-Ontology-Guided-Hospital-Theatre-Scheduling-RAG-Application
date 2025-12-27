from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from rdflib import Graph, Namespace, URIRef


@dataclass(frozen=True)
class OntologyConfig:
    ontology_path: Path
    base_iri: str


class OntologyService:
    def __init__(self, config: OntologyConfig):
        self._g = Graph()
        self._g.parse(str(config.ontology_path))

        self._ns = Namespace(config.base_iri.rstrip("#/") + "#")
        self._can_perform = self._ns.canPerform
        self._requires_equipment = self._ns.requiresEquipment

    def _iri(self, local_name: str) -> URIRef:
        return self._ns[local_name]

    def surgeon_can_perform(self, surgeon_id: str, operation_id: str) -> bool:
        return (self._iri(surgeon_id), self._can_perform, self._iri(operation_id)) in self._g

    def required_equipment(self, operation_id: str) -> List[str]:
        op = self._iri(operation_id)
        items: Set[str] = set()
        for _, _, obj in self._g.triples((op, self._requires_equipment, None)):
            items.add(str(obj).split("#")[-1])
        return sorted(items)
