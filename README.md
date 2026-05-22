# 🤖 Ask AI – RAG Chatbot với Adaptive Retrieval

Một chatbot thông minh sử dụng **Retrieval-Augmented Generation (RAG)** kết hợp với **LangGraph** để tự động định tuyến câu hỏi đến nguồn dữ liệu phù hợp nhất.

## 🚀 Demo

👉 [tracuuthongtinsinhvien.streamlit.app](https://tracuuthongtinsinhvien.streamlit.app)

---

## ✨ Tính năng

- **Tự động định tuyến câu hỏi** – phân loại câu hỏi vào 3 luồng: Vector Store, Web Search, hoặc LLM trực tiếp
- **RAG với tài liệu PDF** – tìm kiếm thông tin từ file `stsv.pdf` thông qua ChromaDB
- **Web Search fallback** – dùng Tavily Search khi câu hỏi nằm ngoài phạm vi tài liệu
- **Chấm điểm tài liệu** – lọc tài liệu không liên quan trước khi sinh câu trả lời
- **Kiểm tra hallucination** – đánh giá câu trả lời có được hỗ trợ bởi dữ liệu hay không
- **Giao diện chat** – xây dựng bằng Streamlit với lịch sử hội thoại

---

## 🏗️ Kiến trúc

```
Câu hỏi
   │
   ▼
Router (Gemini)
   │
   ├──► Vector Store → Grade Docs → Generate → Grade Output
   │                        │                       │
   │                        └──► Web Search ◄────────┘
   │
   ├──► Web Search → Generate → Grade Output
   │
   └──► LLM Fallback (trả lời trực tiếp)
```

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Embedding | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector Store | ChromaDB |
| Orchestration | LangGraph |
| Web Search | Tavily Search |
| Framework | LangChain |
| UI | Streamlit |

---

## ⚙️ Cài đặt local

**1. Clone repo**
```bash
git clone https://github.com/ngvinh185/chatbox0.git
cd chatbox0
```

**2. Cài thư viện**
```bash
pip install -r requirements.txt
```

**3. Tạo file `.env` hoặc set biến môi trường**
```
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

**4. Chạy app**
```bash
streamlit run app.py
```

---

## ☁️ Deploy lên Streamlit Cloud

1. Push code lên GitHub
2. Vào [streamlit.io/cloud](https://streamlit.io/cloud) → **New app**
3. Chọn repo và file `app.py`
4. Vào **Settings → Secrets**, thêm:
```toml
GOOGLE_API_KEY = "your_google_api_key"
TAVILY_API_KEY = "your_tavily_api_key"
```

---

## 🔑 Lấy API Key

- **Google API Key**: https://aistudio.google.com/app/apikey
- **Tavily API Key**: https://app.tavily.com/home

---

## 📁 Cấu trúc project

```
chatbox0/
├── app.py            # Giao diện Streamlit + load vector store
├── utils.py          # LangGraph workflow, các node xử lý
├── stsv.pdf          # Tài liệu nguồn cho RAG
├── requirements.txt  # Thư viện cần thiết
└── README.md
```
