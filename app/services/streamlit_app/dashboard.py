import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("AI-Powered Resume Analysis Platform")
st.write("Upload your resume to analyze technical skills and experience via FastAPI Backend.")

FASTAPI_URL = "http://127.0.0.1:8000/analyze-resume/"

uploaded_file = st.file_uploader("Choose your resume", type=["pdf", "docx"])

if uploaded_file:
    st.success("Resume uploaded successfully!")

    if st.button("Process & Analyze via API", type="primary"):
        with st.spinner("Sending resume to FastAPI backend for analysis..."):
            try:
                # Read bytes explicitly
                bytes_data = uploaded_file.getvalue()
                files = {
                    "file": (uploaded_file.name, bytes_data, uploaded_file.type or "application/pdf")
                }

                # Timeout parameter added to prevent hanging indefinitely
                response = requests.post(FASTAPI_URL, files=files, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    categorized_skills = data.get("categorized_skills", {})
                    skill_exp_data = data.get("skill_wise_experience", [])
                    total_skills_count = data.get("total_skills_count", 0)
                    total_exp = data.get("total_experience_years", 0)
                    extracted_text = data.get("extracted_text", "")

                    st.markdown("### 📊 Candidate Overview")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Technical Skills Identified", total_skills_count)
                    with col2:
                        st.metric("Estimated Professional Experience", f"{total_exp}+ Years")

                    st.markdown("---")

                    tab1, tab2, tab3 = st.tabs(["🛠️ Categorized Skills", "📈 Skill-Wise Experience Table", "📄 Extracted Raw Text"])

                    with tab1:
                        if categorized_skills:
                            cols = st.columns(2)
                            col_idx = 0
                            for category, skills in categorized_skills.items():
                                with cols[col_idx % 2]:
                                    st.markdown(f"#### **{category}**")
                                    st.write(" • ".join([f"`{skill}`" for skill in skills]))
                                    st.markdown("---")
                                col_idx += 1
                        else:
                            st.warning("No technical skills matched.")

                    with tab2:
                        if skill_exp_data:
                            st.subheader("Technology & Skill Duration Mapping")
                            df = pd.DataFrame(skill_exp_data)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("No skills available to build experience table.")

                    with tab3:
                        st.text_area("Resume Content", extracted_text, height=300)

                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")

            except requests.exceptions.Timeout:
                st.error("Request Timed Out! Backend took too long to respond.")
            except requests.exceptions.ConnectionError:
                st.error("Connection Error! Could not connect to http://127.0.0.1:8000. Ensure FastAPI/Uvicorn is running.")
            except Exception as e:
                st.error(f"Unexpected Error: {str(e)}")