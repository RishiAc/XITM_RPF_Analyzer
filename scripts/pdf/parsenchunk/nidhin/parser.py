from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter

parser = LlamaParse(api_key="llx-y0lDjk4o2QVdB13CbRMdFdl3iEAZpBo6AbnsWFdGgBqgJb7l")
parsed_doc = parser.load_data("/Users/nidhingangisetty/XITM_RPF_Analyzer/docs/rpfs/rfp-26-001-htdc.pdf")

splitter = SentenceSplitter(chunk_size=512, chunk_overlap=75)
nodes = splitter.get_nodes_from_documents(parsed_doc)

with open("rfp_chunks.txt3", "w") as f:
    for i, node in enumerate(nodes, start=1):
        f.write(f"\n--- Chunk {i} ---\n{node.text}\n")
