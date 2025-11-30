# PDF Chunker - Related Sections

The best PDF chunking system for RFP analysis. Groups related sections together while keeping unrelated sections separate.

## Files

- `related_sections_pdf_chunker.py` - Main chunking script
- `process_rpfs_related.py` - Process all RFP PDFs
- `requirements.txt` - Dependencies
- `related_chunked_pdfs/` - Output folder with chunked results

## Usage

```bash
# Process all RFP PDFs
python process_rpfs_related.py

# Process individual PDF
python related_sections_pdf_chunker.py --input "path/to/file.pdf" --output "./output"
```

## Results

- Groups related sections together (submission requirements, technical specs, etc.)
- Keeps unrelated sections separate
- Perfect for RFP analysis and RAG systems
- Maintains document structure and context
