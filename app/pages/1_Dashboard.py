import json
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BOOKINGS_FILE = DATA_DIR / "bookings.json"

st.set_page_config(page_title="Bookings Dashboard", layout="wide")
st.title("Bookings Dashboard")

if not BOOKINGS_FILE.exists():
    st.error("bookings.json not found.")
    st.stop()

bookings = json.loads(BOOKINGS_FILE.read_text(encoding="utf-8"))

st.write(f"Total bookings: {len(bookings)}")

if not bookings:
    st.info("No bookings yet.")
else:
    st.dataframe(bookings, use_container_width=True)
