import fitz
import sys

def extract_all_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        with open("full_thesis_text.txt", "w", encoding="utf-8") as f:
            for i in range(len(doc)):
                # Mark page boundaries for easier parsing later
                f.write(f"\n<<<PAGE_START_{i+1}>>>\n")
                page = doc.load_page(i)
                text = page.get_text("text")
                f.write(text)
                f.write(f"\n<<<PAGE_END_{i+1}>>>\n")
        print(f"Extracted {len(doc)} pages to full_thesis_text.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_all_text("workflows and architecture/FINAL (2).pdf")
