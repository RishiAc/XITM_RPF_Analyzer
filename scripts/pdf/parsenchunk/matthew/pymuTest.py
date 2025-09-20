import pymupdf4llm as pmf
from langchain_text_splitters import MarkdownHeaderTextSplitter
import re
import os


# Converts a LangChain Document object into a string
def document_to_string(doc):
    # Convert metadata dictionary to a readable string
    metadata_str = "\n".join(f"{k}: {v}" for k, v in doc.metadata.items())
    
    # Combine metadata and page_content
    return f"{metadata_str}\n\n{doc.page_content}"

# Normalize markdown headers to a consistent format
def normalize_headers(md_text: str) -> str:
    # Convert numbered bold headings (1. **HEADER:**) -> ## HEADER
    md_text = re.sub(r"(\d+\.)\s+\*\*(.*?)\*\*", r"## \2", md_text)
    
    # Need to figure out which type of headers we need to clean up

    # # Convert standalone bold headings (**HEADER**) -> ## HEADER
    # md_text = re.sub(r"\n\*\*(.*?)\*\*\n", r"\n## \1\n", md_text)
    
    # Convert ## **HEADER** -> ## HEADER
    md_text = re.sub(r"(#+)\s+\*\*(.*?)\*\*", r"\1 \2", md_text)
    
    return md_text

# Saves chunks to an output folder
def save_splits_to_files(splits):
    os.makedirs("output", exist_ok=True)
    
    for i, doc in enumerate(splits, start=1):
        text = document_to_string(doc)
        filename = os.path.join("output", f"chunk_{i:03d}.md")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)

def main():
    # Convert PDF to markdown
    md_text = pmf.to_markdown('../../../../docs/rpfs/2-RFP 2000004198.pdf')
    
    # Normalize headers
    md_text_clean = normalize_headers(md_text)
    
    # Define headers to split on
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3")
    ]
    
    # Split markdown based on headers
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(md_text_clean)
    
    # Save each split section to a separate file
    save_splits_to_files(md_header_splits)
    
if __name__ == "__main__":
    main()