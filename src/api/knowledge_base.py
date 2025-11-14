from pydantic import BaseModel
from typing import Optional

class KnowledgeBaseQuery(BaseModel):
    type: int # 0 is relational 1 is semantic
    query_number:  Optional[int] # for relational queries, can have different numbers which are set numbers
    context: Optional[str] # rfp chunks
    query: Optional[str] # query for vector search

def handle_database_query(kb_query: KnowledgeBaseQuery):
    pass

def handle_semantic_query(kb_query: KnowledgeBaseQuery):
    pass


def query_knowledge_base(kb_query: KnowledgeBaseQuery):

    if kb_query.type == 0:
        handle_database_query(kb_query)
    else:
        handle_semantic_query(kb_query)


### Used for make queries to the knowledge base
### - either designated queries to relational db 
### - or vector search on vector db