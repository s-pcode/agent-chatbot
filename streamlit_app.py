import streamlit as st
import requests
import os
import time
import random
import json
import plotly.graph_objects as go
import base64
from dotenv import load_dotenv
# --- Setup ---
load_dotenv()
st.set_page_config(page_title="Agent âTARS Chat", page_icon=":robot_face:")
st.title(":robot_face: chat with âTARS")
# --- Session State ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None
# --- Credentials ---
project_id = st.secrets.get("PROJECT_ID", os.getenv("PROJECT_ID"))
api_key = st.secrets.get("API_KEY", os.getenv("API_KEY"))
region = st.secrets.get("REGION", os.getenv("REGION"))
agent_id = st.secrets.get("AGENT_ID", os.getenv("AGENT_ID"))
if not all([project_id, api_key, region, agent_id]):
    st.error("Missing credentials.")
    st.stop()
# --- Headers ---
token = base64.b64encode(f"{project_id}:{api_key}".encode()).decode()
headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
placeholder_texts = [
    ":robot_face: âTARS is thinking...",
    ":brain: crunching crypto signals...",
    ":sparkles: hold tight, decoding DeFi data...",
    ":rocket: firing up AI engines...",
    ":hourglass_flowing_sand: generating a smart response just for you..."
]
# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
# --- Quick Prompts ---
st.markdown(":speech_bubble: **Quick Prompts**")
cols = st.columns(2)
quick_prompts = [
    "what does aarna do?",
    "what is alpha 30/7 model?",
    "Get investment advice",
    "what are the different vaults?"
]
for i, q in enumerate(quick_prompts):
    if cols[i % 2].button(q, key=f"prompt_{i}", use_container_width=True):
        st.session_state["user_input"] = q
# --- Chat Input ---
user_input = st.chat_input("Type your message")
if user_input:
    st.session_state["user_input"] = user_input
# --- Handle Vault Quiz ---
if "user_input" in st.session_state and "get investment advice" in st.session_state["user_input"].lower():
    st.session_state["pending_form"] = True
    st.session_state.messages.append({"role": "user", "content": st.session_state["user_input"]})
    del st.session_state["user_input"]
if st.session_state.get("pending_form"):
    with st.form("vault_quiz_form"):
        q1 = st.radio(":one: Experience?", ["Beginner", "Some experience", "Experienced trader"], key="q1")
        q2 = st.radio(":two: Risk comfort?", ["Not comfortable", "Somewhat okay", "Completely fine with high risk"], key="q2")
        q3 = st.radio(":three: Goal?", ["Preserve capital", "Balanced growth", "High upside"], key="q3")
        q4 = st.radio(":four: Strategy knowledge?", ["Little to no knowledge", "Basic understanding", "Well-versed"], key="q4")
        submit = st.form_submit_button("Get Recommendation")
    if submit:
        score_map = {
            "Beginner": 1, "Some experience": 2, "Experienced trader": 3,
            "Not comfortable": 1, "Somewhat okay": 2, "Completely fine with high risk": 3,
            "Preserve capital": 1, "Balanced growth": 2, "High upside": 3,
            "Little to no knowledge": 1, "Basic understanding": 2, "Well-versed": 3
        }
        avg = sum([
            score_map[st.session_state["q1"]],
            score_map[st.session_state["q2"]],
            score_map[st.session_state["q3"]],
            score_map[st.session_state["q4"]]
        ]) / 4
        vault = (
            ":shield: atv111 (Stablecoin Yield Vault)" if avg <= 1.5 else
            ":brain: atv802 (AI Quant Vault)" if avg <= 2.2 else
            ":rocket: atv808 (Asymmetric Alpha Vault)"
        )
        recommendation = f"Based on your inputs, we recommend: **{vault}**"
        st.success(recommendation)
        st.button(f'Click here to know more about{vault}')
        st.session_state.messages.append({"role": "assistant", "content": recommendation})
        st.session_state.messages.append({"role": "assistant", "content": ":robot_face: Thanks! I'll use this info to improve future suggestions."})
        st.session_state["pending_form"] = False
# --- Handle Query via Agent ---
elif "user_input" in st.session_state:
    user_prompt = st.session_state.pop("user_input")
    # Show user message live
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(random.choice(placeholder_texts))
        payload = {
            "message": {"role": "user", "content": user_prompt},
            "agent_id": agent_id
        }
        if st.session_state["conversation_id"]:
            payload["conversation_id"] = st.session_state["conversation_id"]
        try:
            trigger_url = f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger"
            trigger_resp = requests.post(trigger_url, headers=headers, json=payload)
            trigger_resp.raise_for_status()
        except Exception as e:
            placeholder.error(f":x: Failed to trigger agent: {e}")
        else:
            result = trigger_resp.json()
            if not st.session_state["conversation_id"]:
                st.session_state["conversation_id"] = result.get("conversation_id") or result.get("job_info", {}).get("conversation_id")
            studio_id = result["job_info"]["studio_id"]
            job_id = result["job_info"]["job_id"]
            polling_url = f"https://api-{region}.stack.tryrelevance.com/latest/studios/{studio_id}/async_poll/{job_id}"
            while True:
                poll_resp = requests.get(polling_url, headers=headers)
                if poll_resp.status_code != 200:
                    placeholder.error(":x: Polling failed.")
                    break
                if any(upd.get("type") == "chain-success" for upd in poll_resp.json().get("updates", [])):
                    break
                time.sleep(1)
            list_url = f"https://api-{region}.stack.tryrelevance.com/latest/knowledge/list"
            list_payload = {
                "knowledge_set": st.session_state["conversation_id"],
                "page_size": 5,
                "sort": [{"insert_date_": "desc"}]
            }
            list_resp = requests.post(list_url, headers=headers, json=list_payload)
            reply = "_:warning: Agent reply not found_"
            if list_resp.status_code == 200:
                for item in list_resp.json().get("results", []):
                    msg = item.get("data", {}).get("message", {})
                    if msg.get("role") == "agent":
                        try:
                            reply = json.loads(msg["content"])
                        except:
                            reply = msg["content"]
                        break
                    elif msg.get("role") == "action-response":
                        reply = msg.get("action_output", {}).get("python_2_transformed")
                        break
            # Render the final result
            if isinstance(reply, list) and all("x" in d and "y" in d for d in reply):
                fig = go.Figure()
                for token in reply:
                    fig.add_trace(go.Scatter(x=token["x"], y=token["y"], mode="lines+markers", name=token.get("symbol", "Token")))
                fig.update_layout(title=":chart_with_upwards_trend: Token Price Trends", xaxis_title="Date", yaxis_title="Price (USD)")
                placeholder.plotly_chart(fig, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": ":bar_chart: Chart rendered successfully!"})
            elif isinstance(reply, str):
                placeholder.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                placeholder.markdown("_:robot_face: Agent responded with unsupported format._")
                st.session_state.messages.append({"role": "assistant", "content": ":robot_face: Agent responded with unsupported format."})