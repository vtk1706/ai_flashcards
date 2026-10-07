from langchain.document_loaders import PyPDFLoader
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain import hub
import re

def generate_flashcards(pdf_path):
    """Generate flashcards from PDF file - MODIFIED TO ACCEPT PARAMETER"""
    
    # Load PDF from the provided path
    try:
        loader = PyPDFLoader(pdf_path)
        doc = loader.load()
        print(f"Loaded {len(doc)} pages from {pdf_path}")
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return [{'question': 'Error loading PDF', 'answer': 'Please try a different file'}]

    # Initialize LLM
    llm = Ollama(model="llama3.2:3b", temperature=0.2)

    # Create prompt for flashcard generation
    prompt_template = """
    ROLE: You are a world-class academic. Your task is to generate a list of flashcard questions from the provided text that are perfect for active recall.

    CRITICAL RULES:
    1.  **GENERATE MULTIPLE QUESTIONS:** Analyze the text and create a list of questions. Generate as many high-quality questions as there are important, test-worthy concepts.
    2.  **ANSWER MUST BE IN THE TEXT:** This is the most important rule. **ONLY generate a question if its answer is a clear, short fact that is stated explicitly in the source text provided.** If the answer isn't directly in the text, DO NOT create the question.
    3.  **FOCUS ON CORE CONCEPTS:** Prioritize questions about fundamental definitions, key theories, cause-and-effect relationships, and important classifications.
    4.  **ABSOLUTELY NO EXERCISES:** IGNORE any practice questions, examples, or activities. Create only original questions about the core educational content.
    5.  **QUESTION QUALITY:** Each question must be a factual recall question. No yes/no, no multiple choice, no opinions.

    **REQUIRED FORMAT:**
    Q: [Your question here]
    Q: [Your next question here]

    **TEXT:**
    {doc_text}

    **QUESTIONS:**"""

    # Extract text from documents
    doc_text = "\n".join([d.page_content for d in doc])

    # Generate questions
    prompt = prompt_template.format(doc_text=doc_text[:4000])  # Limit text length
    questions_response = llm.invoke(prompt)

    # Parse questions from the response
    def parse_questions(response_text):
        """Extract questions from the LLM response"""
        questions = []
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Q:') or line.startswith('Q :') or re.match(r'^\d+\.', line):
                question = re.sub(r'^(Q:|Q\s*:|^\d+\.\s*)', '', line).strip()
                if question and len(question) > 10:
                    questions.append(question)
        return questions

    questions = parse_questions(questions_response)
    print(f"Generated {len(questions)} questions")

    # If no questions generated, return demo questions
    if not questions:
        print("No questions generated, returning demo questions")
        return [
            {'question': 'What is the main topic of this document?', 'answer': 'The main topic appears to be educational content suitable for flashcard generation.'},
            {'question': 'What key concepts are discussed?', 'answer': 'The document contains material that can be converted into study flashcards.'}
        ]

    # Text splitting for RAG
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50, add_start_index=True
    )
    all_splits = text_splitter.split_documents(doc)
    print(f"Split into {len(all_splits)} chunks")

    # Create embeddings and vector store
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vector_store = Chroma.from_documents(
        documents=all_splits,           
        embedding=embeddings,
        collection_name="docs",
        persist_directory="./chroma_langchain_db"
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # Get RAG prompt
    prompt = hub.pull("rlm/rag-prompt")

    # Generate flashcards with answers
    flashcards = []
    
    for i, question in enumerate(questions, 1):
        print(f"Processing Question {i}: {question}")
        
        # Retrieve relevant chunks
        relevant_docs = retriever.invoke(question)
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        if not context_text.strip():
            print("No relevant context found for this question!")
            answer = "Information not found in the document."
        else:
            # Build the prompt
            final_prompt = prompt.invoke({"context": context_text, "question": question})
            
            # Get the answer
            answer = llm.invoke(final_prompt)
        
        # Create flashcard dictionary
        flashcard = {
            'question': question,
            'answer': answer
        }
        flashcards.append(flashcard)

    print(f"Successfully created {len(flashcards)} flashcards")
    return flashcards

# Keep original functionality for standalone use
if __name__ == '__main__':
    # For testing without Flask
    test_pdf = "sci.pdf"  # You can change this for testing
    flashcards = generate_flashcards(test_pdf)
    
    # Write to files
    with open("flashcards.txt", "w", encoding="utf-8") as file:
        file.write("=== FLASHCARDS ===\n\n")
        for i, card in enumerate(flashcards, 1):
            file.write(f"Q{i}: {card['question']}\n\n")

    with open("flashcards_with_answers.txt", "w", encoding="utf-8") as file:
        file.write("=== FLASHCARDS WITH ANSWERS ===\n\n")
        for i, card in enumerate(flashcards, 1):
            file.write(f"Q{i}: {card['question']}\n")
            file.write(f"A: {card['answer']}\n")
            file.write("-" * 50 + "\n\n")

    print("Flashcards saved to files!")