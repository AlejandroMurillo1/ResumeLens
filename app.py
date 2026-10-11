import tempfile
from pathlib import Path

import streamlit as st

from src.bootstrap import build_resources
from src.core.dsl import to_dsl, render_markdown
from src.core.models.models import DSLError

st.set_page_config(page_title="ResumeLens", layout="centered")
st.title("ResumeLens")

resources = build_resources()
pipeline = resources.pipeline
dsl_validator = resources.dsl_validator

tab_analyze, tab_validate = st.tabs(["Analyze résumé", "Validate DSL"])

# --- Tab 1: run the full pipeline on a résumé ---------------------------
with tab_analyze:
    st.write("Upload a résumé, or paste its text below, then click Analyze.")
    uploaded_file = st.file_uploader("Résumé file", type=["txt", "md", "docx", "pdf"])
    pasted_text = st.text_area("...or paste résumé text", height=200)

    if st.button("Analyze", type="primary"):
        path = None
        if uploaded_file is not None:
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(uploaded_file.getvalue())
                path = Path(f.name)
        elif pasted_text.strip():
            with tempfile.NamedTemporaryFile(
                suffix=".txt", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(pasted_text)
                path = Path(f.name)
        else:
            st.warning("Upload a file or paste some text first.")

        if path is not None:
            report = pipeline.process(path)

            st.subheader("Contact")
            st.write(f"**{report.contact.name}** — {report.contact.email} — {report.contact.phone}")

            st.subheader("Recognized skills")
            st.write(", ".join(report.skills) or "_none_")
            if report.unrecognized_skills:
                st.caption("Unrecognized: " + ", ".join(report.unrecognized_skills))

            st.subheader("Profile matches")
            for c in report.classifications:
                mark = "✅" if c.accepted else "❌"
                st.write(f"{mark} **{c.profile_name}** — evaluated: {list(c.sequence)}")

            st.subheader("Rendered profile (DSL → Markdown)")
            try:
                dsl_text = to_dsl(report)
                model = dsl_validator.validate(dsl_text)
                st.markdown(render_markdown(model))
                with st.expander("Raw DSL"):
                    st.code(dsl_text, language="text")
            except DSLError as e:
                st.error(f"[{e.kind.name}] {e.message} (line {e.line}, col {e.column})")

# --- Tab 2: validate a hand-written DSL document -------------------------
with tab_validate:
    st.write("Paste a `candidate { ... }` DSL document to validate it directly.")
    dsl_input = st.text_area("DSL text", height=300)

    if st.button("Validate"):
        try:
            model = dsl_validator.validate(dsl_input)
            st.success("Valid DSL.")
            st.markdown(render_markdown(model))
        except DSLError as e:
            st.error(f"[{e.kind.name}] {e.message} (line {e.line}, col {e.column})")