import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st

from app.services.scheduling_service import find_slot_asap, validate_fixed_slot
from app.services.ontology_service import OntologyConfig, OntologyService
from app.services.rag_service import RagService, build_chunks

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SURGEONS_FILE = DATA_DIR / "surgeons.json"
PATIENTS_FILE = DATA_DIR / "patients.json"
OPERATIONS_FILE = DATA_DIR / "operations.json"
THEATRES_FILE = DATA_DIR / "theatres.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"

ONTOLOGY_PATH = Path(__file__).resolve().parents[2] / "ontology" / "hospital.owl"
BASE_IRI = "http://www.semanticweb.org/hospital"

ontology = OntologyService(OntologyConfig(ontology_path=ONTOLOGY_PATH, base_iri=BASE_IRI))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_dt(date_value, time_str: str) -> datetime:
    hh, mm = time_str.split(":")
    return datetime(date_value.year, date_value.month, date_value.day, int(hh), int(mm))


st.set_page_config(page_title="Create Booking", layout="wide")
st.title("Create Booking")

surgeons = load_json(SURGEONS_FILE)
patients = load_json(PATIENTS_FILE)
operations = load_json(OPERATIONS_FILE)
theatres = load_json(THEATRES_FILE)
bookings = load_json(BOOKINGS_FILE)

surgeon_by_name = {s["name"]: s for s in surgeons}
patient_by_name = {p["name"]: p for p in patients}
operation_by_name = {o["name"]: o for o in operations}
theatre_by_name = {t["name"]: t for t in theatres}

TIME_OPTIONS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
]

col1, col2, col3 = st.columns(3)

with col1:
    patient_name = st.selectbox("Patient", sorted(patient_by_name.keys()))
    operation_name = st.selectbox("Operation", sorted(operation_by_name.keys()))

with col2:
    surgeon_name = st.selectbox("Preferred Surgeon", sorted(surgeon_by_name.keys()))
    theatre_name = st.selectbox("Preferred Theatre", sorted(theatre_by_name.keys()))

with col3:
    mode = st.radio("Scheduling mode", ["Fixed time", "ASAP within range"], horizontal=True)
    booking_date = st.date_input("Start date", value=datetime.now().date() + timedelta(days=1))

    if mode == "Fixed time":
        start_time = st.selectbox("Start time", TIME_OPTIONS)
        days_range = None
    else:
        start_time = None
        days_range = st.selectbox("Search window (days)", [3, 7, 14], index=2)

submit = st.button("Check and Schedule", type="primary")

if submit:
    patient = patient_by_name[patient_name]
    operation = operation_by_name[operation_name]
    surgeon = surgeon_by_name[surgeon_name]
    theatre = theatre_by_name[theatre_name]

    reasons = []

    if not ontology.surgeon_can_perform(surgeon["surgeon_id"], operation["operation_id"]):
        reasons.append("Surgeon is not qualified for the selected operation (ontology rule).")

    required_eq = set(ontology.required_equipment(operation["operation_id"]))
    available_eq = set(theatre.get("equipment", []))
    if not required_eq.issubset(available_eq):
        missing = sorted(required_eq - available_eq)
        reasons.append(f"Theatre is missing required equipment: {', '.join(missing)}")

    if theatre.get("type") != operation.get("required_specialty"):
        reasons.append("Theatre type is not compatible with the operation specialty.")

    duration_minutes = int(operation["duration_minutes"])
    step_minutes = 30

    decision = None
    if not reasons:
        if mode == "Fixed time":
            start_dt = parse_dt(booking_date, start_time)
            decision = validate_fixed_slot(
                start_dt=start_dt,
                duration_minutes=duration_minutes,
                surgeon=surgeon,
                theatre=theatre,
                bookings=bookings,
            )
        else:
            window_start = datetime(booking_date.year, booking_date.month, booking_date.day, 8, 0)
            window_end = window_start + timedelta(days=int(days_range))
            decision = find_slot_asap(
                window_start=window_start,
                window_end=window_end,
                step_minutes=step_minutes,
                duration_minutes=duration_minutes,
                surgeon=surgeon,
                theatre=theatre,
                bookings=bookings,
            )

        if not decision.approved:
            reasons.extend(decision.reasons)

    # Build RAG evidence (after we know the outcome)
    rag = RagService()
    chunks = build_chunks(surgeons, patients, operations, theatres, bookings)
    rag.build(chunks)

    query_text = f"{patient['name']} {operation['name']} {surgeon['name']} {theatre['name']} {mode}"
    results = rag.search(query_text, k=6)

    st.subheader("Retrieved Evidence")
    if not results:
        st.info("No evidence retrieved.")
    else:
        for c, s in results:
            st.write(f"- {c.chunk_id} (score {s:.3f}): {c.text}")

    st.subheader("Decision")
    if reasons:
        st.error("Rejected")
        for r in reasons:
            st.write(f"- {r}")
    else:
        booking = {
            "booking_id": f"B{len(bookings) + 1:04d}",
            "patient_id": patient["patient_id"],
            "patient_name": patient["name"],
            "operation_id": operation["operation_id"],
            "operation_name": operation["name"],
            "surgeon_id": surgeon["surgeon_id"],
            "surgeon_name": surgeon["name"],
            "theatre_id": theatre["theatre_id"],
            "theatre_name": theatre["name"],
            "start_time": decision.start_time.isoformat(timespec="minutes"),
            "end_time": decision.end_time.isoformat(timespec="minutes"),
        }

        bookings.append(booking)
        save_json(BOOKINGS_FILE, bookings)

        st.success("Approved and saved to bookings.json")
        st.json(booking)
