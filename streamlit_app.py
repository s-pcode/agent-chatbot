import streamlit as st
import requests
import os
import time
import random
import json
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

# Load API credentials

project_id = st.secrets.get("PROJECT_ID", os.getenv("PROJECT_ID"))
api_key    = st.secrets.get("API_KEY", os.getenv("API_KEY"))
region     = st.secrets.get("REGION", os.getenv("REGION"))
agent_id   = st.secrets.get("AGENT_ID", os.getenv("AGENT_ID"))


if not project_id or not api_key or not region or not agent_id:
    st.error("Relevance AI credentials not set in environment.")
    st.stop()

auth_token = f"{project_id}:{api_key}"
headers = {"Authorization": auth_token, "Content-Type": "application/json"}

placeholder_texts = [
    "🤖 agent alpha is thinking...",
    "🧠 processing your request with intelligence...",
    "✨ give me a second to think that through...",
    "🚀 crunching data in the alpha matrix...",
    "⏳ generating a smart response just for you..."
]

# Set page configuration
st.set_page_config(page_title="Agent Alpha Chat", page_icon="🤖")
st.title("🤖 chat with agent alpha")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Type your message"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "message": {"role": "user", "content": user_input},
        "agent_id": agent_id
    }
    if st.session_state["conversation_id"]:
        payload["conversation_id"] = st.session_state["conversation_id"]

    try:
        trigger_url = f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger"
        trigger_resp = requests.post(trigger_url, headers=headers, json=payload)
    except Exception as e:
        st.error(f"Failed to trigger agent: {e}")
        st.stop()

    if trigger_resp.status_code != 200:
        st.error(f"Agent trigger failed ({trigger_resp.status_code}): {trigger_resp.text}")
        st.stop()

    result = trigger_resp.json()
    if st.session_state["conversation_id"] is None:
        st.session_state["conversation_id"] = result.get("conversation_id") or result.get("job_info", {}).get("conversation_id")

    studio_id = result["job_info"]["studio_id"]
    job_id = result["job_info"]["job_id"]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(random.choice(placeholder_texts))

        polling_url = f"https://api-{region}.stack.tryrelevance.com/latest/studios/{studio_id}/async_poll/{job_id}"
        
        agent_reply = None
        while True:
            poll_resp = requests.get(polling_url, headers=headers)
            if poll_resp.status_code != 200:
                st.error(f"Polling failed ({poll_resp.status_code}): {poll_resp.text}")
                break

            status = poll_resp.json()
            if any(upd.get("type") == "chain-success" for upd in status.get("updates", [])):
                list_url = f"https://api-{region}.stack.tryrelevance.com/latest/knowledge/list"
                list_payload = {
                    "knowledge_set": st.session_state["conversation_id"],
                    "page_size": 5,
                    "sort": [{"insert_date_": "desc"}]
                }
                list_resp = requests.post(list_url, headers=headers, json=list_payload)
                if list_resp.status_code == 200:
                    results = list_resp.json().get("results", [])
                    if (
                        len(results) > 2 and 
                        "chain_config" in results[-2]["data"]["message"] and 
                        results[-2]["data"]["message"]["chain_config"].get("title") == "Aplha 30/7"
                    ):
                        item = results[1]
                        msg_data = item.get("data", {}).get("message", {}).get("action_output", {}).get("python_transformed", {})
                        # if msg_data.get("role") == "action-response":
                        agent_reply = msg_data.get("chart_data")
                    else:
                        for item in results:
                            msg_data = item.get("data", {}).get("message", {})
                            if msg_data.get("role") == "agent":
                                agent_reply_raw = msg_data.get("content")
                                print(agent_reply_raw,type(agent_reply_raw))
                                try:
                                    agent_reply = json.loads(agent_reply_raw)
                                    print(agent_reply)
                                except Exception:
                                    print(f"Failed to parse JSON: {agent_reply_raw}")
                                    agent_reply = agent_reply_raw  # fallback to raw string if not JSON
                                break
                break
            time.sleep(1)

        if agent_reply is None:
            agent_reply = "_*(Agent response not found)*_"

        # Try to directly render if it's already a plotly figure (Relevance AI returns serialized plotly object)
        try:
            print(agent_reply)
            if isinstance(agent_reply, list):
                fig = go.Figure()
                for token in agent_reply:
                    normalized_y = [(price / token["y"][0]) * 100 for price in token["y"]]
                    fig.add_trace(go.Scatter(
                        x=token["x"],
                        y=normalized_y,
                        mode="lines+markers",
                        name=token["symbol"]
                    ))
                fig.update_layout(
                    title="📈 Token Price Trends (7-day)",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)"
                )
                placeholder.plotly_chart(fig, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": "📊 Chart rendered successfully!"})
            else:
                placeholder.markdown(agent_reply)
                st.session_state.messages.append({"role": "assistant", "content": agent_reply})
        except Exception as e:
            placeholder.markdown(f"⚠️ Failed to render chart: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Failed to render chart: {e}"})