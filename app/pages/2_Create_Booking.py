import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SURGEONS_FILE = DATA_DIR / "surgeons.json"
PATIENTS_FILE = DATA_DIR / "patients.json"
OPERATIONS_FILE = DATA_DIR / "operations.json"
THEATRES_FILE = DATA_DIR / "theatres.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_dt(date_value, time_str: str) -> datetime:
    hh, mm = time_str.split(":")
    return datetime(date_value.year, date_value.month, date_value.day, int(hh), int(mm))


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


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

with st.form("booking_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        patient_name = st.selectbox("Patient", sorted(patient_by_name.keys()))
        operation_name = st.selectbox("Operation", sorted(operation_by_name.keys()))
    with col2:
        surgeon_name = st.selectbox("Preferred Surgeon", sorted(surgeon_by_name.keys()))
        theatre_name = st.selectbox("Preferred Theatre", sorted(theatre_by_name.keys()))
    with col3:
        booking_date = st.date_input("Date", value=datetime.now().date() + timedelta(days=1))
        start_time = st.selectbox("Start time", ["08:00", "08:30", "09:00", "09:30", "10:00",
                                                "10:30", "11:00", "11:30", "12:00", "12:30",
                                                "13:00", "13:30", "14:00", "14:30", "15:00", "15:30"])

    submit = st.form_submit_button("Check and Schedule")

if submit:
    patient = patient_by_name[patient_name]
    operation = operation_by_name[operation_name]
    surgeon = surgeon_by_name[surgeon_name]
    theatre = theatre_by_name[theatre_name]

    start_dt = parse_dt(booking_date, start_time)
    end_dt = start_dt + timedelta(minutes=int(operation["duration_minutes"]))

    # Basic checks (semantic filter comes later)
    reasons = []

    if operation["operation_id"] not in surgeon.get("can_perform", []):
        reasons.append("Surgeon is not qualified for the selected operation.")

    required_eq = set(operation.get("required_equipment", []))
    available_eq = set(theatre.get("equipment", []))
    if not required_eq.issubset(available_eq):
        missing = sorted(required_eq - available_eq)
        reasons.append(f"Theatre is missing required equipment: {', '.join(missing)}")

    if theatre.get("type") != operation.get("required_specialty"):
        reasons.append("Theatre type is not compatible with the operation specialty.")

    for b in bookings:
        b_start = datetime.fromisoformat(b["start_time"])
        b_end = datetime.fromisoformat(b["end_time"])

        if b["surgeon_id"] == surgeon["surgeon_id"] and overlaps(start_dt, end_dt, b_start, b_end):
            reasons.append("Surgeon has a conflicting booking in that time range.")
            break

        if b["theatre_id"] == theatre["theatre_id"] and overlaps(start_dt, end_dt, b_start, b_end):
            reasons.append("Theatre has a conflicting booking in that time range.")
            break

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
            "start_time": start_dt.isoformat(timespec="minutes"),
            "end_time": end_dt.isoformat(timespec="minutes"),
        }

        bookings.append(booking)
        save_json(BOOKINGS_FILE, bookings)

        st.success("Approved and saved to bookings.json")
        st.json(booking)
