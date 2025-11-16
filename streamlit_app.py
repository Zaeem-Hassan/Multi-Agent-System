import streamlit as st
import requests
import time

st.set_page_config(page_title="Multi-Agent System", layout="wide")

st.title("Multi-Agent System")

BACKEND_URL = "http://127.0.0.1:8000"

user_query = st.text_input("Ask something:")


# 🔄 Simple animated dots loading
def animated_loader(message, duration=2.5):
    placeholder = st.empty()
    dots = ["", ".", "..", "..."]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        placeholder.markdown(f"**{message}{dots[i % 4]}**")
        time.sleep(0.4)
        i += 1
    placeholder.empty()


if st.button("Run"):
    if not user_query.strip():
        st.warning("Please enter a query")
    else:

        # 🧠 Agent Thinking Steps UI
        st.write("### 🧠 Agent Thinking Steps")
        thinking_box = st.empty()

        def step(msg):
            thinking_box.markdown(
                f"""
                <div style="
                    background-color:#222;
                    padding:12px;
                    border-radius:8px;
                    border-left: 4px solid #4CAF50;
                    margin-bottom:8px;
                ">
                    <b style="color:#4CAF50;">✔</b> 
                    <span style="color:#EEE;">{msg}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            time.sleep(0.5)

        # SHOW THINKING STEPS (Frontend only)
        step("Initializing Browser Agent")
        animated_loader("Connecting to backend")
        step("Sending query to backend")
        animated_loader("Waiting for search results")

        with st.spinner("Finalizing…"):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/run",
                    json={"query": user_query},
                    timeout=60
                )

                if response.status_code == 200:

                    result = response.json().get("response", {})
                    status = result.get("status")

                    if status == "success":
                        data = result["data"]

                        step("Result received ✔")
                        st.success("Result Found!")

                        # URL SECTION
                        st.subheader("URL")
                        st.write(data["url"])

                        # SNIPPET SECTION
                        st.subheader("Snippet")
                        st.write(data["snippet"])

                        # FULL TEXT SCROLL BOX
                        st.subheader("Summarized Full Text")
                        st.markdown(
                            f"""
                            <div style="
                                background-color:#111;
                                padding:15px;
                                border-radius:10px;
                                height:350px;
                                overflow-y: scroll;
                                border:1px solid #444;
                            ">
                                <p style="color:#EEE; font-size:15px; line-height:1.6;">
                                    {data["full_text"].replace("\n", "<br>")}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:
                        st.error(result.get("error", "No data returned."))

                else:
                    st.error(f"Backend Error: {response.text}")

            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
