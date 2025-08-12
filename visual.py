import os
import pandas as pd
import streamlit as st
from openai import OpenAI

# First try to get from Streamlit Cloud secrets
api_key = st.secrets.get("OPENAI_API_KEY", None)

# Fallback: load from .env for local development
if not api_key:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI API key not found. Please set it in Streamlit secrets (Cloud) or .env (local).")
    st.stop()

client = OpenAI(api_key=api_key)

# Streamlit UI
st.title("Excel Data Cleaner with AI Prompts")

uploaded_file = st.file_uploader("Upload Excel/CSV file", type=["xlsx", "csv"])
if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("### Original Data")
    st.dataframe(df)

    user_prompt = st.text_area(
        "Describe the cleaning changes you want (e.g., 'Remove characters after comma in column Name')"
    )

    if st.button("Apply Changes") and user_prompt:
        try:
            prompt_text = f"""
            You are a data cleaning assistant.
            I have the following data (first 10 rows shown below):
            {df.head(10).to_csv(index=False)}

            Instruction from user:
            {user_prompt}

            Explain in plain English how to modify the DataFrame in pandas code,
            and only return Python code that modifies `df` in place.
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0
            )

            code_to_run = response.choices[0].message.content.strip("```python").strip("```")
            exec(code_to_run, {"df": df, "pd": pd})

            st.write("### Cleaned Data")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Cleaned CSV",
                data=csv,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error: {e}")
