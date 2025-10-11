from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter
import re

def write_to_file(nodes, file):
    with open(file, "w") as f:
        for i, node in enumerate(nodes):
            f.write(f"--- Chunk #{i} ---\n")
            f.write(node.text + "\n")

def parse(file, chunkSize: int = 1028, chunkOverlap: int = 50):
    parser = LlamaParse(
        api_key="llx-y0lDjk4o2QVdB13CbRMdFdl3iEAZpBo6AbnsWFdGgBqgJb7l",  # See how to get your API key at https://docs.cloud.llamaindex.ai/api_key
        parse_mode="parse_page_with_agent",  # The parsing mode
        model="anthropic-sonnet-4.0",  # The model to use
        high_res_ocr=True,  # Whether to use high resolution OCR (slower but more precise)
        adaptive_long_table=True,  # Adaptive long table. LlamaParse will try to detect long table and adapt the output
        outlined_table_extraction=True,  # Whether to try to extract outlined tables
        output_tables_as_HTML=True,  # Whether to output tables as HTML in the markdown output
    )
    parsed_doc = parser.load_data(file)

    splitter = SentenceSplitter(chunk_size=chunkSize, chunk_overlap=chunkOverlap)
    nodes = splitter.get_nodes_from_documents(parsed_doc)

    write_to_file(nodes, "rfp_chunks_with_chat.txt2")

    return nodes

def chunks_to_json(doc_id, nodes):
    output = {
        "doc_id": doc_id,
        "chunks": []
    }
    for i, node in enumerate(nodes, start=1):  # start numbering at 1
        text = node.text.strip()
        text = text.replace("\r\n", " ")  # normalize Windows line endings
        text = text.replace("\n", " ")

        text = re.sub(r"\s+", " ", text) # Simple Regex logic by Sriman S.

        output["chunks"].append({
            "chunk_num": i,
            "text": text
        })

    return output

# print(chunks_to_json("test", parse(r"C:\Users\mcyoo\Desktop\XITM\XITM_RPF_Analyzer\docs\rfps\2-RFP 2000004198.pdf")))
# print(chunks_to_json("test", parse(r"C:\Users\mcyoo\Desktop\XITM\XITM_RPF_Analyzer\docs\rfps\2-RFP 2000004198.pdf")))