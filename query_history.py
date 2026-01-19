# query_history.py
# Query history tracking and re-execution across document versions

from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
import MySQLdb

logger = logging.getLogger(__name__)


class QueryHistoryManager:
    """Manage query history and enable re-execution"""
    
    @staticmethod
    def save_query(
        db_connection,
        user_id: int,
        query_text: str,
        response_text: str,
        context_used: Dict = None,
        tools_used: List[str] = None,
        intent: str = None,
        execution_time_ms: int = 0
    ) -> int:
        """
        Save a query to history
        
        Returns:
            query_id: ID of saved query
        """
        try:
            cursor = db_connection.cursor()
            
            context_json = json.dumps(context_used) if context_used else None
            tools_json = json.dumps(tools_used) if tools_used else None
            
            cursor.execute("""
                INSERT INTO query_history 
                (user_id, query_text, response_text, context_used, tools_used, intent, execution_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, query_text, response_text, context_json, tools_json, intent, execution_time_ms))
            
            query_id = cursor.lastrowid
            db_connection.commit()
            cursor.close()
            
            logger.info(f"Saved query history ID {query_id} for user {user_id}")
            return query_id
        
        except Exception as e:
            logger.exception(f"Failed to save query history: {e}")
            return 0
    
    @staticmethod
    def get_query_history(
        db_connection,
        user_id: int,
        limit: int = 50,
        intent_filter: str = None
    ) -> List[Dict]:
        """
        Get query history for a user
        
        Args:
            db_connection: Database connection
            user_id: User ID
            limit: Max number of queries to return
            intent_filter: Filter by intent type (optional)
        
        Returns:
            List of query history dicts
        """
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            if intent_filter:
                cursor.execute("""
                    SELECT * FROM query_history
                    WHERE user_id = %s AND intent = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, intent_filter, limit))
            else:
                cursor.execute("""
                    SELECT * FROM query_history
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, limit))
            
            history = cursor.fetchall()
            cursor.close()
            
            # Parse JSON fields
            for item in history:
                if item.get('context_used'):
                    try:
                        item['context_used'] = json.loads(item['context_used'])
                    except:
                        item['context_used'] = {}
                
                if item.get('tools_used'):
                    try:
                        item['tools_used'] = json.loads(item['tools_used'])
                    except:
                        item['tools_used'] = []
            
            return history
        
        except Exception as e:
            logger.exception(f"Failed to get query history: {e}")
            return []
    
    @staticmethod
    def rerun_query(
        db_connection,
        query_id: int,
        new_response: str,
        new_context: Dict = None
    ) -> Dict:
        """
        Re-run a historical query and compare results
        
        Args:
            db_connection: Database connection
            query_id: Original query ID
            new_response: New response from re-execution
            new_context: New context used
        
        Returns:
            {
                'original_response': str,
                'new_response': str,
                'differences': str,
                'context_changes': dict,
                'success': bool
            }
        """
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get original query
            cursor.execute("""
                SELECT query_text, response_text, context_used
                FROM query_history
                WHERE id = %s
            """, (query_id,))
            
            original = cursor.fetchone()
            
            if not original:
                return {'success': False, 'error': 'Original query not found'}
            
            # Parse original context
            original_context = {}
            if original.get('context_used'):
                try:
                    original_context = json.loads(original['context_used'])
                except:
                    pass
            
            # Compute differences (simple comparison)
            differences = QueryHistoryManager._compute_differences(
                original['response_text'],
                new_response
            )
            
            # Get context changes
            context_changes = {
                'original_files': original_context.get('files', []),
                'new_files': new_context.get('files', []) if new_context else [],
                'files_added': [],
                'files_removed': []
            }
            
            if new_context:
                orig_files = set(original_context.get('files', []))
                new_files = set(new_context.get('files', []))
                context_changes['files_added'] = list(new_files - orig_files)
                context_changes['files_removed'] = list(orig_files - new_files)
            
            # Save rerun record
            cursor.execute("""
                INSERT INTO query_reruns
                (original_query_id, new_response, differences, context_changes)
                VALUES (%s, %s, %s, %s)
            """, (
                query_id,
                new_response,
                differences,
                json.dumps(context_changes)
            ))
            
            db_connection.commit()
            cursor.close()
            
            return {
                'success': True,
                'original_response': original['response_text'],
                'new_response': new_response,
                'differences': differences,
                'context_changes': context_changes
            }
        
        except Exception as e:
            logger.exception(f"Failed to rerun query: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _compute_differences(original: str, new: str) -> str:
        """Compute simple differences between two responses"""
        # Simple character-level comparison
        if original == new:
            return "No changes detected."
        
        # Count word differences
        orig_words = set(original.lower().split())
        new_words = set(new.lower().split())
        
        added = new_words - orig_words
        removed = orig_words - new_words
        
        diff_summary = []
        
        if removed:
            diff_summary.append(f"Removed concepts: {', '.join(list(removed)[:10])}")
        
        if added:
            diff_summary.append(f"Added concepts: {', '.join(list(added)[:10])}")
        
        if not diff_summary:
            diff_summary.append("Response structure changed but vocabulary similar.")
        
        return " | ".join(diff_summary)
    
    @staticmethod
    def get_rerun_history(db_connection, original_query_id: int) -> List[Dict]:
        """Get all reruns for a specific query"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            cursor.execute("""
                SELECT * FROM query_reruns
                WHERE original_query_id = %s
                ORDER BY rerun_timestamp DESC
            """, (original_query_id,))
            
            reruns = cursor.fetchall()
            cursor.close()
            
            # Parse JSON
            for rerun in reruns:
                if rerun.get('context_changes'):
                    try:
                        rerun['context_changes'] = json.loads(rerun['context_changes'])
                    except:
                        rerun['context_changes'] = {}
            
            return reruns
        
        except Exception as e:
            logger.exception(f"Failed to get rerun history: {e}")
            return []


# Convenience functions
def save_query_to_history(
    db_connection,
    user_id: int,
    query: str,
    response: str,
    context: Dict = None,
    tools: List[str] = None,
    intent: str = None,
    exec_time: int = 0
) -> int:
    """Save query to history"""
    return QueryHistoryManager.save_query(
        db_connection, user_id, query, response,
        context, tools, intent, exec_time
    )
