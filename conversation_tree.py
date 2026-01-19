# conversation_tree.py
# Conversation branching and tree visualization system

from typing import List, Dict, Optional, Tuple
import logging
import json
import MySQLdb
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationTree:
    """Manage conversation branching and tree structures"""
    
    @staticmethod
    def create_branch(
        db_connection,
        chat_id: int,
        message_id: int,
        parent_message_id: int = None,
        branch_name: str = None
    ) -> int:
        """Create a new conversation branch"""
        try:
            cursor = db_connection.cursor()
            
            cursor.execute("""
                INSERT INTO message_branches (chat_id, message_id, parent_message_id, branch_name)
                VALUES (%s, %s, %s, %s)
            """, (chat_id, message_id, parent_message_id, branch_name))
            
            branch_id = cursor.lastrowid
            db_connection.commit()
            cursor.close()
            
            logger.info(f"Created branch {branch_id} for chat {chat_id}")
            return branch_id
        
        except Exception as e:
            logger.exception(f"Failed to create branch: {e}")
            return 0
    
    @staticmethod
    def get_tree_structure(db_connection, chat_id: int) -> Dict:
        """Get the complete conversation tree structure"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get all messages in this chat
            cursor.execute("""
                SELECT m.*, b.parent_message_id, b.branch_name, b.id as branch_id
                FROM messages m
                LEFT JOIN message_branches b ON m.id = b.message_id
                WHERE m.chat_id = %s
                ORDER BY m.created_at ASC
            """, (chat_id,))
            
            messages = cursor.fetchall()
            cursor.close()
            
            if not messages:
                return {'nodes': [], 'edges': [], 'root': None}
            
            # Build tree structure
            nodes = []
            edges = []
            root_id = None
            
            for msg in messages:
                node = {
                    'id': msg['id'],
                    'text': msg['text'][:100] + '...' if len(msg['text']) > 100 else msg['text'],
                    'sender': msg['sender'],
                    'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
                    'branch_id': msg.get('branch_id'),
                    'branch_name': msg.get('branch_name'),
                    'parent_id': msg.get('parent_message_id')
                }
                nodes.append(node)
                
                # Create edges
                if msg.get('parent_message_id'):
                    edges.append({
                        'from': msg['parent_message_id'],
                        'to': msg['id'],
                        'branch_name': msg.get('branch_name')
                    })
                else:
                    # This is a root node (no parent)
                    if root_id is None:
                        root_id = msg['id']
            
            return {
                'nodes': nodes,
                'edges': edges,
                'root': root_id,
                'total_nodes': len(nodes),
                'total_branches': len([n for n in nodes if n.get('branch_id')])
            }
        
        except Exception as e:
            logger.exception(f"Failed to get tree structure: {e}")
            return {'nodes': [], 'edges': [], 'root': None}
    
    @staticmethod
    def get_branch_path(
        db_connection,
        message_id: int
    ) -> List[Dict]:
        """Get the full path from root to a specific message"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            path = []
            current_id = message_id
            
            # Traverse up the tree
            for _ in range(100):  # Max depth to prevent infinite loops
                cursor.execute("""
                    SELECT m.*, b.parent_message_id, b.branch_name
                    FROM messages m
                    LEFT JOIN message_branches b ON m.id = b.message_id
                    WHERE m.id = %s
                """, (current_id,))
                
                msg = cursor.fetchone()
                
                if not msg:
                    break
                
                path.insert(0, {
                    'id': msg['id'],
                    'text': msg['text'],
                    'sender': msg['sender'],
                    'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
                    'branch_name': msg.get('branch_name')
                })
                
                # Move to parent
                if msg.get('parent_message_id'):
                    current_id = msg['parent_message_id']
                else:
                    break
            
            cursor.close()
            return path
        
        except Exception as e:
            logger.exception(f"Failed to get branch path: {e}")
            return []
    
    @staticmethod
    def compare_branches(
        db_connection,
        branch_ids: List[int]
    ) -> Dict:
        """Compare multiple conversation branches"""
        try:
            if not branch_ids or len(branch_ids) < 2:
                return {'error': 'Need at least 2 branches to compare'}
            
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            branches_data = []
            
            for branch_id in branch_ids:
                # Get branch info
                cursor.execute("""
                    SELECT b.*, m.text as message_text, m.sender, m.created_at,
                           bm.quality_score, bm.user_preference
                    FROM message_branches b
                    JOIN messages m ON b.message_id = m.id
                    LEFT JOIN branch_metadata bm ON b.id = bm.branch_id
                    WHERE b.id = %s
                """, (branch_id,))
                
                branch = cursor.fetchone()
                
                if branch:
                    # Get full path for this branch
                    path = ConversationTree.get_branch_path(db_connection, branch['message_id'])
                    
                    branches_data.append({
                        'branch_id': branch_id,
                        'branch_name': branch.get('branch_name'),
                        'message_id': branch['message_id'],
                        'message_text': branch['message_text'],
                        'sender': branch['sender'],
                        'created_at': branch['created_at'].isoformat() if branch.get('created_at') else None,
                        'quality_score': branch.get('quality_score'),
                        'user_preference': branch.get('user_preference'),
                        'path': path,
                        'path_length': len(path)
                    })
            
            cursor.close()
            
            return {
                'branches': branches_data,
                'comparison_count': len(branches_data)
            }
        
        except Exception as e:
            logger.exception(f"Failed to compare branches: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def set_branch_preference(
        db_connection,
        branch_id: int,
        preference: str,
        quality_score: float = None
    ) -> bool:
        """Set user preference for a branch"""
        try:
            cursor = db_connection.cursor()
            
            # Check if preference is valid
            valid_preferences = ['preferred', 'neutral', 'rejected']
            if preference not in valid_preferences:
                logger.error(f"Invalid preference: {preference}")
                return False
            
            # Insert or update branch metadata
            cursor.execute("""
                INSERT INTO branch_metadata (branch_id, user_preference, quality_score)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    user_preference = VALUES(user_preference),
                    quality_score = VALUES(quality_score)
            """, (branch_id, preference, quality_score))
            
            db_connection.commit()
            cursor.close()
            
            return True
        
        except Exception as e:
            logger.exception(f"Failed to set branch preference: {e}")
            return False
    
    @staticmethod
    def get_divergence_point(
        db_connection,
        branch_id1: int,
        branch_id2: int
    ) -> Optional[int]:
        """Find where two branches diverged"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Get both branch message IDs
            cursor.execute("SELECT message_id FROM message_branches WHERE id = %s", (branch_id1,))
            msg1 = cursor.fetchone()
            
            cursor.execute("SELECT message_id FROM message_branches WHERE id = %s", (branch_id2,))
            msg2 = cursor.fetchone()
            
            if not msg1 or not msg2:
                cursor.close()
                return None
            
            # Get paths for both branches
            path1 = ConversationTree.get_branch_path(db_connection, msg1['message_id'])
            path2 = ConversationTree.get_branch_path(db_connection, msg2['message_id'])
            
            cursor.close()
            
            # Find last common ancestor
            common_ancestor = None
            for i in range(min(len(path1), len(path2))):
                if path1[i]['id'] == path2[i]['id']:
                    common_ancestor = path1[i]['id']
                else:
                    break
            
            return common_ancestor
        
        except Exception as e:
            logger.exception(f"Failed to get divergence point: {e}")
            return None


# Convenience functions
def create_conversation_branch(db, chat_id: int, message_id: int, parent_id: int = None, name: str = None) -> int:
    """Create a conversation branch"""
    return ConversationTree.create_branch(db, chat_id, message_id, parent_id, name)


def get_conversation_tree(db, chat_id: int) -> Dict:
    """Get conversation tree structure"""
    return ConversationTree.get_tree_structure(db, chat_id)
