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
st.subheader(":robot_face: aarnâ’s DeFi agent >> â_TARS >> tokenized autonomous reinforcement sentience")
st.text("â_TARS is sentience for DeFi — your autonomous strategist built on reinforcement learning, protocol intuition, and deep vault wisdom.")
st.divider()
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
    ":sparkles: hold tight, decoding aarnâ data...",
    ":rocket: firing up AI engines...",
    ":hourglass_flowing_sand: generating a smart response just for you..."
]

custom_colors = ["#008080", "#006666","#1AD5C7", "#004C4C", "#66B2B2", "#B2D8D8"]

# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
# --- Quick Prompts ---
st.markdown("**Quick Prompts**")
cols = st.columns(2)
quick_prompts = [
    "what does aarna do?",
    "what is alpha 30/7 model?",
    "get vault recommendation",
    "what are âtv vaults?"
]
for i, q in enumerate(quick_prompts):
    if cols[i % 2].button(q, key=f"prompt_{i}", use_container_width=True):
        st.session_state["user_input"] = q
# --- Chat Input ---
user_input = st.chat_input("Type your message")
if user_input:
    st.session_state["user_input"] = user_input
# --- Handle Vault Quiz ---
if "user_input" in st.session_state and "get vault recommendation" in st.session_state["user_input"].lower():
    st.session_state["pending_form"] = True
    # st.session_state.messages.append({"role": "user", "content": st.session_state["user_input"]})
    del st.session_state["user_input"]
if st.session_state.get("pending_form"):
    with st.form("vault_quiz_form"):
        q1 = st.radio(
            ":one: what's your investing experience level?",
            ["I'm new to investing", "I've dabbled a bit", "I actively manage my investments"],
            key="q1"
        )

        q2 = st.radio(
            ":two: how do you typically feel about risk?",
            ["I avoid it — I prefer stability", "I'm okay with some risk for better returns", "I seek high risk for high reward"],
            key="q2"
        )

        q3 = st.radio(
            ":three: what's your primary investment goal?",
            ["Protect my capital", "Grow steadily over time", "Maximize gains even if it’s volatile"],
            key="q3"
        )

        q4 = st.radio(
            ":four: how familiar are you with crypto and DeFi strategies?",
            ["Very little — I just want exposure", "I understand basic crypto investing", "I'm confident and use DeFi protocols actively"],
            key="q4"
        )

        submit = st.form_submit_button("get recommendation")
    if submit:
        score_map = {
            "I'm new to investing": 1,
            "I've dabbled a bit": 2,
            "I actively manage my investments": 3,
            
            "I avoid it — I prefer stability": 1,
            "I'm okay with some risk for better returns": 2,
            "I seek high risk for high reward": 3,
            
            "Protect my capital": 1,
            "Grow steadily over time": 2,
            "Maximize gains even if it’s volatile": 3,
            
            "Very little — I just want exposure": 1,
            "I understand basic crypto investing": 2,
            "I'm confident and use DeFi protocols actively": 3
        }

        avg = sum([
            score_map[st.session_state["q1"]],
            score_map[st.session_state["q2"]],
            score_map[st.session_state["q3"]],
            score_map[st.session_state["q4"]]
        ]) / 4
        vault_map = {
            "âtv111": {
                "label": ":shield: âtv111 (Dual Layer Yield Vault)",
                "desc": "Earn passive yield on USDC with dynamic allocation and incentive-driven staking. Perfect for conservative investors seeking minimal risk."
            },
            "âtv802": {
                "label": ":brain: âtv802 (AI Quant Vault)",
                "desc": "Powered by the Alpha 30/7 AI model, this vault seeks consistent crypto alpha with risk-managed rebalancing every week."
            },
            "âtv808": {
                "label": ":rocket: âtv808 (Asymmetric Alpha Vault)",
                "desc": "Targets deep drawdowns with high rebound potential. Built for aggressive investors aiming for asymmetric upside."
            }
        }
        if avg <= 1.5:
            selected = "âtv111"
        elif avg <= 2.2:
            selected = "âtv808"
        else:
            selected = "âtv802"
        vault_info = vault_map[selected]
        recommendation = f"Based on your inputs, âTARS recommends:\n\n**{vault_info['label']}**\n\n{vault_info['desc']}"
        st.success(recommendation)
        st.markdown(f"[👉 Click here to explore this vault](https://aarna.ai/vaults?productId={selected[3:]})", unsafe_allow_html=True)
        # recommendation = f"Based on your inputs, we recommend: **{vault}**"
        # st.success(recommendation)
        # st.button(f'Click here to know more about{vault}')
        # st.session_state.messages.append({"role": "assistant", "content": recommendation})
        # st.session_state.messages.append({"role": "assistant", "content": ":robot_face: Thanks! I'll use this info to improve future suggestions."})
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
                # write the response to a file
                # with open("response.json", "w") as f:
                #     json.dump(list_resp.json(), f, indent=4)
                # for item in list_resp.json().get("results", []):
                if list_resp.json().get("results", []):
                    # _item = list_resp.json()["results"][0]
                    if list_resp.json()["results"][1].get("data", {}).get("message", {}).get("action_output").get("transformed",{}).get("chart_data",{}) == {}:
                        item = list_resp.json()["results"][0]
                        msg = item.get("data", {}).get("message", {})
                        if msg.get("role") == "agent":
                            try:
                                reply = json.loads(msg["content"])
                            except:
                                reply = msg["content"]
                    else:
                        item = list_resp.json()["results"][1]
                        msg = item.get("data", {}).get("message", {})
                        reply = msg.get("action_output", {}).get("transformed",{}).get("chart_data",{})

                    
            # Render the final result
        if isinstance(reply, list) and all("x" in d and "y" in d for d in reply):
            fig = go.Figure()

            for idx, token in enumerate(reply):
                symbol = token.get("symbol", "Token")
                x_vals = token["x"]
                y_vals = token["y"]

                # Compute % change
                pct_changes = []
                prev = None
                for price in y_vals:
                    if prev is None:
                        pct_changes.append(0.0)
                    else:
                        pct_changes.append(((price - prev) / prev) * 100)
                    prev = y_vals[0]

                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=pct_changes,
                    mode="lines",
                    name=symbol,
                    line=dict(color=custom_colors[idx % len(custom_colors)])
                ))

            # Add horizontal dashed line at +5%
            fig.update_layout(
            shapes=[
                dict(
                    type="line",
                    xref="paper", x0=0, x1=1,
                    yref="y", y0=5, y1=5,
                    line=dict(color="teal", width=2, dash="dot")
                )
            ],
            annotations=[
                dict(
                    x=0, y=6,
                    xref="paper", yref="y",
                    text="🎯 30/7 model target",
                    showarrow=False,
                    font=dict(color="#1AD5C7", size=12),
                    bgcolor="rgba(0,0,0,0)",
                    xanchor="left"
                )
            ],
             title="📈 % Price Change per Token",
                xaxis_title="Date",
                yaxis_title="% Price Change",
                yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray'),
                template="plotly_dark",
                xaxis=dict(
                gridcolor='rgba(255,255,255,0.05)'
                ),
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
            )

            placeholder.plotly_chart(fig, use_container_width=True)

        elif isinstance(reply, str):
            placeholder.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        else:
            placeholder.markdown("_:robot_face: Agent responded with unsupported format._")
            st.session_state.messages.append({"role": "assistant", "content": ":robot_face: Agent responded with unsupported format."})