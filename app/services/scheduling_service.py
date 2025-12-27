from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple


DAY_MAP = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


@dataclass(frozen=True)
class CandidateDecision:
    approved: bool
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    surgeon_id: str
    theatre_id: str
    reasons: List[str]


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _parse_hhmm(hhmm: str) -> time:
    hh, mm = hhmm.split(":")
    return time(hour=int(hh), minute=int(mm))


def _is_within_windows(dt_start: datetime, dt_end: datetime, windows: List[Dict[str, str]]) -> bool:
    day = DAY_MAP[dt_start.weekday()]
    if DAY_MAP[dt_end.weekday()] != day:
        return False

    for w in windows:
        if w["day"] != day:
            continue
        w_start = _parse_hhmm(w["start"])
        w_end = _parse_hhmm(w["end"])
        if w_start <= dt_start.time() and dt_end.time() <= w_end:
            return True
    return False


def generate_candidate_starts(
    window_start: datetime,
    window_end: datetime,
    step_minutes: int,
) -> List[datetime]:
    starts: List[datetime] = []
    cursor = window_start

    if window_end <= window_start:
        return starts

    step = timedelta(minutes=step_minutes)
    while cursor + step <= window_end + timedelta(seconds=1):
        starts.append(cursor)
        cursor += step

    return starts


def find_slot_asap(
    window_start: datetime,
    window_end: datetime,
    step_minutes: int,
    duration_minutes: int,
    surgeon: Dict,
    theatre: Dict,
    bookings: List[Dict],
) -> CandidateDecision:
    reasons: List[str] = []
    duration = timedelta(minutes=duration_minutes)

    if window_end <= window_start:
        return CandidateDecision(False, None, None, surgeon["surgeon_id"], theatre["theatre_id"], ["Invalid time window."])

    candidate_starts = generate_candidate_starts(window_start, window_end, step_minutes)

    for start_dt in candidate_starts:
        end_dt = start_dt + duration

        if end_dt > window_end:
            continue

        if not _is_within_windows(start_dt, end_dt, surgeon.get("availability", [])):
            continue

        if not _is_within_windows(start_dt, end_dt, theatre.get("availability", [])):
            continue

        conflict = False
        for b in bookings:
            b_start = datetime.fromisoformat(b["start_time"])
            b_end = datetime.fromisoformat(b["end_time"])

            if b["surgeon_id"] == surgeon["surgeon_id"] and _overlaps(start_dt, end_dt, b_start, b_end):
                conflict = True
                break

            if b["theatre_id"] == theatre["theatre_id"] and _overlaps(start_dt, end_dt, b_start, b_end):
                conflict = True
                break

        if conflict:
            continue

        return CandidateDecision(True, start_dt, end_dt, surgeon["surgeon_id"], theatre["theatre_id"], [])

    reasons.append("No available slot found within the requested window.")
    return CandidateDecision(False, None, None, surgeon["surgeon_id"], theatre["theatre_id"], reasons)


def validate_fixed_slot(
    start_dt: datetime,
    duration_minutes: int,
    surgeon: Dict,
    theatre: Dict,
    bookings: List[Dict],
) -> CandidateDecision:
    reasons: List[str] = []
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    if not _is_within_windows(start_dt, end_dt, surgeon.get("availability", [])):
        reasons.append("Surgeon not available in that time range.")

    if not _is_within_windows(start_dt, end_dt, theatre.get("availability", [])):
        reasons.append("Theatre not available in that time range.")

    for b in bookings:
        b_start = datetime.fromisoformat(b["start_time"])
        b_end = datetime.fromisoformat(b["end_time"])

        if b["surgeon_id"] == surgeon["surgeon_id"] and _overlaps(start_dt, end_dt, b_start, b_end):
            reasons.append("Surgeon has a conflicting booking.")
            break

    for b in bookings:
        b_start = datetime.fromisoformat(b["start_time"])
        b_end = datetime.fromisoformat(b["end_time"])

        if b["theatre_id"] == theatre["theatre_id"] and _overlaps(start_dt, end_dt, b_start, b_end):
            reasons.append("Theatre has a conflicting booking.")
            break

    approved = len(reasons) == 0
    return CandidateDecision(approved, start_dt if approved else None, end_dt if approved else None, surgeon["surgeon_id"], theatre["theatre_id"], reasons)
