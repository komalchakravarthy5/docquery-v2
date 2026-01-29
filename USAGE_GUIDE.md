# DocQuery Usage Guide

## 📏 File Size Limits & Performance

### Current Configuration

**Maximum File Size**: Technically up to **100MB**, but practical limits are lower due to processing time.

### Recommended File Sizes

| File Size | Pages (approx) | Processing Time | Recommendation |
|-----------|----------------|-----------------|----------------|
| < 2MB | 1-20 pages | 5-10 seconds | ✅ Optimal |
| 2-5MB | 20-50 pages | 15-30 seconds | ✅ Good |
| 5-10MB | 50-100 pages | 30-60 seconds | ⚠️ Slower |
| 10-20MB | 100-200 pages | 1-3 minutes | ⚠️ Very slow |
| > 20MB | 200+ pages | 3+ minutes | ❌ Not recommended |

### Why Large Files Are Slow

1. **PDF Text Extraction**: PyMuPDF processes each page
2. **Text Chunking**: Creates 500-character chunks with overlap
3. **Embedding Generation**: Most time-consuming step
   - Each chunk needs a 384-dimensional vector
   - 100 pages ≈ 400 chunks ≈ 20-30 seconds just for embeddings
4. **FAISS Index Creation**: Fast, but adds overhead
5. **Database Storage**: Minimal impact

### Tips for Large Files

1. **Split large PDFs** into smaller sections (by chapter/topic)
2. **Be patient** - first upload loads the embedding model
3. **Use text-based PDFs** - scanned images won't work
4. **Check file quality** - some PDFs have extraction issues

---

## 💬 What Questions to Ask

### ✅ Good Questions (What DocQuery Excels At)

#### 1. **Factual Information Retrieval**
```
❓ "What is the main topic of this document?"
❓ "Who are the authors mentioned?"
❓ "What is the definition of [term]?"
❓ "What are the key findings?"
```

#### 2. **Specific Details**
```
❓ "What methodology was used in the study?"
❓ "What are the system requirements?"
❓ "What is the budget mentioned on page 5?"
❓ "List all the recommendations"
```

#### 3. **Summarization**
```
❓ "Summarize the introduction"
❓ "What are the main conclusions?"
❓ "Give me a brief overview of chapter 3"
❓ "Summarize the key findings"
```

#### 4. **Comparison Questions**
```
❓ "What are the differences between method A and method B?"
❓ "Compare the results from section 2 and section 4"
❓ "What are the pros and cons mentioned?"
```

#### 5. **List Extraction**
```
❓ "List all the technologies mentioned"
❓ "What are the steps in the process?"
❓ "What are the challenges identified?"
❓ "List the references to [topic]"
```

#### 6. **Contextual Understanding**
```
❓ "Why was this approach chosen?"
❓ "What problem does this solve?"
❓ "What is the significance of [finding]?"
```

---

### ❌ Questions DocQuery May Struggle With

#### 1. **Information NOT in the Document**
```
❌ "What happened after this study?" (if not in doc)
❌ "What do other researchers think?" (external knowledge)
❌ "Is this still relevant today?" (requires current info)
```

#### 2. **Complex Reasoning Across Entire Document**
```
⚠️ "Analyze the logical flow of the entire argument"
⚠️ "Find contradictions across all chapters"
⚠️ "Create a comprehensive timeline from all dates"
```
*Why*: RAG retrieves top-5 chunks, may miss distant connections

#### 3. **Visual/Image Content**
```
❌ "What does the graph on page 10 show?"
❌ "Describe the diagram"
❌ "What are the values in the table?"
```
*Why*: Only text is extracted, images/tables are not processed

#### 4. **Mathematical Calculations**
```
❌ "Calculate the average from the data"
❌ "What is 25% of the budget mentioned?"
```
*Why*: LLM may hallucinate calculations

#### 5. **Subjective Opinions**
```
❌ "Is this a good research paper?"
❌ "Should I implement this approach?"
```
*Why*: DocQuery provides information, not opinions

---

## 🎯 Best Practices

### 1. **Be Specific**
- ❌ "Tell me about the results"
- ✅ "What were the accuracy results for Model A?"

### 2. **Reference Sections/Pages**
- ✅ "What does the introduction say about [topic]?"
- ✅ "Summarize the methodology section"

### 3. **Ask Follow-up Questions**
- First: "What is the main research question?"
- Then: "How did they address this question?"

### 4. **Check Citations**
- Always review the **page numbers** and **text snippets**
- Verify the answer matches the source

### 5. **Rephrase if Needed**
- If you get "I cannot find this information"
- Try rephrasing or asking more specifically

---

## 📊 Example Queries by Document Type

### Research Papers
```
✅ "What is the research methodology?"
✅ "What are the main findings?"
✅ "What are the limitations mentioned?"
✅ "What future work is suggested?"
```

### Technical Documentation
```
✅ "How do I install this software?"
✅ "What are the system requirements?"
✅ "Explain the API endpoints"
✅ "What are the configuration options?"
```

### Business Documents
```
✅ "What is the project timeline?"
✅ "What are the deliverables?"
✅ "Who are the stakeholders?"
✅ "What is the budget allocation?"
```

### Legal/Policy Documents
```
✅ "What are the terms and conditions?"
✅ "What are the compliance requirements?"
✅ "What are the penalties mentioned?"
✅ "Summarize section 5"
```

### Educational Materials
```
✅ "Explain the concept of [term]"
✅ "What are the key points in chapter 3?"
✅ "List the learning objectives"
✅ "What examples are provided?"
```

---

## 🔍 Understanding Citations

Each answer includes **citations** showing:

- **Page Number**: Where the information was found
- **Text Snippet**: Preview of the relevant text
- **Relevance Score**: How relevant this chunk is (0-1)

**High relevance (>0.8)**: Very confident answer  
**Medium relevance (0.5-0.8)**: Good match  
**Low relevance (<0.5)**: May not be directly related

---

## 🚀 Pro Tips

1. **First question loads models** - takes 10-20 seconds
2. **Subsequent questions are fast** - 1-3 seconds
3. **Upload once, ask many questions** - no need to re-upload
4. **Use "Upload New Document"** to switch PDFs
5. **Refresh page** if you encounter errors
6. **Check backend terminal** for detailed error logs

---

## 🛠️ Troubleshooting

### "I cannot find this information in the document"
- Information might not be in the PDF
- Try rephrasing your question
- Check if it's in a table/image (not supported)

### Upload fails for large files
- File might be > 10MB (slow processing)
- Try splitting the PDF
- Check if PDF is text-based (not scanned)

### Slow responses
- First query loads models (normal)
- Large documents take longer
- Check internet connection (Gemini API)

---

## 📝 Summary

**DocQuery is best for:**
- ✅ Finding specific information in documents
- ✅ Summarizing sections
- ✅ Extracting facts and details
- ✅ Understanding document content

**DocQuery is NOT for:**
- ❌ Information outside the document
- ❌ Processing images/tables
- ❌ Complex calculations
- ❌ Subjective opinions

**Optimal usage:**
- Documents: 1-50 pages (< 5MB)
- Questions: Specific, factual queries
- Always verify citations!
