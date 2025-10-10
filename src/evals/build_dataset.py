from paddleocr import PaddleOCR
import os
from google import genai
import json
from pprint import pprint


ocr = PaddleOCR(use_angle_cls=True, lang='en')

def build_prompt(chunk):
    prompt = f"""
        ### Role
        You are an expert RFP analyst working at a government contracting staffing agency. 
        Your task is to read sections ("chunks") of Request for Proposal (RFP) documents 
        and generate natural-language search queries that could be used to retrieve that exact chunk.

        ### Objective
        Given the RFP chunk below, write **exactly three** concise and realistic queries that a user might ask 
        to find this part of the document. The queries should:
        - Reflect the intent or information contained in the text.
        - Use natural, human phrasing (not keywords or boilerplate).
        - Cover slightly different perspectives or phrasings of the same idea.
        - Avoid repeating exact wording from the text unless necessary.

        ### Example
        **Chunk Example:**
        "The Cover Letter must not contain any italics in the title."

        **Good Queries:**
        - "Find restrictions on the format of the cover letter"
        - "Can italics be used in the cover letter title"
        - "What are the formatting guidelines for the cover letter"

        ### Output Format
        Return the three queries **in a single line**, separated by commas **with no extra spaces or punctuation**.  
        For example:

        query1,query2,query3

        ### Chunk
        {chunk}
    """

    return prompt

def get_queries(chunk):

    retries = 3
    prompt = build_prompt(chunk)

    for i in range(retries):

        print(f"Attempt: {i + 1}")

        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )

        result = response.text

        print(f"Response Text:\n{result}")

        queries = result.split(",")

        print(queries)

        if len(queries) == 3:

            return queries
    
    return []

def get_chunks(chunk_img_dir):
    print("="*50)
    print(f"Getting Chunks From {chunk_img_dir}")

    count = 1

    chunks = []

    for chunk_img in os.listdir(chunk_img_dir):
        img_path = f"{chunk_img_dir}/{chunk_img}"
        result = ocr.predict(img_path)

        if len(result) > 0:

            print(f"Chunk Number: {count}")
            print(f"Adding: {img_path}")

            chunk = " ".join(result[0]["rec_texts"])

            chunks.append(chunk)

            count += 1
    
    return chunks

def generate_dataset_questions(chunk_img_dir, document_name):
    chunks = get_chunks(chunk_img_dir)

    data = {"chunks": []}

    for i, chunk in enumerate(chunks):

        print(f"Chunk Number: {i}")
        print("="*50)

        queries = get_queries(chunk)

        if len(queries) == 3:

            chunk_object = {
                "chunk_number": i + 1,
                "chunk_text": chunk,
                "queries": queries
            }

            pprint(chunk_object)

            data["chunks"].append(chunk_object)

    with open(f"chunk_jsons/{document_name}.json", "w") as f:
        json.dump(data, f, indent=4)


generate_dataset_questions("chunk_images", "rfp_1")