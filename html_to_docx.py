import os
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Configuration
HTML_FILE = "thesis_restructured.html"
DOCX_FILE = "thesis_final.docx"
IMAGE_DIR = "." # Images are relative to this script typically

def convert_html_to_docx():
    print(f"Reading {HTML_FILE}...")
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    doc = Document()
    
    # Set default style to Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    # Set margins to A4 default (approx 1 inch)
    # 2.54 cm = 1 inch
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.81) # 1.5 inch for binding
    section.right_margin = Cm(2.54) # 1 inch

    # Process Body
    body = soup.find('body')
    process_element(body, doc)

    print(f"Saving to {DOCX_FILE}...")
    doc.save(DOCX_FILE)
    print("Done.")

def process_element(element, doc):
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(element.name[1])
        text = element.get_text(strip=True)
        if text:
            doc.add_heading(text, level=level)
    
    elif element.name == 'p':
        text = element.get_text(strip=True)
        if text:
            # Check for center alignment in style attribute
            style = element.get('style', '')
            p = doc.add_paragraph(text)
            if 'text-align: center' in style:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
    elif element.name == 'ul':
        for li in element.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            doc.add_paragraph(text, style='List Bullet')
            
    elif element.name == 'ol':
        for li in element.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            doc.add_paragraph(text, style='List Number')
            
    elif element.name == 'figure':
        img = element.find('img')
        if img:
            src = img.get('src')
            if src.startswith('./'):
                src = src[2:]
            
            img_path = os.path.join(IMAGE_DIR, src)
            if os.path.exists(img_path):
                try:
                    # Adjust width to fit margin
                    doc.add_picture(img_path, width=Inches(5.5)) 
                except Exception as e:
                    print(f"Error adding image {img_path}: {e}")
            else:
                print(f"Image not found: {img_path}")
        
        caption = element.find('figcaption')
        if caption:
            text = caption.get_text(strip=True)
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.italic = True

    elif element.name == 'table':
        rows = element.find_all('tr')
        if rows:
            cols = len(rows[0].find_all(['td', 'th']))
            if cols > 0:
                table = doc.add_table(rows=len(rows), cols=cols)
                table.style = 'Table Grid'
                
                for i, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    row_cells = table.rows[i].cells
                    for j, cell in enumerate(cells):
                        if j < len(row_cells):
                            row_cells[j].text = cell.get_text(strip=True)

    elif element.name in ['div', 'body']:
        for child in element.children:
            if child.name:
                process_element(child, doc)

if __name__ == "__main__":
    convert_html_to_docx()
