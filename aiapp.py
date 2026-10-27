
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st

LOG = Path("audit_logs.jsonl")

def record(event, proposal_id, details):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "proposal_id": proposal_id,
        **details,
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def read_logs():
    if not LOG.exists():
        return []
    with LOG.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

st.set_page_config(page_title="AI Approval System", page_icon="🛡️")
st.title("🛡️ AI Employee Approval System")
st.caption("Prepare a proposal → Review → Approve or reject → Audit")

if "proposals" not in st.session_state:
    st.session_state.proposals = {}

create_tab, review_tab, audit_tab = st.tabs(
    ["Create Task", "Review Proposals", "Audit Log"]
)

with create_tab:
    task = st.text_area(
        "Describe the task",
        placeholder="Draft a reminder for a client with missing documents",
    )

    if st.button("Generate Proposal", type="primary"):
        if not task.strip():
            st.warning("Enter a task first.")
        else:
            pid = str(uuid.uuid4())[:8]
            draft = (
                "DEMO DRAFT — Review before use\n\n"
                f"Task: {task.strip()}\n\n"
                "Hello,\n\n"
                "This is a friendly reminder about the pending documents. "
                "Could you please provide an update when convenient?\n\n"
                "Thank you."
            )
            st.session_state.proposals[pid] = {
                "task": task.strip(),
                "draft": draft,
                "status": "Pending",
            }
            record("created", pid, {"task": task.strip()})
            st.success(f"Proposal {pid} created. Open Review Proposals.")

with review_tab:
    if not st.session_state.proposals:
        st.info("Create a proposal first.")

    for pid, p in list(st.session_state.proposals.items()):
        with st.expander(f"{pid} — {p['status']}"):
            st.write("**Task:**", p["task"])
            edited = st.text_area(
                "Edit proposal",
                value=p["draft"],
                key=f"draft_{pid}",
                disabled=p["status"] != "Pending",
            )

            if p["status"] == "Pending":
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Approve", key=f"approve_{pid}"):
                        p["draft"] = edited
                        p["status"] = "Approved"
                        record("approved", pid, {"final_draft": edited})
                        st.rerun()

                with col2:
                    if st.button("Reject", key=f"reject_{pid}"):
                        p["status"] = "Rejected"
                        record("rejected", pid, {})
                        st.rerun()

with audit_tab:
    events = read_logs()
    if events:
        st.dataframe(events, use_container_width=True)
        st.download_button(
            "Download Audit Log",
            data="\n".join(json.dumps(e) for e in events),
            file_name="audit_logs.jsonl",
            mime="application/x-ndjson",
        )
    else:
        st.info("No audit events yet.")
