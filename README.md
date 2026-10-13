# ResumeLens 📄🔍

## Overview
**ResumeLens** is an automated resume parsing, normalization, and evaluation application designed to streamline talent assessment. The system ingests raw candidate resumes, extracts core technical skills, normalizes spelling and formatting variations using formal models, and rigorously evaluates candidates against predefined career profiles to determine their qualification status.

---

## Pipeline Modules
The application processes data through a sequential 6-stage pipeline:

1. **Ingestion**: Accepts and parses raw resume files in multiple formats (`.txt`, `.md`, `.docx`, `.pdf`).
2. **Extraction**: Identifies and extracts key components, including contact details, education, experience, certifications, and technical skills.
3. **Normalization (FST)**: Standardizes inconsistent skill variants (e.g., `React.js`, `React-js`, `REACT JS` *to* `REACT`) using a 3-tier Finite State Transducer architecture (Stripping, Case Folding, and Token Mapping).
4. **Projection**: Sorts and filters the normalized skills into a canonical, strictly increasing sequence that matches a profile's defined vocabulary.
5. **Classification (DFA)**: Evaluates the candidate against specific target profiles (such as *Full Stack Developer*, *Machine Learning Engineer*, *Cloud Engineer*, or *Data Analyst*) using a Deterministic Finite Automaton governed by group rules (`REQUIRED`, `ANY_OF`, and `OPTIONAL`).
6. **DSL (Domain Specific Language)**: Generates a clean, structured text representation of the evaluation result, capturing candidate metadata and profile status.

---

## Team Members
* **Alejandro Murillo**
* **Isabella Candado**

---

## Tech Stack
* **Core Language:** Python 3.9+
* **Web Interface:** Streamlit
* **Automata & Transducers:** `pyformlang`
* **Development Environment:** PyCharm (JetBrains)

---

## How to Use
No local installation or setup is required to test the application. Simply access the live deployment:

👉 **[ia-resumelens.streamlit.app](https://ia-resumelens.streamlit.app)**

Upload any candidate resume file –or the ones inside `test_files`– to view real-time extraction, normalization, and profile evaluation results.

---
Thank you for exploring **ResumeLens**! This project bridges formal language theory (FSTs and DFAs) with practical recruitment automation. If you have any feedback or suggestions, feel free to reach out.
