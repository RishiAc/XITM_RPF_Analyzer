from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter

def parse(file):
    parser = LlamaParse(api_key="llx-y0lDjk4o2QVdB13CbRMdFdl3iEAZpBo6AbnsWFdGgBqgJb7l")
    parsed_doc = parser.load_data(file)

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=75)
    nodes = splitter.get_nodes_from_documents(parsed_doc)

    return nodes

def chunks_to_json(doc_id, nodes):
    output = {
        "doc_id": doc_id,
        "chunks": []
    }
    for i, node in enumerate(nodes, start=1):  # start numbering at 1
        text = node.text.strip()
        text = text.replace("\r\n", " ")  # normalize Windows line endings
        text = text.replace("\n\n", " ")
        text = text.replace("\n", " ")
        text = text.replace("          ", " ")

        output["chunks"].append({
            "chunk_num": i,
            "text": text
        })

    return output

if __name__ == "__main__":
    print(chunks_to_json("test", parse("/Users/nidhingangisetty/XITM_RPF_Analyzer/docs/rpfs/rfp-26-001-htdc.pdf")))