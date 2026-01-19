# template_manager.py
# Prompt template management system

from typing import List, Dict, Optional
import logging
import json
import MySQLdb
import re

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage prompt templates"""
    
    # Built-in system templates (inserted via SQL migration)
    SYSTEM_TEMPLATES = {
        'summarize': 'Summarize the key findings, methodology, and conclusions from {document}. Focus on practical implications.',
        'extract_findings': 'Extract all key findings from {document}. List them as bullet points with page references.',
        'compare_methods': 'Compare the methodologies between {document1} and {document2}. Highlight similarities and differences.',
        'legal_analysis': 'Analyze the legal implications of {section} in {document}. Cite relevant case law if available.',
        'extract_keywords': 'Extract the top 20 most important keywords from {document} and explain their significance.',
        'section_summary': 'Provide a detailed summary of the {section} section in {document}.'
    }
    
    @staticmethod
    def get_templates(
        db_connection,
        user_id: int = None,
        category: str = None,
        include_public: bool = True
    ) -> List[Dict]:
        """Get available templates"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Build query
            conditions = []
            params = []
            
            if user_id:
                conditions.append("(user_id = %s OR user_id IS NULL)")
                params.append(user_id)
            else:
                conditions.append("user_id IS NULL")  # Only system templates
            
            if category:
                conditions.append("category = %s")
                params.append(category)
            
            if include_public:
                if user_id:
                    conditions.append("(is_public = TRUE OR user_id = %s OR user_id IS NULL)")
                    params.append(user_id)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor.execute(f"""
                SELECT * FROM prompt_templates
                WHERE {where_clause}
                ORDER BY category, name
            """, tuple(params))
            
            templates = cursor.fetchall()
            cursor.close()
            
            # Parse JSON variables
            for template in templates:
                if template.get('variables'):
                    try:
                        template['variables'] = json.loads(template['variables'])
                    except:
                        template['variables'] = []
                
                # Convert timestamps
                if template.get('created_at'):
                    template['created_at'] = template['created_at'].isoformat()
            
            return templates
        
        except Exception as e:
            logger.exception(f"Failed to get templates: {e}")
            return []
    
    @staticmethod
    def create_template(
        db_connection,
        user_id: int,
        name: str,
        template_text: str,
        description: str = None,
        category: str = 'custom',
        variables: List[str] = None,
        is_public: bool = False
    ) -> int:
        """Create a custom template"""
        try:
            cursor = db_connection.cursor()
            
            variables_json = json.dumps(variables) if variables else None
            
            cursor.execute("""
                INSERT INTO prompt_templates 
                (user_id, name, description, template_text, category, variables, is_public)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, name, description, template_text, category, variables_json, is_public))
            
            template_id = cursor.lastrowid
            db_connection.commit()
            cursor.close()
            
            logger.info(f"Created template {template_id} for user {user_id}")
            return template_id
        
        except Exception as e:
            logger.exception(f"Failed to create template: {e}")
            return 0
    
    @staticmethod
    def execute_template(
        template_text: str,
        variables: Dict[str, str]
    ) -> str:
        """Execute a template by substituting variables"""
        try:
            result = template_text
            
            # Replace all {variable} placeholders
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                result = result.replace(placeholder, str(value))
            
            # Check for any remaining placeholders
            remaining = re.findall(r'\{(\w+)\}', result)
            if remaining:
                logger.warning(f"Template has unfilled variables: {remaining}")
            
            return result
        
        except Exception as e:
            logger.exception(f"Template execution failed: {e}")
            return template_text
    
    @staticmethod
    def extract_variables(template_text: str) -> List[str]:
        """Extract variable names from template"""
        return re.findall(r'\{(\w+)\}', template_text)
    
    @staticmethod
    def record_usage(db_connection, template_id: int, user_id: int):
        """Record template usage for analytics"""
        try:
            cursor = db_connection.cursor()
            
            # Increment usage count
            cursor.execute("""
                UPDATE prompt_templates 
                SET usage_count = usage_count + 1
                WHERE id = %s
            """, (template_id,))
            
            # Record in usage table
            cursor.execute("""
                INSERT INTO template_usage (template_id, user_id)
                VALUES (%s, %s)
            """, (template_id, user_id))
            
            db_connection.commit()
            cursor.close()
        
        except Exception as e:
            logger.exception(f"Failed to record template usage: {e}")
    
    @staticmethod
    def get_popular_templates(db_connection, limit: int = 10) -> List[Dict]:
        """Get most used templates"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            cursor.execute("""
                SELECT * FROM prompt_templates
                WHERE is_public = TRUE OR user_id IS NULL
                ORDER BY usage_count DESC
                LIMIT %s
            """, (limit,))
            
            templates = cursor.fetchall()
            cursor.close()
            
            # Parse JSON
            for template in templates:
                if template.get('variables'):
                    try:
                        template['variables'] = json.loads(template['variables'])
                    except:
                        template['variables'] = []
            
            return templates
        
        except Exception as e:
            logger.exception(f"Failed to get popular templates: {e}")
            return []


# Convenience functions
def get_templates(db, user_id: int = None, category: str = None) -> List[Dict]:
    """Get templates"""
    return TemplateManager.get_templates(db, user_id, category)


def execute_template(template_text: str, variables: Dict[str, str]) -> str:
    """Execute template with variables"""
    return TemplateManager.execute_template(template_text, variables)
