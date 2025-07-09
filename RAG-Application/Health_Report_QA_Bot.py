import os
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# 🔐 Secure API Key
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Constants
PDF_FILE = "RAG-Application/whoReport.pdf"
APP_TITLE = "🌍 Health Report Q/A Bot"
APP_DESCRIPTION = """
Ask role-specific questions and receive grounded responses from the **WHO TB-Diabetes report**.

This assistant adapts the answer based on your professional background and delivers insights accordingly.
"""

# 🧠 Prompt Template
PROMPT_TEMPLATE = """
You are a domain-specific assistant grounded in the WHO TB–Diabetes report.

The user belongs to the category **{category}**, and their role is **{role}**. Based on this role, tailor your response using the appropriate tone, depth, and terminology that best serves the user's professional context and information needs.

Use only facts derived from the WHO document.

Context from WHO Report:
{context}

Conversation History:
{chat_history}

Question:
{question}

Your response must be:
- Consistent with the WHO’s findings and guidelines.
- Aligned with the role’s expectations (e.g., clinical detail for doctors, practical steps for caregivers, policy-level summaries for administrators).
- Clear, concise, and relevant to the user’s domain.

Respond accordingly, ensuring domain-specific accuracy and usefulness.
"""

# 🧠 Load and Embed PDF to FAISS


@st.cache_resource
def load_faiss_db():
    loader = PyPDFLoader(PDF_FILE)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(pages)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return FAISS.from_documents(docs, embeddings)

# 🔗 RAG Chain Builder


def build_chain(db, category, role):
    retriever = db.as_retriever()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question"
    )
    prompt = PromptTemplate(
        input_variables=["chat_history", "question",
                         "context", "category", "role"],
        template=PROMPT_TEMPLATE
    )
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
    )


# 🎨 Page Setup
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.markdown(
    f"<h1 style='text-align:center;'>{APP_TITLE}</h1>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center; color: gray;'>{APP_DESCRIPTION}</div>", unsafe_allow_html=True)
st.markdown("---")

# 🧭 Sidebar for Role & Category
with st.sidebar:
    st.markdown("## 👤 User Profile")
    roles_map = {
        "Healthcare Professional": ["Doctor", "Physician", "Nurse", "Pharmacist", "Lab Technician"],
        "Student or Trainee": ["Medical Student", "Public Health Student", "Intern"],
        "General Public": ["Patient", "Caregiver", "At-Risk Individual"],
        "Policy / System Worker": ["Health Admin", "Policy Maker", "NGO Worker"],
        "Research & Data": ["Researcher", "Epidemiologist", "Public Health Analyst"]
    }

    # Placeholder simulation
    category_options = ["🔽 Select a Category"] + list(roles_map.keys())
    category = st.selectbox(
        "🏷️ Select Your Category", category_options)

    if category != "🔽 Select a Category":
        role_options = ["🔽 Select a Role"] + roles_map[category]
        role = st.selectbox("🎓 Select Your Role", role_options)
    else:
        role = None

    st.markdown("---")
    st.markdown("💡 _The assistant tailors responses based on your role._")

# 🧠 Initialize Session State
if "chat_chain" not in st.session_state:
    st.session_state.chat_chain = None
    st.session_state.messages = []
    st.session_state.last_role = ""

if st.session_state.chat_chain is None or st.session_state.last_role != role:
    db = load_faiss_db()
    st.session_state.chat_chain = build_chain(db, category, role)
    st.session_state.last_role = role

# 💬 Main Chat Interface
st.markdown("## 💬 Ask Your Question")
with st.container():
    question = st.text_input("Type your question here",
                             placeholder="e.g., What are the screening guidelines for TB in diabetic patients?")

if question:
    response = st.session_state.chat_chain.invoke({
        "question": question,
        "category": category,
        "role": role
    })
    st.session_state.messages.append(("user", question))
    st.session_state.messages.append(("bot", response["answer"]))

# 🗨️ Display Chat History with Styled Bubbles
if st.session_state.messages:
    st.markdown("---")
    st.markdown("### 🗂️ Conversation")
    for sender, msg in st.session_state.messages:
        if sender == "user":
            st.markdown(
                f"""
                <div style='
                    background-color: black;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    border: 1px solid #93c5fd;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                '>
                    <b>🧑 You: ({role})</b><br>{msg}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='
                    background-color: black;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                    border: 1px solid #80cbc4;
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
                '>
                    <b>🤖 Assistant:</b><br>{msg}
                </div>
                """,
                unsafe_allow_html=True
            )

# 🧹 Footer
st.markdown("---")
st.markdown("<center><sub>Powered by LangChain • Google Gemini • Streamlit</sub></center>",
            unsafe_allow_html=True)
