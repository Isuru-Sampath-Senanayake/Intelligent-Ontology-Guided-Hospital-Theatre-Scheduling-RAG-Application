# INTELLIGENT HOSPITAL THEATRE SCHEDULING SYSTEM

This project implements an intelligent hospital theatre scheduling support system
using Streamlit, a local Ollama LLM, Retrieval Augmented Generation (RAG),
and an OWL ontology to minimize hallucinations and ensure explainable decisions.

The system reasons over surgeons, patients, theatres, operations, and time slots,
and provides grounded scheduling decisions with evidence-based explanations.

---

## SYSTEM ARCHITECTURE (HIGH LEVEL)

User Input  
→ Ontology Semantic Filter (OWL)  
→ Scheduling Engine (time + conflict checks)  
→ RAG Evidence Retrieval  
→ Ollama LLM (explanation only)  
→ Result Display

Important:  
- The ontology enforces hard constraints  
- The LLM NEVER makes scheduling decisions  
- The LLM only explains system decisions using retrieved evidence

---

## PREREQUISITES

**Operating System:**  
- Linux (tested on Ubuntu-based systems)

**Required Software:**  
- Python 3.12+  
- Git  
- Ollama (local LLM runtime)  
- Protégé (for viewing ontology)

---

## INSTALL OLLAMA

Install Ollama:
```bash
sudo snap install ollama
```

Verify installation:
```bash
ollama --version
```

Pull the required model:
```bash
ollama pull phi3:mini
```

Verify model:
```bash
ollama list
```

---

## PROJECT SETUP

1. Clone the repository
```bash
git clone <your-github-repository-url>
cd hospital-ontology-rag
```

2. Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Upgrade pip
```bash
pip install --upgrade pip
```

4. Install required Python packages
```bash
pip install streamlit rdflib scikit-learn requests
```

---

## PROJECT STRUCTURE

```
hospital-ontology-rag/
│
├── app/
│   ├── Home.py
│   ├── pages/
│   │   ├── 1_Dashboard.py
│   │   └── 2_Create_Booking.py
│   └── services/
│       ├── scheduling_service.py
│       ├── ontology_service.py
│       ├── rag_service.py
│       └── llm_service.py
│
├── data/
│   ├── surgeons.json
│   ├── patients.json
│   ├── operations.json
│   ├── theatres.json
│   ├── bookings.json
│   └── policies.txt
│
├── ontology/
│   └── hospital.owl
│
├── docs/
│   └── screenshots/
│
├── README.txt
└── .venv/
```

---

## RUNNING THE APPLICATION

Always run Streamlit using Python module mode:

```bash
python -m streamlit run app/Home.py
```

Application URL:  
http://localhost:8501

---

## USING THE SYSTEM

1. Open "Create Booking" page  
2. Select patient, operation, surgeon, and theatre  
3. Choose scheduling mode:
   - Fixed time
   - ASAP within range
4. Click "Check and Schedule"

The system will:  
- Validate rules using ontology and scheduling logic  
- Retrieve relevant evidence using RAG  
- Generate a grounded explanation using Ollama

---

## EVALUATION MODE (COURSEWORK REQUIREMENT)

The system supports evaluation by comparing:

- Ontology ON  → semantic filter enabled  
- Ontology OFF → baseline JSON-only validation

To reset bookings before each evaluation run:

```bash
echo "[]" > data/bookings.json
```

Use identical test scenarios in both modes to compare results
and demonstrate hallucination mitigation.

---

## ONTOLOGY

Ontology file location:  
ontology/hospital.owl

Open using Protégé to view:  
- Classes  
- Object properties  
- Individuals  
- Relationships

The ontology represents authoritative domain knowledge.

---

## NOTES

- All data is stored in JSON files  
- No external database is required  
- All decisions are deterministic  
- LLM output is constrained using retrieved evidence  
- This system is designed for academic coursework purposes

---

END OF FILE
------------------------------------------------------------
