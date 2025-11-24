#!/usr/bin/env python3
"""
RFP Analyzer and PDF Chunker using pdfplumber
Extracts, classifies, and structures RFP data into chunks with rich metadata for RAG pipeline.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import pdfplumber
import re
from datetime import datetime
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants and Regex Patterns
FAR_DFARS_PATTERN = r'(FAR|DFARS)\s*\d{1,3}\.\d{1,3}-\d{1,3}(?:[a-z])?'
DATE_PATTERNS = [
    r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
    r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
    r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'  # DD Month YYYY
]

ELIGIBILITY_KEYWORDS = {
    '8(a)': ['8(a)', 'eight a', '8a'],
    'SDVOSB': ['sdvosb', 'service disabled veteran', 'veteran owned'],
    'WOSB': ['wosb', 'woman owned', 'women owned'],
    'GSB': ['gsb', 'government small business'],
    'SWaM': ['swam', 'small women minority'],
    'Small Business': ['small business', 'small business concern'],
    'HUBZone': ['hubzone', 'historically underutilized'],
    'VOSB': ['vosb', 'veteran owned small business']
}

EVALUATION_TYPES = ['best value', 'lpta', 'lowest price', 'technical', 'cost', 'price']
PRICING_MODELS = ['ffp', 'firm fixed price', 't&m', 'time and materials', 'idiq', 'indefinite delivery']
RISK_KEYWORDS = ['termination', 'liquidated damages', 'mandatory', 'penalty', 'breach', 'default']

SECTION_KEYWORDS = {
    'scope': ['scope', 'work', 'statement of work', 'sow', 'requirements', 'objectives'],
    'evaluation': ['evaluation', 'criteria', 'scoring', 'assessment', 'review', 'selection'],
    'submission_requirements': ['submission', 'proposal', 'response', 'instructions', 'format', 'deadline'],
    'pricing': ['pricing', 'cost', 'price', 'budget', 'financial', 'commercial'],
    'eligibility': ['eligibility', 'qualification', 'certification', 'set aside'],
    'general': ['general', 'terms', 'conditions', 'agreement', 'contract']
}

class RelatedSectionsPDFChunker:
    def __init__(self, max_chunk_size: int = 6000, min_chunk_size: int = 2000, overlap: int = 200):
        """
        Initialize the RFP analyzer and PDF chunker.
        
        Args:
            max_chunk_size: Maximum number of characters per chunk
            min_chunk_size: Minimum number of characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap = overlap
        
        # Section patterns for RFP document structure
        self.section_patterns = [
            # Numbered sections with colons
            r'^\s*\d+\.\s+[A-Z][A-Z\s]+:',  # "1. PURPOSE AND SCOPE:"
            r'^\s*\d+\.\d+\s+[A-Z][A-Z\s]+:',  # "1.1. SECTION NAME:"
            r'^\s*\d+\.\d+\.\d+\s+[A-Z][A-Z\s]+:',  # "1.1.1 SUBSECTION:"
            
            # Mixed case numbered sections
            r'^\s*\d+\.\s+[A-Z][a-z\s]+:',  # "1. Purpose and Scope:"
            r'^\s*\d+\.\d+\s+[A-Z][a-z\s]+:',  # "1.1. Section Name:"
            
            # Major section headers without colons
            r'^\s*\d+\.\s+[A-Z][A-Z\s]+$',  # "1. PURPOSE AND SCOPE"
            r'^\s*\d+\.\d+\s+[A-Z][A-Z\s]+$',  # "1.1. SECTION NAME"
            
            # Part/Section markers
            r'^\s*SECTION\s+\d+',  # "SECTION 1"
            r'^\s*PART\s+[IVX\d]+',  # "PART I", "PART 1"
            r'^\s*CHAPTER\s+\d+',  # "CHAPTER 1"
            
            # RFP-specific patterns
            r'^\s*SCOPE\s+OF\s+WORK',  # "SCOPE OF WORK"
            r'^\s*EVALUATION\s+CRITERIA',  # "EVALUATION CRITERIA"
            r'^\s*PROPOSAL\s+REQUIREMENTS',  # "PROPOSAL REQUIREMENTS"
            r'^\s*PRICING\s+INFORMATION',  # "PRICING INFORMATION"
        ]
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract full text from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        cleaned_text = self.clean_text(page_text)
                        text_content.append(cleaned_text)
                
                full_text = '\n\n'.join(text_content)
                logger.info(f"Extracted {len(full_text)} characters from {pdf_path.name}")
                return full_text
                
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into semantic sections based on headers and keywords.
        
        Args:
            text: Full text content
            
        Returns:
            List of section dictionaries with title, content, and metadata
        """
        sections = []
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            is_section = False
            section_number = None
            
            # Check against patterns
            for pattern in self.section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    is_section = True
                    # Extract section number if present
                    number_match = re.match(r'^(\d+(?:\.\d+)*)', line)
                    if number_match:
                        section_number = number_match.group(1)
                    break
            
            if is_section:
                # Save previous section if it exists
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    current_section['end_line'] = i - 1
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line,
                    'section_number': section_number,
                    'start_line': i,
                    'content': '',
                    'end_line': None
                }
                current_content = [line]
            else:
                current_content.append(line)
        
        # Add the last section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        logger.info(f"Identified {len(sections)} sections")
        return sections
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from section content.
        
        Args:
            content: Section content text
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'due_dates': [],
            'eligibility': [],
            'far_references': [],
            'pricing_model': None,
            'evaluation_type': None,
            'risk_level': 'Low',
            'keywords': [],
            'word_count': len(content.split())
        }
        
        content_lower = content.lower()
        
        # Extract due dates
        for pattern in DATE_PATTERNS:
            dates = re.findall(pattern, content, re.IGNORECASE)
            metadata['due_dates'].extend(dates)
        
        # Extract FAR/DFARS references
        far_refs = re.findall(FAR_DFARS_PATTERN, content, re.IGNORECASE)
        metadata['far_references'] = [ref.strip() for ref in far_refs]
        
        # Extract eligibility terms
        for eligibility_type, keywords in ELIGIBILITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    if eligibility_type not in metadata['eligibility']:
                        metadata['eligibility'].append(eligibility_type)
        
        # Extract pricing model
        for pricing_type in PRICING_MODELS:
            if pricing_type in content_lower:
                metadata['pricing_model'] = pricing_type.upper()
                break
        
        # Extract evaluation type
        for eval_type in EVALUATION_TYPES:
            if eval_type in content_lower:
                metadata['evaluation_type'] = eval_type.title()
                break
        
        # Calculate risk level
        risk_count = sum(1 for keyword in RISK_KEYWORDS if keyword in content_lower)
        if risk_count >= 3:
            metadata['risk_level'] = 'High'
        elif risk_count >= 1:
            metadata['risk_level'] = 'Medium'
        
        # Extract keywords (simple word frequency)
        words = re.findall(r'\b\w+\b', content_lower)
        word_freq = Counter(words)
        # Get most common words (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        keywords = [word for word, count in word_freq.most_common(10) if word not in stop_words and len(word) > 3]
        metadata['keywords'] = keywords[:5]  # Top 5 keywords
        
        return metadata
    
    def classify_section(self, title: str) -> str:
        """
        Classify section type based on title.
        
        Args:
            title: Section title
            
        Returns:
            Section type classification
        """
        title_lower = title.lower()
        
        # Check each section type
        for section_type, keywords in SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return section_type
        
        return 'general'
    
    def assign_phase(self, section_type: str) -> str:
        """
        Assign phase based on section type.
        
        Args:
            section_type: Classified section type
            
        Returns:
            Phase assignment (P1, P2, P3, P4)
        """
        phase_mapping = {
            'eligibility': 'P1',
            'general': 'P1',  # Terms and conditions often in P1
            'scope': 'P2',
            'submission_requirements': 'P2',
            'evaluation': 'P3',
            'pricing': 'P4'
        }
        
        return phase_mapping.get(section_type, 'P2')  # Default to P2
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text extracted from PDF."""
        if not text:
            return ""
        
        # Remove excessive whitespace but preserve structure
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page numbers (standalone numbers)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Normalize newlines but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def create_chunks(self, sections: List[Dict], source_file: str) -> List[Dict[str, Any]]:
        """
        Create chunks with metadata and classification.
        
        Args:
            sections: List of section dictionaries
            source_file: Source PDF filename
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        chunk_id = 1
        
        for section in sections:
            content = section['content']
            title = section['title']
            section_number = section.get('section_number', '')
            
            # Extract metadata
            metadata = self.extract_metadata(content)
            
            # Classify section
            section_type = self.classify_section(title)
            
            # Assign phase
            phase = self.assign_phase(section_type)
            
            # Create chunk
            chunk = {
                'chunk_id': f"{Path(source_file).stem}_chunk_{chunk_id:03d}",
                'section_title': title,
                'section_number': section_number,
                'section_type': section_type,
                'phase': phase,
                'due_dates': metadata['due_dates'],
                'eligibility': metadata['eligibility'],
                'evaluation_type': metadata['evaluation_type'],
                'pricing_model': metadata['pricing_model'],
                'risk_level': metadata['risk_level'],
                'far_references': metadata['far_references'],
                'keywords': metadata['keywords'],
                'word_count': metadata['word_count'],
                'content': content,
                'char_count': len(content),
                'source_file': source_file,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            chunks.append(chunk)
            chunk_id += 1
        
        logger.info(f"Created {len(chunks)} chunks from {len(sections)} sections")
        return chunks
    
    def save_chunks_as_text(self, chunks: List[Dict], output_folder: Path, source_file: str):
        """
        Save chunks as individual text files with metadata headers.
        
        Args:
            chunks: List of chunk dictionaries
            output_folder: Output directory path
            source_file: Source PDF filename
        """
        chunks_dir = output_folder / f"{Path(source_file).stem}_chunks"
        chunks_dir.mkdir(exist_ok=True)
        
        for chunk in chunks:
            chunk_file = chunks_dir / f"{chunk['chunk_id']}.txt"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                # Write metadata header
                f.write(f"Chunk ID: {chunk['chunk_id']}\n")
                f.write(f"Section: {chunk['section_title']}\n")
                f.write(f"Section Number: {chunk['section_number']}\n")
                f.write(f"Section Type: {chunk['section_type']}\n")
                f.write(f"Phase: {chunk['phase']}\n")
                f.write(f"Due Dates: {', '.join(chunk['due_dates']) if chunk['due_dates'] else 'None'}\n")
                f.write(f"Eligibility: {', '.join(chunk['eligibility']) if chunk['eligibility'] else 'None'}\n")
                f.write(f"Evaluation Type: {chunk['evaluation_type'] or 'None'}\n")
                f.write(f"Pricing Model: {chunk['pricing_model'] or 'None'}\n")
                f.write(f"Risk Level: {chunk['risk_level']}\n")
                f.write(f"FAR References: {', '.join(chunk['far_references']) if chunk['far_references'] else 'None'}\n")
                f.write(f"Keywords: {', '.join(chunk['keywords']) if chunk['keywords'] else 'None'}\n")
                f.write(f"Word Count: {chunk['word_count']}\n")
                f.write(f"Source File: {chunk['source_file']}\n")
                f.write("="*80 + "\n\n")
                f.write(chunk['content'])
        
        logger.info(f"Saved {len(chunks)} chunk files to {chunks_dir}")
    
    def save_summary(self, chunks: List[Dict], output_folder: Path, source_file: str, stats: Dict[str, Any]):
        """
        Save processing summary.
        
        Args:
            chunks: List of chunk dictionaries
            output_folder: Output directory path
            source_file: Source PDF filename
            stats: Processing statistics
        """
        summary_file = output_folder / f"{Path(source_file).stem}_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"RFP Analysis Summary\n")
            f.write(f"===================\n\n")
            f.write(f"Source File: {source_file}\n")
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Chunks: {len(chunks)}\n")
            f.write(f"Total Sections: {stats.get('total_sections', 0)}\n")
            f.write(f"Total Characters: {stats.get('total_characters', 0):,}\n")
            f.write(f"Total Words: {stats.get('total_words', 0):,}\n\n")
            
            # FAR References Summary
            all_far_refs = []
            for chunk in chunks:
                all_far_refs.extend(chunk['far_references'])
            unique_far_refs = list(set(all_far_refs))
            f.write(f"FAR/DFARS References Found: {len(unique_far_refs)}\n")
            for ref in sorted(unique_far_refs):
                f.write(f"  - {ref}\n")
            f.write("\n")
            
            # Eligibility Summary
            all_eligibility = []
            for chunk in chunks:
                all_eligibility.extend(chunk['eligibility'])
            unique_eligibility = list(set(all_eligibility))
            f.write(f"Eligibility Types Found: {len(unique_eligibility)}\n")
            for eligibility in sorted(unique_eligibility):
                f.write(f"  - {eligibility}\n")
            f.write("\n")
            
            # Evaluation Types Summary
            eval_types = [chunk['evaluation_type'] for chunk in chunks if chunk['evaluation_type']]
            unique_eval_types = list(set(eval_types))
            f.write(f"Evaluation Types Found: {len(unique_eval_types)}\n")
            for eval_type in sorted(unique_eval_types):
                f.write(f"  - {eval_type}\n")
            f.write("\n")
            
            # Pricing Models Summary
            pricing_models = [chunk['pricing_model'] for chunk in chunks if chunk['pricing_model']]
            unique_pricing = list(set(pricing_models))
            f.write(f"Pricing Models Found: {len(unique_pricing)}\n")
            for pricing in sorted(unique_pricing):
                f.write(f"  - {pricing}\n")
            f.write("\n")
            
            # Risk Level Summary
            risk_levels = [chunk['risk_level'] for chunk in chunks]
            risk_counts = Counter(risk_levels)
            f.write(f"Risk Level Distribution:\n")
            for risk_level, count in risk_counts.items():
                f.write(f"  - {risk_level}: {count} chunks\n")
            f.write("\n")
            
            # Phase Distribution
            phases = [chunk['phase'] for chunk in chunks]
            phase_counts = Counter(phases)
            f.write(f"Phase Distribution:\n")
            for phase, count in phase_counts.items():
                f.write(f"  - {phase}: {count} chunks\n")
        
        logger.info(f"Saved summary to {summary_file}")
    
    # Bonus Features
    def get_risk_score(self, chunk: Dict[str, Any]) -> int:
        """
        Calculate risk score (0-5) based on red flags and FAR references.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Risk score from 0 (low) to 5 (high)
        """
        score = 0
        
        # Base score from risk level
        risk_level_scores = {'Low': 0, 'Medium': 2, 'High': 4}
        score += risk_level_scores.get(chunk['risk_level'], 0)
        
        # Additional points for FAR references (complexity)
        score += min(len(chunk['far_references']), 2)
        
        # Additional points for multiple eligibility requirements
        if len(chunk['eligibility']) > 2:
            score += 1
        
        return min(score, 5)  # Cap at 5
    
    def extract_keywords(self, content: str) -> List[str]:
        """
        Extract most frequent keywords from content.
        
        Args:
            content: Text content
            
        Returns:
            List of top keywords
        """
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = Counter(words)
        
        # Common stop words to exclude
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'shall', 'must', 'will', 'shall', 'may', 'should', 'contractor',
            'government', 'contract', 'proposal', 'rfp', 'solicitation'
        }
        
        keywords = [
            word for word, count in word_freq.most_common(20)
            if word not in stop_words and len(word) > 3
        ]
        
        return keywords[:10]  # Top 10 keywords
    
    def auto_phase_assignment(self, chunk: Dict[str, Any]) -> str:
        """
        Automatically assign phase based on content analysis.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Phase assignment (P1, P2, P3, P4)
        """
        content_lower = chunk['content'].lower()
        
        # P1 indicators (Eligibility, Risk, Due Date)
        p1_keywords = ['eligibility', 'qualification', 'certification', 'set aside', 'due date', 'deadline', 'mandatory']
        if any(keyword in content_lower for keyword in p1_keywords):
            return 'P1'
        
        # P3 indicators (Evaluation Criteria)
        p3_keywords = ['evaluation', 'criteria', 'scoring', 'assessment', 'review', 'selection', 'points']
        if any(keyword in content_lower for keyword in p3_keywords):
            return 'P3'
        
        # P4 indicators (Pricing, Schedule)
        p4_keywords = ['pricing', 'cost', 'price', 'budget', 'financial', 'schedule', 'timeline']
        if any(keyword in content_lower for keyword in p4_keywords):
            return 'P4'
        
        # Default to P2 (Scope, Technical Requirements, Evidence)
        return 'P2'
    
    def process_pdf(self, pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Process a single PDF file and create RFP analysis chunks.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory for results
            
        Returns:
            Processing results dictionary
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Processing RFP PDF: {pdf_path.name}")
        
        # Extract text
        full_text = self.extract_text(pdf_path)
        if not full_text:
            logger.error(f"Failed to extract text from {pdf_path}")
            return None
        
        # Split into sections
        sections = self.split_into_sections(full_text)
        logger.info(f"Identified {len(sections)} sections")
        
        # Create chunks with metadata
        chunks = self.create_chunks(sections, pdf_path.name)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Calculate statistics
        stats = {
            'total_sections': len(sections),
            'total_chunks': len(chunks),
            'total_characters': len(full_text),
            'total_words': len(full_text.split()),
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # Prepare results
        result = {
            'pdf_file': pdf_path.name,
            'pdf_path': str(pdf_path),
            'processing_timestamp': datetime.now().isoformat(),
            'chunking_config': {
                'max_chunk_size': self.max_chunk_size,
                'min_chunk_size': self.min_chunk_size,
                'overlap': self.overlap,
                'chunking_strategy': 'rfp_analysis_with_metadata'
            },
            'sections': sections,
            'chunks': chunks,
            'statistics': stats
        }
        
        # Save output if output directory is specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save chunks as JSON
            json_file = output_path / f"{pdf_path.stem}_chunks.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Save chunks as text files
            self.save_chunks_as_text(chunks, output_path, pdf_path.name)
            
            # Save summary
            self.save_summary(chunks, output_path, pdf_path.name, stats)
            
            logger.info(f"Results saved to: {output_path}")
        
        return result
    
def main():
    parser = argparse.ArgumentParser(description='RFP Analyzer and PDF Chunker using pdfplumber')
    parser.add_argument('--input', '-i', required=True, 
                       help='Input PDF file or directory containing PDFs')
    parser.add_argument('--output', '-o', default='./rfp_analysis_output',
                       help='Output directory for analysis results')
    parser.add_argument('--max-chunk-size', '-s', type=int, default=6000,
                       help='Maximum characters per chunk (default: 6000)')
    parser.add_argument('--min-chunk-size', '-m', type=int, default=2000,
                       help='Minimum characters per chunk (default: 2000)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process PDFs recursively in subdirectories')
    
    args = parser.parse_args()
    
    # Initialize RFP analyzer
    analyzer = RelatedSectionsPDFChunker(
        max_chunk_size=args.max_chunk_size, 
        min_chunk_size=args.min_chunk_size
    )
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    # Find PDF files
    pdf_files = []
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        pdf_files = [input_path]
    elif input_path.is_dir():
        pattern = "**/*.pdf" if args.recursive else "*.pdf"
        pdf_files = list(input_path.glob(pattern))
    else:
        logger.error(f"Error: {input_path} is not a valid PDF file or directory")
        sys.exit(1)
    
    if not pdf_files:
        logger.error(f"No PDF files found in {input_path}")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Process each PDF
    results = []
    for pdf_file in pdf_files:
        try:
            result = analyzer.process_pdf(pdf_file, output_dir)
            if result:
                results.append(result)
                logger.info(f"✓ Successfully processed: {pdf_file.name}")
                logger.info(f"  - Sections: {result['statistics']['total_sections']}")
                logger.info(f"  - Chunks: {result['statistics']['total_chunks']}")
                logger.info(f"  - Characters: {result['statistics']['total_characters']:,}")
            else:
                logger.error(f"✗ Failed to process: {pdf_file.name}")
        except Exception as e:
            logger.error(f"✗ Error processing {pdf_file.name}: {str(e)}")
    
    # Print summary
    logger.info(f"\nRFP Analysis Summary:")
    logger.info(f"  Total files: {len(pdf_files)}")
    logger.info(f"  Successfully processed: {len(results)}")
    logger.info(f"  Failed: {len(pdf_files) - len(results)}")
    
    if results:
        total_chunks = sum(r['statistics']['total_chunks'] for r in results)
        total_sections = sum(r['statistics']['total_sections'] for r in results)
        total_chars = sum(r['statistics']['total_characters'] for r in results)
        logger.info(f"  Total sections analyzed: {total_sections}")
        logger.info(f"  Total chunks created: {total_chunks}")
        logger.info(f"  Total characters processed: {total_chars:,}")

if __name__ == "__main__":
    main()
