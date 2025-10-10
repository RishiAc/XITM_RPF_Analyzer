from api.pdf.parser import chunks_to_json, parse

def main():
    filepath = "files/rfp_1.pdf"
    json_chunks = chunks_to_json("test", parse(filepath))
    print(json_chunks["chunks"][0])

if __name__ == "__main__":
    main()