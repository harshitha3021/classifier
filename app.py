import json
from typing import Any, Dict, List

import streamlit as st

from classifier import classify_po

st.set_page_config(page_title="PO Category Classifier", layout="wide")

st.title("PO L1-L2-L3 Classifier")
st.caption("Classify purchase order text into L1/L2/L3 categories.")

EXAMPLE_DESCRIPTION = "Purchase of 50 office chairs with ergonomic support for HQ."
EXAMPLE_SUPPLIER = "Acme Office Supplies"

if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "po_description" not in st.session_state:
    st.session_state.po_description = ""
if "supplier" not in st.session_state:
    st.session_state.supplier = ""


@st.cache_data(show_spinner=False)
def _classify_cached(description: str, supplier_name: str) -> str:
    return classify_po(description, supplier_name)


def _add_history(entry: Dict[str, Any]) -> None:
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:3]


left, right = st.columns([2, 3], gap="large")

with left:
    st.subheader("Input")
    st.write("Tip: include item, quantity, and use-case for best results.")
    st.session_state.po_description = st.text_area(
        "PO Description",
        value=st.session_state.po_description,
        height=140,
        help="Example: 'Purchase of 50 office chairs with ergonomic support for HQ.'",
    )
    st.session_state.supplier = st.text_input(
        "Supplier (optional)",
        value=st.session_state.supplier,
        help="Vendor or supplier name, if known.",
    )

    cols = st.columns(2)
    with cols[0]:
        if st.button("Use Example"):
            st.session_state.po_description = EXAMPLE_DESCRIPTION
            st.session_state.supplier = EXAMPLE_SUPPLIER
    with cols[1]:
        if st.button("Clear"):
            st.session_state.po_description = ""
            st.session_state.supplier = ""
            st.session_state.last_result = None

    can_classify = bool(st.session_state.po_description.strip())
    if st.button("Classify", disabled=not can_classify):
        with st.spinner("Classifying..."):
            try:
                result = _classify_cached(
                    st.session_state.po_description, st.session_state.supplier
                )
            except Exception as exc:
                st.error("Classification failed. Please try again.")
                st.exception(exc)
            else:
                st.session_state.last_result = result
                _add_history(
                    {
                        "description": st.session_state.po_description,
                        "supplier": st.session_state.supplier,
                        "result": result,
                    }
                )

with right:
    st.subheader("Result")
    if st.session_state.last_result:
        try:
            parsed: Dict[str, Any] = json.loads(st.session_state.last_result)
            l1 = parsed.get("l1")
            l2 = parsed.get("l2")
            l3 = parsed.get("l3")
            summary_parts: List[str] = [p for p in [l1, l2, l3] if p]
            if summary_parts:
                st.success(" > ".join(summary_parts))
            st.json(parsed)
        except Exception:
            st.error("Invalid model response. Showing raw output.")
            st.text(st.session_state.last_result)
    else:
        st.info("Run a classification to see results here.")

    if st.session_state.history:
        st.subheader("Recent History")
        for entry in st.session_state.history:
            st.write(f"- {entry['description'][:80]}")
            if entry["supplier"]:
                st.caption(f"Supplier: {entry['supplier']}")
