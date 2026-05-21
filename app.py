from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.load import dumps, loads
import os
import streamlit as st
from operator import itemgetter
from utils import *
loader = PyPDFLoader('stsv.pdf')
pages = loader.load()
#print(type(pages)) #list
# for idx, page in enumerate(pages):
#   if idx == 3:
#     with open("output.txt", "w", encoding="utf-8") as f:
#       print(page, file = f)
#       break


os.environ['GOOGLE_API_KEY'] = st.secrets["GOOGLE_API_KEY"]


# splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 200)
# chunks = splitter.split_documents(pages)
# #print(type(chunks)) #list
# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# )
# vector_store = Chroma.from_documents(documents = chunks, embedding = embeddings)
# retriver = vector_store.as_retriever()

@st.cache_resource
def load_vectorstore():
    loader = PyPDFLoader('stsv.pdf')
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    chunks = splitter.split_documents(pages)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    return Chroma.from_documents(documents=chunks, embedding=embeddings)

vector_store = load_vectorstore()
retriever = vector_store.as_retriever(search_kwargs={"k": 2})


st.title('Ask AI 🤖')

# def ai_response(question):
  
#   def get_unique_union(documents: list[list]):
#     """ Unique union of retrieved docs """
#     # Flatten list of lists, and convert each Document to string
#     flattened_docs = [dumps(doc) for sublist in documents for doc in sublist]
#     # Get unique documents
#     unique_docs = list(set(flattened_docs))
#     # Return
#     return [loads(doc) for doc in unique_docs]
#   template1 = """You are an AI language model assistant. Your task is to generate three 
#     different versions of the given user question to retrieve relevant documents from a vector 
#     database. By generating multiple perspectives on the user question, your goal is to help
#     the user overcome some of the limitations of the distance-based similarity search. 
#     Provide these alternative questions separated by newlines. Original question: {question}"""
#   prompt1 = ChatPromptTemplate.from_template(template1)
#   generate_queries = (
#     prompt1
#     | ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
#     | StrOutputParser() 
#     | (lambda x: x.split("\n"))
# )
#   retriver_chain = generate_queries | retriever.map() | get_unique_union
  
#   template2 = """Answer the following question based on this context:
#     {context}
#     Question: {question}
#   """
#   prompt2 = ChatPromptTemplate.from_template(template2)
  
#   chain = (
#     {'question': itemgetter("question"), 'context': retriver_chain} | prompt2 | ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
#     | StrOutputParser() 
#   )
#   return chain.invoke({'question': question})
  
if 'messages' not in st.session_state: 
  st.session_state.messages = []

for message in st.session_state.messages:
  st.chat_message(message['role']).markdown(message['content'])

prompt = st.chat_input('Pass your prompt here')

if prompt:
  st.chat_message('user').markdown(prompt)
  st.session_state.messages.append({'role': 'user', 'content': prompt})
  response = app.invoke({"question": prompt, "retriever": retriever})['generation']
  st.chat_message('assistant').markdown(response)
  st.session_state.messages.append({'role': 'assistant', 'content': response})
