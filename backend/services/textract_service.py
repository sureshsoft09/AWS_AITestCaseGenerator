"""
AWS Textract Service for document text extraction.
Handles PDF and document text extraction using AWS Textract.
"""
import os
import boto3
from typing import List, Dict, Optional
from backend.logger import logger
from backend.config import config


class TextractService:
    """Service for extracting text from documents using AWS Textract."""
    
    def __init__(self):
        """Initialize Textract client using default credential chain (saml2aws, environment, profile, IAM role)."""
        self.textract_client = boto3.client('textract', region_name=config.AWS_REGION)
        self.s3_client = boto3.client('s3', region_name=config.AWS_REGION)
        self.bucket_name = config.S3_BUCKET_NAME
    
    def extract_text_from_s3(self, s3_key: str) -> str:
        """
        Extract text from a document stored in S3 using Textract.
        
        Args:
            s3_key: S3 key of the document
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If text extraction fails
        """
        try:
            logger.info(
                "Starting Textract extraction",
                extra={"s3_key": s3_key, "bucket": self.bucket_name}
            )
            
            # Start document text detection
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': s3_key
                    }
                }
            )
            
            # Extract text from blocks
            extracted_text = self._extract_text_from_blocks(response.get('Blocks', []))
            
            logger.info(
                "Textract extraction completed",
                extra={
                    "s3_key": s3_key,
                    "text_length": len(extracted_text),
                    "blocks_count": len(response.get('Blocks', []))
                }
            )
            
            return extracted_text
            
        except Exception as e:
            logger.error(
                "Textract extraction failed",
                extra={"s3_key": s3_key, "error": str(e)}
            )
            raise Exception(f"Failed to extract text from {s3_key}: {str(e)}")
    
    def extract_text_from_multiple_documents(self, s3_keys: List[str]) -> str:
        """
        Extract and combine text from multiple documents.
        
        Args:
            s3_keys: List of S3 keys
            
        Returns:
            Combined extracted text from all documents
        """
        all_text = []
        
        for s3_key in s3_keys:
            try:
                text = self.extract_text_from_s3(s3_key)
                all_text.append(f"\n\n--- Document: {s3_key} ---\n\n{text}")
            except Exception as e:
                logger.warning(
                    "Skipping document due to extraction error",
                    extra={"s3_key": s3_key, "error": str(e)}
                )
                all_text.append(f"\n\n--- Document: {s3_key} ---\n\nERROR: {str(e)}")
        
        return "\n".join(all_text)
    
    def analyze_document(self, s3_key: str) -> Dict:
        """
        Perform advanced document analysis using Textract.
        Extracts text, tables, forms, and key-value pairs.
        
        Args:
            s3_key: S3 key of the document
            
        Returns:
            Dictionary containing extracted content
        """
        try:
            logger.info(
                "Starting Textract document analysis",
                extra={"s3_key": s3_key}
            )
            
            # Analyze document
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': s3_key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            blocks = response.get('Blocks', [])
            
            # Extract different types of content
            result = {
                'text': self._extract_text_from_blocks(blocks),
                'tables': self._extract_tables(blocks),
                'key_value_pairs': self._extract_key_value_pairs(blocks)
            }
            
            logger.info(
                "Document analysis completed",
                extra={
                    "s3_key": s3_key,
                    "tables_count": len(result['tables']),
                    "key_value_pairs_count": len(result['key_value_pairs'])
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Document analysis failed",
                extra={"s3_key": s3_key, "error": str(e)}
            )
            raise Exception(f"Failed to analyze document {s3_key}: {str(e)}")
    
    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """
        Extract plain text from Textract blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            Extracted text
        """
        lines = []
        
        for block in blocks:
            if block.get('BlockType') == 'LINE':
                text = block.get('Text', '')
                if text:
                    lines.append(text)
        
        return '\n'.join(lines)
    
    def _extract_tables(self, blocks: List[Dict]) -> List[List[str]]:
        """
        Extract tables from Textract blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            List of tables (each table is a list of rows)
        """
        tables = []
        
        # Create block map for quick lookup
        block_map = {block['Id']: block for block in blocks}
        
        for block in blocks:
            if block.get('BlockType') == 'TABLE':
                table = self._extract_table_cells(block, block_map)
                if table:
                    tables.append(table)
        
        return tables
    
    def _extract_table_cells(self, table_block: Dict, block_map: Dict) -> List[List[str]]:
        """
        Extract cells from a table block.
        
        Args:
            table_block: Table block from Textract
            block_map: Map of block IDs to blocks
            
        Returns:
            2D list representing table cells
        """
        cells = {}
        
        relationships = table_block.get('Relationships', [])
        for relationship in relationships:
            if relationship.get('Type') == 'CHILD':
                for cell_id in relationship.get('Ids', []):
                    cell = block_map.get(cell_id)
                    if cell and cell.get('BlockType') == 'CELL':
                        row_index = cell.get('RowIndex', 0)
                        col_index = cell.get('ColumnIndex', 0)
                        
                        # Get cell text
                        cell_text = self._get_cell_text(cell, block_map)
                        
                        if row_index not in cells:
                            cells[row_index] = {}
                        cells[row_index][col_index] = cell_text
        
        # Convert to 2D list
        if not cells:
            return []
        
        max_row = max(cells.keys())
        max_col = max(max(row.keys()) for row in cells.values())
        
        table_data = []
        for row in range(1, max_row + 1):
            row_data = []
            for col in range(1, max_col + 1):
                row_data.append(cells.get(row, {}).get(col, ''))
            table_data.append(row_data)
        
        return table_data
    
    def _get_cell_text(self, cell: Dict, block_map: Dict) -> str:
        """
        Get text content of a cell.
        
        Args:
            cell: Cell block
            block_map: Map of block IDs to blocks
            
        Returns:
            Cell text
        """
        text_parts = []
        
        relationships = cell.get('Relationships', [])
        for relationship in relationships:
            if relationship.get('Type') == 'CHILD':
                for child_id in relationship.get('Ids', []):
                    child = block_map.get(child_id)
                    if child and child.get('BlockType') == 'WORD':
                        text_parts.append(child.get('Text', ''))
        
        return ' '.join(text_parts)
    
    def _extract_key_value_pairs(self, blocks: List[Dict]) -> Dict[str, str]:
        """
        Extract key-value pairs (form fields) from blocks.
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            Dictionary of key-value pairs
        """
        key_value_pairs = {}
        
        # Create block map
        block_map = {block['Id']: block for block in blocks}
        
        for block in blocks:
            if block.get('BlockType') == 'KEY_VALUE_SET':
                entity_types = block.get('EntityTypes', [])
                
                if 'KEY' in entity_types:
                    # This is a key block
                    key_text = self._get_text_from_relationship(block, block_map, 'CHILD')
                    value_text = self._get_text_from_relationship(block, block_map, 'VALUE')
                    
                    if key_text and value_text:
                        key_value_pairs[key_text] = value_text
        
        return key_value_pairs
    
    def _get_text_from_relationship(
        self,
        block: Dict,
        block_map: Dict,
        relationship_type: str
    ) -> str:
        """
        Get text from blocks related by a specific relationship type.
        
        Args:
            block: Source block
            block_map: Map of block IDs to blocks
            relationship_type: Type of relationship ('CHILD' or 'VALUE')
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        relationships = block.get('Relationships', [])
        for relationship in relationships:
            if relationship.get('Type') == relationship_type:
                for related_id in relationship.get('Ids', []):
                    related_block = block_map.get(related_id)
                    
                    if not related_block:
                        continue
                    
                    if related_block.get('BlockType') == 'WORD':
                        text_parts.append(related_block.get('Text', ''))
                    elif related_block.get('BlockType') == 'KEY_VALUE_SET':
                        # Recursively get text from value block
                        text_parts.append(
                            self._get_text_from_relationship(
                                related_block,
                                block_map,
                                'CHILD'
                            )
                        )
        
        return ' '.join(text_parts)


# Global instance
textract_service = TextractService()
