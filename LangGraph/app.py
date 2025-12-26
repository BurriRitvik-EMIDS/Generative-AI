from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from PyPDF2 import PdfReader
from typing import TypedDict
import os

# ✅ Step 1: Define the graph state schema
class GraphState(TypedDict):
    pdf_text: str
    summary: str

# ✅ Step 2: Read PDF
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text.strip()

# ✅ Step 3: Setup Gemini 2.5 Flash model

os.environ["GOOGLE_API_KEY"] = "AIzaSyDQnt6RSm6qr_DafyrAgmt7_uHJ2W6Gvp4"

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    temperature=0.3
)

# ✅ Step 4: Define the summarization node
def summarize_node(state: GraphState) -> GraphState:
    text = state["pdf_text"]
    
    prompt = [
        SystemMessage(content="You are a helpful assistant that summarizes documents in strictly 4–5 sentences."),
        HumanMessage(content=f"Summarize the following document:\n{text}")
    ]

    response = llm.invoke(prompt)
    return {"summary": response.content, "pdf_text": text}

# ✅ Step 5: Build the LangGraph
graph = StateGraph(GraphState)
graph.add_node("summarize", summarize_node)
graph.set_entry_point("summarize")
graph.set_finish_point("summarize")  # ✅ This is the correct method in your version

app = graph.compile()

# ✅ Step 6: Wrapper to run the summarizer
def summarize_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    text = read_pdf(file_path)
    if not text:
        return "The PDF is empty or contains no extractable text."
    
    result = app.invoke({"pdf_text": text, "summary": ""})
    return result["summary"]

# ✅ Run the app
if __name__ == "__main__":
    summary = summarize_pdf("document.pdf")
    print("\n📄 Summary:\n", summary)
