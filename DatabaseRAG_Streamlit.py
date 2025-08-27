import streamlit as st
import time
from datetime import datetime
import mysql.connector
import pandas as pd
import os
from textwrap import dedent
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.schema import Document
st.set_page_config(
    page_title="Query Pilot",
    page_icon="🧭",
    layout="wide",
    menu_items={
        "Get Help": "https://docs.streamlit.io",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "Query Pilot — prompt-to-SQL and SQL-to-text assistant."
    },
)

st.title("QueryPilot App")
st.markdown("---")

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",       
    port=3306,             
    user="root",            
    password="Aaadd@1986",
    database="retail"  
)

# Create cursor
cursor = conn.cursor()
with open(r"C:\Users\fayab\Desktop\AI\GENAI\API_Keys\OPENAI_API_KEY.txt") as f:
    OPENAI_API_KEY = f.read().strip()
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

cursor.execute("SHOW TABLES")
rows = cursor.fetchall()                     
tables = [r[0] for r in rows]                

df = pd.DataFrame(rows, columns=["table"])   
st.subheader("Tables in schema")
st.write(df if not df.empty else "(none)")  

schema_lines = []
for t in tables:
    cursor.execute(f"DESCRIBE `{t}`")
    cols = cursor.fetchall()  
    cols_str = ", ".join(f"{c[0]} {c[1]}" for c in cols)
    schema_lines.append(f"{t}({cols_str})")
SCHEMA = "\n".join(schema_lines)

def run_and_fetch(cursor, sql):
    cursor.execute(sql)
    if not cursor.with_rows:      
        return [], []
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return cols, rows

st.subheader("Ask in plain English (NL → SQL → result)")
question = st.text_input(
    "Your question",
    value='Show me the number of employees who were hired before "1998-01-01"'
)
if st.button("Generate SQL and Run"):
    try:
        prompt = f"""
You generate a single MySQL SELECT that answers the question.
Use ONLY tables/columns from this schema and valid MySQL syntax.
Return SQL only (no comments, no explanation).

SCHEMA:
{SCHEMA}

QUESTION:
{question}

SQL:
""".strip()

        sql = llm.invoke(prompt).content.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        st.code(sql, language="sql")

        cols, rows = run_and_fetch(cursor, sql)

        if rows:
            # If it's a single numeric cell (e.g., COUNT(*)), show text + number
            if len(rows) == 1 and len(cols) == 1:
                val = rows[0][0]
                st.success(f"Answer: {val}")
                st.caption("There are {} record(s) matching your request.".format(val))
            else:
                import pandas as pd
                df = pd.DataFrame(rows, columns=cols)
                st.dataframe(df, use_container_width=True)
                st.caption(f"{len(rows)} row(s)")
        else:
            st.info("Query executed. No result set to display.")

    except Exception as e:
        st.error(f"Error: {e}")

st.markdown("---")

st.subheader("Run SQL directly")
raw_sql = st.text_area("SQL", value="SELECT * FROM employee LIMIT 10", height=120)

if st.button("Run SQL"):
    try:
        cols, rows = run_and_fetch(cursor, raw_sql)
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
            st.caption(f"{len(rows)} row(s)")
        else:
            st.info("Query executed. No result set to display.")
    except Exception as e:
        st.error(f"Error: {e}")