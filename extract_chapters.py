"""
Complete Thesis Restructuring Script
Converts 8-chapter thesis to 5-chapter University of Sindh template format
"""

def create_restructured_thesis():
    # Read original thesis
    with open('thesis_final.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract chapters using markers
    import re
    
    # Find all chapter sections
    chapters = {}
    chapter_pattern = r'<div class="chapter" id="chapter(\d+)">(.*?)(?=<div class="chapter" id="chapter|<div class="references"|<div class="appendices"|<div class="page-break-before">|</body>)'
    
    for match in re.finditer(chapter_pattern, content, re.DOTALL):
        chapter_num = match.group(1)
        chapter_content = match.group(2)
        chapters[chapter_num] = chapter_content
        
    print(f"Found {len(chapters)} chapters")
    for num in sorted(chapters.keys()):
        print(f"  Chapter {num}: {len(chapters[num])} chars")
    
    # Extract other sections
    head = re.search(r'(<head>.*?</head>)', content, re.DOTALL)
    abstract = re.search(r'<div class="abstract">(.*?)</div>', content, re.DOTALL)
    references = re.search(r'<div class="references" id="references">(.*?)</div>\s*(?=<div class="page-break-before">|<div class="appendices"|$)', content, re.DOTALL)
    
    return {
        'head': head.group(1) if head else '',
        'abstract': abstract.group(1) if abstract else '',
        'chapters': chapters,
        'references': references.group(1) if references else '',
    }

if __name__ == '__main__':
    data = create_restructured_thesis()
    print("\nExtraction Summary:")
    print(f"Head: {len(data['head'])} chars")
    print(f"Abstract: {len(data['abstract'])} chars")
    print(f"References: {len(data['references'])} chars")
    print(f"Total chapters: {len(data['chapters'])}")
