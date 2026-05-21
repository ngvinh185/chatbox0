### Router
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from operator import itemgetter
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser


import os
from typing import Any
os.environ['TAVILY_API_KEY'] =st.secrets["TAVILY_API_KEY"]

from langchain_community.tools.tavily_search import TavilySearchResults
os.environ['GOOGLE_API_KEY'] = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
websearch_tool = TavilySearchResults()
def route_query(state):
  q = state['question']
  class websearch(BaseModel):
    """
    The internet. Use websearch for questions that are related to anything else than agents, prompt engineering, and adversarial attacks.
    """

    query: str = Field(description="The query to use when searching the internet.")


  class vectorstore(BaseModel):
      """
      A vectorstore containing documents related to agents, prompt engineering, and adversarial attacks. Use the vectorstore for questions on these topics.
      """

      query: str = Field(description="The query to use when searching the vectorstore.")
  
  preamble = """You are an expert at routing a user question to a vectorstore or web search.
    The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
    Use the vectorstore for questions on these topics. Otherwise, use web-search.""" 
  
  llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
  structered_llm = llm.bind_tools(
    tools = [websearch, vectorstore]
  )
  route_prompt = ChatPromptTemplate.from_messages([
      ("human", "{question}"),
    ])
  route_chain = itemgetter('question') | route_prompt | structered_llm
  response = route_chain.invoke({"question": q})
  if "tool_calls" not in response.additional_kwargs:

      return "llm_fallback"
  if len(response.additional_kwargs["tool_calls"]) == 0:
      raise "Router could not decide source"
  datasource = response.additional_kwargs["tool_calls"][0]["function"]["name"]
  if datasource == "websearch":
  
      return "websearch"
  elif datasource == "vectorstore":

      return "vectorstore"
  else:

      return "vectorstore"
    
def retrieve(state):
  q = state['question']
  # retrieve_chain = itemgetter("question") | retrieve
  retrieve_chain = state['retriever']
  
  documents = retrieve_chain.invoke(q)
  return {"question": q, "documents": documents}


def websearch(state):
  question = state["question"]
 
    # Web search
  docs = websearch_tool.invoke({"query": question})
  web_results = "\n".join([d["content"] for d in docs])
  web_results = Document(page_content=web_results)

  return {"documents": web_results, "question": question}
def llm_fallback(state):
  q = state['question']
  preamble = """You are an assistant for question-answering tasks. Answer the question based upon your knowledge. Use three sentences maximum and keep the answer concise."""
  prompt = ChatPromptTemplate.from_messages([
    ("system", preamble),
    ("user", "{question}")]
  )
  
  # llm_chain = itemgetter("question") | prompt | llm
  llm_chain = prompt | llm | StrOutputParser()
  
  generation = llm_chain.invoke({"question": q})
  return {"question": q, "generation": generation}
def grade_documents (state):
  class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
  structered_llm = llm.with_structured_output(GradeDocuments)
  q = state['question']
  documents = state['documents']
# Prompt
  preamble = """You are a grader assessing relevance of a retrieved document to a user question. \n
  If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
  Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

  retrieve_prompt = ChatPromptTemplate.from_messages([
    ('system', preamble),
    ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
  ])
  
  retrieve_chain = {"question": itemgetter("question"), "document": itemgetter("document")} | retrieve_prompt | structered_llm
  filter_doc = []
  for document in documents:
    score = retrieve_chain.invoke({"question": q, "document": document})
    grade = score.binary_score
    if grade == 'yes':
      filter_doc.append(document)
  return {"documents": filter_doc, "question": q}
  
def decide_to_generate(state):
  documents = state['documents']
  question = state['question']
  if len(documents) == 0:
    return 'websearch'
  return 'generate'
def generate(state):
  documents = state['documents']
  question = state['question']
  if not isinstance(documents, list):
    documents = [documents]


  preamble = """You are an assistant for question-answering tasks. \
  Use the following retrieved documents to answer the question. \
  If you don't know the answer, just say that you don't know. \
  Use three sentences maximum and keep the answer concise."""

  rag_prompt = ChatPromptTemplate.from_messages([
      ("system", preamble),
      ("human", "Documents: \n\n {documents} \n\n Question: {question}")
  ])

  rag_chain = (
    {
        "documents": itemgetter("documents"),
        "question": itemgetter("question")
    }
    | rag_prompt
    | llm
    | StrOutputParser()
  )
  generation = rag_chain.invoke({"documents": documents, "question": question})
  return {"documents": documents, "question": question, "generation": generation}

def grade_generation_v_documents_and_question(state):
  question = state["question"]
  documents = state["documents"]
  generation = state["generation"]
  class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )
# Preamble
  preamble = """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n
  Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""

  # LLM with function call
  structured_llm_grader = llm.with_structured_output(
      GradeHallucinations
  )

  # Prompt
  hallucination_prompt = ChatPromptTemplate.from_messages(
      [
          # ("system", system),
          ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
      ]
  )

  hallucination_grader = hallucination_prompt | structured_llm_grader
  score = hallucination_grader.invoke(
      {"documents": documents, "generation": generation}
  )
  grade = score.binary_score
  class GradeAnswer(BaseModel):
    """Binary score to assess answer addresses question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


# Preamble
  preamble = """You are a grader assessing whether an answer addresses / resolves a question \n
  Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""

  # LLM with function call
  structured_llm_grader = llm.with_structured_output(GradeAnswer)

  # Prompt
  answer_prompt = ChatPromptTemplate.from_messages(
      [
          ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
      ]
  )

  answer_grader = answer_prompt | structured_llm_grader
  # Check hallucination
  if grade == "yes":
    print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
    # Check question-answering
    print("---GRADE GENERATION vs QUESTION---")
    score = answer_grader.invoke({"question": question, "generation": generation})
    grade = score.binary_score
    if grade == "yes":
        return "useful"
    else:
        return "not useful"
  else:
    return "not supported"

import pprint

from langgraph.graph import END, StateGraph, START
from typing import List

from typing_extensions import TypedDict


class GraphState(TypedDict):
    """|
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]
    retriever: Any
workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("websearch", websearch)  # web search
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # rag
workflow.add_node("llm_fallback", llm_fallback)  # llm

# Build graph
workflow.add_conditional_edges(
    START,
    route_query,
    {
        "websearch": "websearch",
        "vectorstore": "retrieve",
        "llm_fallback": "llm_fallback",
    },
)
workflow.add_edge("websearch", "generate")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "websearch": "websearch",
        "generate": "generate",
    },
)
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",  # Hallucinations: re-generate
        "not useful": "websearch",  # Fails to answer question: fall-back to web-search
        "useful": END,
    },
)
workflow.add_edge("llm_fallback", END)

# Compile
app = workflow.compile()
