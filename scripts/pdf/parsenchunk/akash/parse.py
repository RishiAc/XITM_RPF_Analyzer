# Baseline PDF Parser
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
import io
import shutil
import subprocess
import sys
import platform
from pathlib import Path
import time


def basic_parser(filepath):
    docs = PyPDFLoader(filepath).load()  

    # standard pdf parser based on chunk size, simplest
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_documents(docs) 

    return chunks

# Header aware parser (need to convert to html first)

def convert_to_html(filepath, outpath):
    output = io.StringIO()
    with open(filepath, "rb") as f:
        extract_text_to_fp(f, output, laparams=LAParams(), output_type="html", codec=None)
    html_text = output.getvalue()

    with open(outpath, "w") as f:
        f.write(html_text)

def ensure_poppler_installed():
    """Check if pdftohtml (Poppler) is installed; install if missing."""
    if shutil.which("pdftohtml"):
        print("✅ Poppler is already installed.")
        return

    os_type = platform.system()
    print("⚠️ Poppler not found. Attempting installation...")

    try:
        if os_type == "Linux":
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "poppler-utils"])
        elif os_type == "Darwin":  # macOS
            subprocess.check_call(["brew", "install", "poppler"])
        else:
            raise OSError(f"Unsupported OS for auto-install: {os_type}")
        print("✅ Poppler installed successfully.")
    except Exception as e:
        print(f"❌ Failed to install Poppler automatically: {e}")
        sys.exit(1)

def convert_to_html_cli(pdf_path: str, out_path: str):
    """Convert a PDF to HTML using pdftohtml."""
    pdf_path = Path(pdf_path)
    out_path = Path(out_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

    ensure_poppler_installed()

    # Run pdftohtml
    cmd = ["pdftohtml", "-c", "-noframes", str(pdf_path), str(out_path)]
    subprocess.check_call(cmd)

    print(f"✅ Converted {pdf_path} → {out_path}")
        
def structured_html_parser(filepath):
    pass

def unstructured_parser(filename):
    # strategy=fast for digital pdfs, use "auto/hi_res" for scanned documents
    loader = UnstructuredPDFLoader(
        filename,
        mode="elements",        
        strategy="fast"          
    )

    # Document Object: https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html 
    docs = loader.load()

    return docs

# Semantic Parser

def embedding_parser():
    pass

def basic_parser_driver(filepath):
    basic_chunks = basic_parser(filepath)

    with open("basic_pdf_parser.md", "w") as f:
        for i, chunk in enumerate(basic_chunks, start=1):
            f.write(f"\n--- Chunk {i} ---\n{chunk.page_content}\n")   

def unstructued_driver(filepath):
    start = time.time()

    docs = unstructured_parser(filepath)

    with open("unstructured_parser_res.md", "w") as f:
        for doc in docs:
            metadata = doc.metadata
            # Can split by category
            if "category" in metadata:
                category = metadata["category"]
                page_content = doc.page_content

                f.write(f"\n### {category}\n{page_content}")
    
    print(f"TOTAL TIME: {time.time() - start}")

def embedding_driver(filepath):
    # Good lightweight models for docs:

    #  - sentence-transformers/all-MiniLM-L6-v2  (small, fast)
    #  - thenlper/gte-base                       (balanced)
    #  - intfloat/e5-base-v2                     (popular, strong)
    emb = HuggingFaceEmbeddings(
        model_name="thenlper/gte-base",    # pick one from above
        # encode_kwargs={"normalize_embeddings": True},  # optional
    )

    sem_splitter = SemanticChunker(
    embeddings=emb,
        # Optional knobs:
        # breakpoint_threshold_type="percentile",       # or "standard_deviation"
        # breakpoint_threshold_amount=95,               # higher → fewer, larger chunks
    )

    text = open("unstructured_parser_res.md").read()  # or the cleaned text you want to chunk
    chunks = sem_splitter.split_text(text)

    with open("embedding_parser_res.md", "w") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"\n# Chunk {i}\n{chunk}")


def main():
    filepath = "/Users/akashwudali/XITM_RPF_Analyzer/docs/rpfs/2-RFP 2000004198.pdf"
    embedding_driver(filepath)


if __name__=="__main__":
    main()