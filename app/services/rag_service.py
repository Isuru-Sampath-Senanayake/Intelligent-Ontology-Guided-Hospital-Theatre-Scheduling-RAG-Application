from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class EvidenceChunk:
    chunk_id: str
    text: str
    tags: Dict[str, str]


class RagService:
    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._chunks: List[EvidenceChunk] = []
        self._matrix = None

    def build(self, chunks: List[EvidenceChunk]) -> None:
        self._chunks = chunks[:]
        texts = [c.text for c in self._chunks]
        self._matrix = self._vectorizer.fit_transform(texts) if texts else None

    def search(self, query: str, k: int = 6) -> List[Tuple[EvidenceChunk, float]]:
        if not self._chunks or self._matrix is None:
            return []

        qv = self._vectorizer.transform([query])
        sims = cosine_similarity(qv, self._matrix).ravel()

        scored = list(zip(self._chunks, sims))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(c, float(s)) for c, s in scored[:k]]


def build_chunks(
    surgeons: List[Dict],
    patients: List[Dict],
    operations: List[Dict],
    theatres: List[Dict],
    bookings: List[Dict],
    policies_text: Optional[str] = None,
) -> List[EvidenceChunk]:
    chunks: List[EvidenceChunk] = []

    if policies_text and policies_text.strip():
        chunks.append(
            EvidenceChunk(
                chunk_id="POLICY_RULES",
                text=policies_text.strip(),
                tags={"type": "policy"},
            )
        )

    for s in surgeons:
        chunks.append(
            EvidenceChunk(
                chunk_id=f"SURGEON_{s['surgeon_id']}",
                text=f"Surgeon {s['name']} (ID {s['surgeon_id']}) can perform operations {', '.join(s.get('can_perform', []))}. "
                     f"Specialties: {', '.join(s.get('specialties', []))}.",
                tags={"type": "surgeon", "surgeon_id": s["surgeon_id"]},
            )
        )

    for o in operations:
        chunks.append(
            EvidenceChunk(
                chunk_id=f"OP_{o['operation_id']}",
                text=f"Operation {o['name']} (ID {o['operation_id']}) requires specialty {o.get('required_specialty')}, "
                     f"equipment {', '.join(o.get('required_equipment', []))}, duration {o.get('duration_minutes')} minutes.",
                tags={"type": "operation", "operation_id": o["operation_id"]},
            )
        )

    for t in theatres:
        chunks.append(
            EvidenceChunk(
                chunk_id=f"THEATRE_{t['theatre_id']}",
                text=f"Theatre {t['name']} (ID {t['theatre_id']}) type {t.get('type')}, equipment {', '.join(t.get('equipment', []))}.",
                tags={"type": "theatre", "theatre_id": t["theatre_id"]},
            )
        )

    for p in patients:
        chunks.append(
            EvidenceChunk(
                chunk_id=f"PATIENT_{p['patient_id']}",
                text=f"Patient {p['name']} (ID {p['patient_id']}) priority {p.get('priority')}.",
                tags={"type": "patient", "patient_id": p["patient_id"]},
            )
        )

    # Keep recent booking evidence only (prevents domination)
    for b in bookings[-20:]:
        chunks.append(
            EvidenceChunk(
                chunk_id=f"BOOKING_{b['booking_id']}",
                text=f"Booking {b['booking_id']} scheduled patient {b['patient_name']} with surgeon {b['surgeon_name']} "
                     f"in theatre {b['theatre_name']} from {b['start_time']} to {b['end_time']}.",
                tags={"type": "booking", "booking_id": b["booking_id"]},
            )
        )

    return chunks
