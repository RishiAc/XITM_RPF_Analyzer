#!/usr/bin/env python3
"""
Enhanced RFP Analyzer and Chunker
- Full-featured RFP analyzer for RAG pipeline
- Extracts FAR/DFARS, eligibility, due dates, evaluation criteria
- Classifies sections and assigns phases (P1-P4)
- Generates structured metadata for each chunk
"""

import re
import json
import pdfplumber
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import calendar

class RelatedSectionsPDFChunker:
    def __init__(self, max_chunk_size=8000, min_chunk_size=3000, overlap=500):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap

        # Enhanced regex patterns for comprehensive RFP analysis
        self.header_pattern = re.compile(
            r"(?i)\b(scope of work|statement of work|evaluation criteria|proposal requirements|submission instructions|contract clauses|attachments|appendix|terms and conditions|technical requirements|performance standards|deliverables|timeline|budget|cost|pricing|qualifications|experience|past performance|security requirements|compliance|certifications|insurance|warranty|maintenance|support|training|instructions|requirements|specifications|objectives|background|purpose|introduction)\b"
        )
        
        # Section numbering patterns
        self.section_num_pattern = re.compile(
            r"^\s*(\d+(?:\.\d+)*)\s+([A-Z][^.]*\.?)"
        )
        
        # FAR/DFARS detection patterns
        self.far_pattern = re.compile(
            r"\b(FAR\s*(?:52\.)?\d{1,3}(?:\.\d{1,3})*(?:-\d{1,3})?)\b",
            re.IGNORECASE
        )
        self.far_clause_pattern = re.compile(
            r"\b(52\.\d{1,3}(?:\.\d{1,3})*(?:-\d{1,3})?)\b"
        )
        self.dfars_pattern = re.compile(
            r"\b(DFARS?\s*(?:252\.)?\d{1,3}(?:\.\d{1,3})*(?:-\d{1,3})?)\b",
            re.IGNORECASE
        )
        
        # Eligibility patterns
        self.eligibility_patterns = {
            '8a': re.compile(r'\b8\(a\)\b', re.IGNORECASE),
            'sdvosb': re.compile(r'\b(SDVOSB|Service-Disabled Veteran-Owned Small Business)\b', re.IGNORECASE),
            'wosb': re.compile(r'\b(WOSB|Woman-Owned Small Business)\b', re.IGNORECASE),
            'gsb': re.compile(r'\b(GSB|Government Small Business)\b', re.IGNORECASE),
            'swam': re.compile(r'\b(SWaM|Small Women and Minority)\b', re.IGNORECASE),
            'small_business': re.compile(r'\b(Small Business|SB)\b', re.IGNORECASE),
            'hubzone': re.compile(r'\b(HUBZone|Historically Underutilized Business Zone)\b', re.IGNORECASE),
            'veteran': re.compile(r'\b(Veteran-Owned|VOSB)\b', re.IGNORECASE)
        }
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b'),  # MM/DD/YYYY
            re.compile(r'\b(\d{1,2}-\d{1,2}-\d{4})\b'),   # MM-DD-YYYY
            re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE),  # Month DD, YYYY
            re.compile(r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', re.IGNORECASE)  # DD Month YYYY
        ]
        
        # Evaluation criteria patterns
        self.evaluation_patterns = {
            'best_value': re.compile(r'\b(Best Value|Best Value Trade-off)\b', re.IGNORECASE),
            'lpta': re.compile(r'\b(LPTA|Lowest Price Technically Acceptable)\b', re.IGNORECASE),
            'points': re.compile(r'\b(\d+)\s*(points?|pts?)\b', re.IGNORECASE),
            'criteria': re.compile(r'\b(evaluation criteria|scoring criteria|assessment criteria)\b', re.IGNORECASE),
            'award_basis': re.compile(r'\b(award basis|selection criteria|evaluation factors)\b', re.IGNORECASE)
        }
        
        # (Removed pricing and risk pattern usage per requirements)
        
        # Submission instruction patterns
        self.submission_patterns = {
            'page_limit': re.compile(r'\b(\d+)\s*(pages?|page limit)\b', re.IGNORECASE),
            'format': re.compile(r'\b(format|formatting|font|margin|spacing)\b', re.IGNORECASE),
            'certifications': re.compile(r'\b(certifications|certified|certify)\b', re.IGNORECASE),
            'past_performance': re.compile(r'\b(past performance|previous work|references)\b', re.IGNORECASE),
            'deadline': re.compile(r'\b(deadline|due date|submission date|closing date)\b', re.IGNORECASE)
        }

    # --------------------------------------------------
    # Extract all text from the PDF
    # --------------------------------------------------
    def extract_text(self, pdf_path: Path) -> str:
        """Extract all text from PDF using pdfplumber"""
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text

    # --------------------------------------------------
    # Split PDF into semantic sections
    # --------------------------------------------------
    def split_into_sections(self, text: str) -> List[Dict]:
        """Split text into semantic sections based on headers and numbering"""
        sections = []
        current_section = {"title": "General", "content": [], "section_number": None}
        current_content_length = 0

        lines = text.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for major section headers (numbered sections)
            section_match = self.section_num_pattern.match(line)
            is_header = self.header_pattern.search(line)

            # If we find a new major section and current section has content
            if (section_match or is_header) and current_section["content"] and current_content_length > self.min_chunk_size:
                # Save current section
                sections.append(current_section)
                # Start new section
                current_section = {
                    "title": line,
                    "content": [line],
                    "section_number": section_match.group(1) if section_match else None
                }
                current_content_length = len(line)
            else:
                # Add to current section
                current_section["content"].append(line)
                current_content_length += len(line)

                # If we've exceeded max size, force a new section
                if current_content_length > self.max_chunk_size:
                    sections.append(current_section)
                    current_section = {
                        "title": f"Continuation of {current_section['title']}",
                        "content": [line],
                        "section_number": current_section["section_number"]
                    }
                    current_content_length = len(line)

            i += 1

        # Add the last section
        if current_section["content"]:
            sections.append(current_section)
            
        return sections

    # --------------------------------------------------
    # Extract comprehensive metadata from content
    # --------------------------------------------------
    def extract_metadata(self, content: str) -> Dict:
        """Extract all metadata from content"""
        metadata = {
            'due_dates': [],
            'eligibility': [],
            'far_references': [],
            'dfars_references': [],
            'evaluation_type': None,
            'submission_requirements': [],
            'keywords': []
        }
        
        # Extract dates
        for pattern in self.date_patterns:
            matches = pattern.findall(content)
            metadata['due_dates'].extend(matches)
        
        # Extract eligibility
        for eligibility_type, pattern in self.eligibility_patterns.items():
            if pattern.search(content):
                metadata['eligibility'].append(eligibility_type.upper())
        
        # Extract FAR references
        far_refs = list(set(self.far_pattern.findall(content)))
        far_clause_refs = list(set(self.far_clause_pattern.findall(content)))
        metadata['far_references'] = far_refs + far_clause_refs
        
        # Extract DFARS references
        dfars_refs = list(set(self.dfars_pattern.findall(content)))
        metadata['dfars_references'] = dfars_refs
        
        # Extract evaluation type
        for eval_type, pattern in self.evaluation_patterns.items():
            if pattern.search(content):
                metadata['evaluation_type'] = eval_type.replace('_', ' ').title()
                break
        
        # (Removed pricing model and risk extraction per requirements)
        
        # Extract submission requirements
        for sub_type, pattern in self.submission_patterns.items():
            if pattern.search(content):
                metadata['submission_requirements'].append(sub_type.replace('_', ' ').title())
        
        # Extract keywords (simple noun/verb extraction)
        words = re.findall(r'\b\w{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            if word not in ['that', 'this', 'with', 'from', 'they', 'have', 'been', 'will', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'after', 'first', 'well', 'also', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'may', 'say', 'use', 'her', 'many', 'some', 'time', 'very', 'when', 'much', 'then', 'them', 'can', 'only', 'other', 'new', 'some', 'take', 'than', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us']:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 10 keywords
        metadata['keywords'] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        metadata['keywords'] = [word for word, freq in metadata['keywords']]
        
        return metadata

    # --------------------------------------------------
    # Classify section based on title and content
    # --------------------------------------------------
    def classify_section(self, title: str, content: str = "") -> str:
        """Classify section type based on title and content"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        if "scope" in title_lower or "statement" in title_lower or "work" in title_lower:
            return "scope"
        elif "evaluation" in title_lower or "criteria" in title_lower or "scoring" in title_lower:
            return "evaluation"
        elif "requirement" in title_lower or "specification" in title_lower or "technical" in title_lower:
            return "technical_requirements"
        elif "submission" in title_lower or "proposal" in title_lower or "instructions" in title_lower:
            return "submission_requirements"
        elif "pricing" in title_lower or "cost" in title_lower or "budget" in title_lower or "price" in title_lower:
            return "pricing"
        elif "eligibility" in title_lower or "qualification" in title_lower or "qualify" in title_lower:
            return "eligibility"
        elif "clause" in title_lower or "term" in title_lower or "condition" in title_lower:
            return "contract_clauses"
        elif "deliverable" in title_lower or "timeline" in title_lower or "schedule" in title_lower:
            return "deliverables_timeline"
        elif "security" in title_lower or "compliance" in title_lower or "certification" in title_lower:
            return "security_compliance"
        elif "insurance" in title_lower or "warranty" in title_lower or "maintenance" in title_lower:
            return "insurance_warranty"
        else:
            return "general"

    # --------------------------------------------------
    # Assign phase based on section type and content
    # --------------------------------------------------
    def assign_phase(self, section_type: str, content: str = "") -> str:
        """Assign P1-P4 phase based on section type"""
        content_lower = content.lower()
        
        # P1 = Eligibility, Risk, Due Date
        if section_type in ["eligibility", "contract_clauses"] or any(word in content_lower for word in ["due date", "deadline", "submission date", "closing"]):
            return "P1"
        
        # P2 = Scope, Technical Requirements, Evidence
        elif section_type in ["scope", "technical_requirements", "deliverables_timeline"]:
            return "P2"
        
        # P3 = Evaluation Criteria
        elif section_type in ["evaluation"]:
            return "P3"
        
        # P4 = Pricing, Schedule
        elif section_type in ["pricing", "submission_requirements"]:
            return "P4"
        
        else:
            return "P1"  # Default to P1

    # --------------------------------------------------
    # Calculate risk score (0-5)
    # --------------------------------------------------
    def get_risk_score(self, metadata: Dict) -> int:
        """Risk scoring removed per requirements; always 0"""
        return 0

    # --------------------------------------------------
    # Create final chunks with comprehensive metadata
    # --------------------------------------------------
    def create_chunks(self, sections: List[Dict], source_file: str) -> List[Dict]:
        """Create chunks with comprehensive metadata"""
        chunks = []
        for i, section in enumerate(sections):
            content = "\n".join(section["content"])
            
            # Extract metadata
            metadata = self.extract_metadata(content)
            
            # Classify section
            section_type = self.classify_section(section["title"], content)
            
            # Assign phase
            phase = self.assign_phase(section_type, content)
            
            # Calculate risk score
            risk_score = self.get_risk_score(metadata)
            
            # Create comprehensive metadata
            chunk_metadata = {
                "chunk_id": f"{Path(source_file).stem}_chunk_{i+1:04d}",
                "source_file": source_file,
                "section_title": section["title"],
                "section_number": section.get("section_number", "N/A"),
                "phase": phase,
                "due_dates": metadata['due_dates'],
                "eligibility": metadata['eligibility'],
                "evaluation_type": metadata['evaluation_type'],
                "far_references": metadata['far_references'],
                "dfars_references": metadata['dfars_references'],
                "keywords": metadata['keywords'],
                "word_count": len(content.split()),
                "character_count": len(content),
                "line_count": len(section["content"])
            }

            chunks.append({
                "metadata": chunk_metadata,
                "content": content
            })
        return chunks

    # --------------------------------------------------
    # Save chunks as readable text files
    # --------------------------------------------------
    def save_chunks_as_text(self, chunks: List[Dict], output_folder: Path, source_file: str):
        """Save each chunk as a separate text file with comprehensive metadata"""
        chunk_folder = output_folder / f"{Path(source_file).stem}_chunks"
        chunk_folder.mkdir(parents=True, exist_ok=True)
        
        for chunk in chunks:
            metadata = chunk["metadata"]
            content = chunk["content"]
            
            # Create filename
            chunk_filename = f"{metadata['chunk_id']}.txt"
            chunk_path = chunk_folder / chunk_filename
            
            # Format comprehensive metadata header
            metadata_header = f"""=== CHUNK METADATA ===
Chunk ID: {metadata['chunk_id']}
Source File: {metadata['source_file']}
Section Title: {metadata['section_title']}
Section Number: {metadata['section_number']}
Phase: {metadata['phase']}
Word Count: {metadata['word_count']}
Character Count: {metadata['character_count']}
Line Count: {metadata['line_count']}

=== KEY DATES ===
Due Dates: {', '.join(metadata['due_dates']) if metadata['due_dates'] else 'None'}

=== ELIGIBILITY ===
Eligibility Types: {', '.join(metadata['eligibility']) if metadata['eligibility'] else 'None'}

=== EVALUATION ===
Evaluation Type: {metadata['evaluation_type'] or 'Not specified'}

=== GOVERNMENT REFERENCES ===
FAR References: {', '.join(metadata['far_references']) if metadata['far_references'] else 'None'}
DFARS References: {', '.join(metadata['dfars_references']) if metadata['dfars_references'] else 'None'}

=== KEYWORDS ===
Top Keywords: {', '.join(metadata['keywords'][:10]) if metadata['keywords'] else 'None'}

=== CHUNK CONTENT ===
"""
            
            # Write to file
            with open(chunk_path, "w", encoding="utf-8") as f:
                f.write(metadata_header)
                f.write(content)

    # --------------------------------------------------
    # Save comprehensive summary file
    # --------------------------------------------------
    def save_summary(self, chunks: List[Dict], output_folder: Path, source_file: str, stats: Dict):
        """Save a comprehensive summary file"""
        summary_path = output_folder / f"{Path(source_file).stem}_summary.txt"
        
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"=== RFP COMPREHENSIVE ANALYSIS SUMMARY ===\n")
            f.write(f"Source File: {source_file}\n")
            f.write(f"Total Sections: {stats['total_original_sections']}\n")
            f.write(f"Total Chunks: {stats['total_chunks']}\n")
            f.write(f"Total Characters: {stats['extraction_metadata']['total_characters']}\n\n")
            
            # Phase distribution only (removed section types per requirements)
            f.write(f"=== PHASE DISTRIBUTION ===\n")
            phase_counts = {}
            for chunk in chunks:
                phase = chunk['metadata']['phase']
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
            for phase, count in sorted(phase_counts.items()):
                f.write(f"  - {phase}: {count} chunks\n")
            
            # FAR/DFARS summary
            far_refs = set()
            dfars_refs = set()
            total_far_count = 0
            total_dfars_count = 0
            
            for chunk in chunks:
                far_refs.update(chunk['metadata']['far_references'])
                dfars_refs.update(chunk['metadata']['dfars_references'])
                total_far_count += len(chunk['metadata']['far_references'])
                total_dfars_count += len(chunk['metadata']['dfars_references'])
            
            f.write(f"\n=== GOVERNMENT REFERENCES SUMMARY ===\n")
            f.write(f"Total FAR References Found: {total_far_count}\n")
            f.write(f"Total DFARS References Found: {total_dfars_count}\n")
            
            if far_refs:
                f.write(f"Unique FAR References:\n")
                for ref in sorted(far_refs):
                    f.write(f"  - {ref}\n")
            
            if dfars_refs:
                f.write(f"Unique DFARS References:\n")
                for ref in sorted(dfars_refs):
                    f.write(f"  - {ref}\n")
            
            # Eligibility summary
            eligibility_types = set()
            for chunk in chunks:
                eligibility_types.update(chunk['metadata']['eligibility'])
            
            f.write(f"\n=== ELIGIBILITY SUMMARY ===\n")
            if eligibility_types:
                f.write(f"Eligibility Types Found:\n")
                for el_type in sorted(eligibility_types):
                    f.write(f"  - {el_type}\n")
            else:
                f.write("No specific eligibility requirements found\n")
            
            # Evaluation summary only (removed pricing models per requirements)
            evaluation_types = set()
            
            for chunk in chunks:
                if chunk['metadata']['evaluation_type']:
                    evaluation_types.add(chunk['metadata']['evaluation_type'])
            
            f.write(f"\n=== EVALUATION SUMMARY ===\n")
            f.write(f"Evaluation Types: {', '.join(sorted(evaluation_types)) if evaluation_types else 'Not specified'}\n")
            
            # (Removed risk assessment summary per requirements)
            
            # Due dates summary
            all_due_dates = set()
            for chunk in chunks:
                all_due_dates.update(chunk['metadata']['due_dates'])
            
            f.write(f"\n=== KEY DATES SUMMARY ===\n")
            if all_due_dates:
                f.write(f"Due Dates Found:\n")
                for date in sorted(all_due_dates):
                    f.write(f"  - {date}\n")
            else:
                f.write("No specific due dates found\n")
            
            f.write(f"\n=== CHUNK LIST ===\n")
            for chunk in chunks:
                metadata = chunk['metadata']
                f.write(f"{metadata['chunk_id']}: {metadata['section_title']} (Phase: {metadata['phase']})\n")

    # --------------------------------------------------
    # Main PDF processor with comprehensive analysis
    # --------------------------------------------------
    def process_pdf(self, pdf_path: Path, output_folder: Path) -> Dict:
        """Process PDF with comprehensive RFP analysis"""
        text = self.extract_text(pdf_path)
        sections = self.split_into_sections(text)
        chunks = self.create_chunks(sections, pdf_path.name)

        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Save chunks as individual text files
        self.save_chunks_as_text(chunks, output_folder, pdf_path.name)
        
        # Save JSON for programmatic access
        json_path = output_folder / f"{pdf_path.stem}_chunks.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)

        # Prepare stats
        stats = {
            "file": pdf_path.name,
            "total_original_sections": len(sections),
            "total_grouped_sections": len(chunks),
            "total_chunks": len(chunks),
            "extraction_metadata": {"total_characters": len(text)},
        }

        # Save comprehensive summary
        self.save_summary(chunks, output_folder, pdf_path.name, stats)
        
        return stats