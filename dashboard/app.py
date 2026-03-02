"""Streamlit dashboard for the Minions orchestrator."""

import httpx
import streamlit as st

from common.config import get_settings

settings = get_settings()
BASE_URL = settings.api_base_url

st.set_page_config(page_title="Minions Dashboard", layout="wide")
st.title("Minions Dashboard")

# --------------- Sidebar: New Task Form ---------------
with st.sidebar:
    st.header("Submit New Task")
    with st.form("new_task_form"):
        description = st.text_area("Description", placeholder="Describe the task...")
        repo = st.text_input("Repository", placeholder="owner/repo")
        submitted = st.form_submit_button("Submit Task")

    if submitted and description and repo:
        try:
            resp = httpx.post(
                f"{BASE_URL}/tasks",
                json={"description": description, "repo": repo},
            )
            resp.raise_for_status()
            data = resp.json()
            st.success(f"Task created: {data['id']}")
        except httpx.HTTPError as exc:
            st.error(f"Failed to create task: {exc}")

# --------------- Main Area: Task List ---------------
st.header("Tasks")

STATUS_EMOJI = {
    "PENDING": "🕐",
    "PREFETCHING": "📥",
    "RUNNING": "🔄",
    "TESTING": "🧪",
    "RETRYING": "🔁",
    "COMPLETED": "✅",
    "FAILED": "❌",
    "CANCELLED": "🚫",
}

try:
    resp = httpx.get(f"{BASE_URL}/tasks")
    resp.raise_for_status()
    tasks = resp.json()
except httpx.HTTPError:
    tasks = []
    st.warning("Could not fetch tasks from API.")

if not tasks:
    st.info("No tasks yet. Submit one from the sidebar.")
else:
    for task in tasks:
        emoji = STATUS_EMOJI.get(task["status"], "❓")
        col1, col2, col3 = st.columns([5, 2, 1])

        with col1:
            st.markdown(
                f"**{emoji} {task['status']}** — `{task['repo']}` — {task['description']}"
            )
            if task.get("pr_url"):
                st.markdown(f"[PR Link]({task['pr_url']})")
            st.caption(f"Retries: {task.get('retries', 0)}")

        with col2:
            st.text(str(task["id"])[:8])

        with col3:
            if task["status"] not in ("COMPLETED", "FAILED", "CANCELLED"):
                cancel_key = f"cancel_{task['id']}"
                if st.button("Cancel", key=cancel_key):
                    try:
                        cancel_resp = httpx.post(
                            f"{BASE_URL}/tasks/{task['id']}/cancel"
                        )
                        cancel_resp.raise_for_status()
                        st.rerun()
                    except httpx.HTTPError as exc:
                        st.error(f"Cancel failed: {exc}")

        # Expandable logs section
        logs = task.get("logs", [])
        with st.expander("Logs", expanded=False):
            if logs:
                for line in logs:
                    st.text(line)
            else:
                st.text("No logs yet.")

        st.divider()
