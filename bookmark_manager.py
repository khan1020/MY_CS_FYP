# bookmark_manager.py
# Bookmark management and PDF export functionality

from typing import List, Dict, Optional
import logging
import json
from datetime import datetime
import MySQLdb

logger = logging.getLogger(__name__)

# PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available. Install with: pip install reportlab")


class BookmarkManager:
    """Manage bookmarks and export to PDF"""
    
    @staticmethod
    def create_bookmark(
        db_connection,
        user_id: int,
        message_id: int,
        title: str = None,
        tags: List[str] = None,
        notes: str = None
    ) -> int:
        """Create a new bookmark"""
        try:
            cursor = db_connection.cursor()
            
            tags_json = json.dumps(tags) if tags else None
            
            cursor.execute("""
                INSERT INTO bookmarks (user_id, message_id, title, tags, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, message_id, title, tags_json, notes))
            
            bookmark_id = cursor.lastrowid
            db_connection.commit()
            cursor.close()
            
            logger.info(f"Created bookmark {bookmark_id} for user {user_id}")
            return bookmark_id
        
        except Exception as e:
            logger.exception(f"Failed to create bookmark: {e}")
            return 0
    
    @staticmethod
    def get_bookmarks(
        db_connection,
        user_id: int,
        tag_filter: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get user's bookmarks"""
        try:
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            if tag_filter:
                # Filter by tag (simplified - would need JSON_CONTAINS for proper filtering)
                cursor.execute("""
                    SELECT b.*, m.text as message_text, m.sender, m.created_at as message_created_at
                    FROM bookmarks b
                    JOIN messages m ON b.message_id = m.id
                    WHERE b.user_id = %s AND b.tags LIKE %s
                    ORDER BY b.created_at DESC
                    LIMIT %s
                """, (user_id, f'%{tag_filter}%', limit))
            else:
                cursor.execute("""
                    SELECT b.*, m.text as message_text, m.sender, m.created_at as message_created_at
                    FROM bookmarks b
                    JOIN messages m ON b.message_id = m.id
                    WHERE b.user_id = %s
                    ORDER BY b.created_at DESC
                    LIMIT %s
                """, (user_id, limit))
            
            bookmarks = cursor.fetchall()
            cursor.close()
            
            # Parse JSON tags
            for bookmark in bookmarks:
                if bookmark.get('tags'):
                    try:
                        bookmark['tags'] = json.loads(bookmark['tags'])
                    except:
                        bookmark['tags'] = []
                
                # Convert timestamps
                for field in ['created_at', 'message_created_at']:
                    if bookmark.get(field):
                        bookmark[field] = bookmark[field].isoformat()
            
            return bookmarks
        
        except Exception as e:
            logger.exception(f"Failed to get bookmarks: {e}")
            return []
    
    @staticmethod
    def delete_bookmark(db_connection, bookmark_id: int, user_id: int) -> bool:
        """Delete a bookmark"""
        try:
            cursor = db_connection.cursor()
            cursor.execute("""
                DELETE FROM bookmarks WHERE id = %s AND user_id = %s
            """, (bookmark_id, user_id))
            
            deleted = cursor.rowcount > 0
            db_connection.commit()
            cursor.close()
            
            return deleted
        
        except Exception as e:
            logger.exception(f"Failed to delete bookmark: {e}")
            return False
    
    @staticmethod
    def export_to_pdf(
        db_connection,
        user_id: int,
        bookmark_ids: List[int] = None,
        filename: str = "bookmarks_export.pdf"
    ) -> Optional[str]:
        """Export bookmarks to PDF"""
        
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available for PDF export")
            return None
        
        try:
            import io
            
            # Get bookmarks
            cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
            
            if bookmark_ids:
                placeholders = ','.join(['%s'] * len(bookmark_ids))
                cursor.execute(f"""
                    SELECT b.*, m.text as message_text, m.sender, m.created_at as message_created_at
                    FROM bookmarks b
                    JOIN messages m ON b.message_id = m.id
                    WHERE b.user_id = %s AND b.id IN ({placeholders})
                    ORDER BY b.created_at DESC
                """, (user_id, *bookmark_ids))
            else:
                cursor.execute("""
                    SELECT b.*, m.text as message_text, m.sender, m.created_at as message_created_at
                    FROM bookmarks b
                    JOIN messages m ON b.message_id = m.id
                    WHERE b.user_id = %s
                    ORDER BY b.created_at DESC
                """, (user_id,))
            
            bookmarks = cursor.fetchall()
            cursor.close()
            
            if not bookmarks:
                return None
            
            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495E'),
                spaceAfter=12
            )
            
            # Title
            story.append(Paragraph("Saved Responses", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Generate date
            export_date = datetime.now().strftime("%B %d, %Y")
            story.append(Paragraph(f"Exported on: {export_date}", styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            # Add each bookmark
            for i, bookmark in enumerate(bookmarks, 1):
                # Parse tags
                tags = []
                if bookmark.get('tags'):
                    try:
                        tags = json.loads(bookmark['tags'])
                    except:
                        pass
                
                # Title
                title = bookmark.get('title') or f"Bookmark #{i}"
                story.append(Paragraph(f"{i}. {title}", heading_style))
                story.append(Spacer(1, 0.1*inch))
                
                # Tags
                if tags:
                    tags_text = "Tags: " + ", ".join(tags)
                    story.append(Paragraph(tags_text, styles['Italic']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Message text
                message_text = bookmark.get('message_text', '')
                # Clean and format text
                message_text = message_text.replace('\n', '<br/>')
                story.append(Paragraph(message_text, styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))
                
                # Notes
                if bookmark.get('notes'):
                    story.append(Paragraph(f"<b>Notes:</b> {bookmark['notes']}", styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
                
                # Metadata
                created = bookmark.get('created_at', datetime.now()).strftime("%Y-%m-%d %H:%M") if bookmark.get('created_at') else 'Unknown'
                story.append(Paragraph(f"<i>Bookmarked: {created}</i>", styles['Italic']))
                
                story.append(Spacer(1, 0.3*inch))
                
                # Page break between bookmarks (except last)
                if i < len(bookmarks):
                    story.append(PageBreak())
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data
            buffer.seek(0)
            return buffer
        
        except Exception as e:
            logger.exception(f"PDF export failed: {e}")
            return None


# Convenience functions
def create_bookmark(db, user_id: int, message_id: int, title: str = None, tags: List[str] = None, notes: str = None) -> int:
    """Create a bookmark"""
    return BookmarkManager.create_bookmark(db, user_id, message_id, title, tags, notes)


def get_bookmarks(db, user_id: int, tag_filter: str = None, limit: int = 100) -> List[Dict]:
    """Get bookmarks"""
    return BookmarkManager.get_bookmarks(db, user_id, tag_filter, limit)


def export_bookmarks_to_pdf(db, user_id: int, bookmark_ids: List[int] = None) -> Optional[str]:
    """Export bookmarks to PDF"""
    return BookmarkManager.export_to_pdf(db, user_id, bookmark_ids)
