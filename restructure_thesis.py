"""
Script to restructure thesis from 8 chapters to 5 chapters following University of Sindh template
"""

import re
from pathlib import Path

# Read the original thesis
with open('thesis_final.html', 'r', encoding='utf-8') as f:
    original_content = f.read()

# Extract the HTML head section
head_match = re.search(r'(<head>.*?</head>)', original_content, re.DOTALL)
head_section = head_match.group(1) if head_match else ''

# Extract abstract
abstract_match = re.search(r'<div class="abstract">(.*?)</div>', original_content, re.DOTALL)
abstract_content = abstract_match.group(1) if abstract_match else ''

# Extract acknowledgments (near end of file)
ack_match = re.search(r'<h1 class="text-center">Acknowledgments</h1>(.*?)</div>', original_content, re.DOTALL)
acknowledgments_content = ack_match.group(1) if ack_match else ''

# Extract references
ref_match = re.search(r'<div class="references" id="references">(.*?)</div>\s*(?=<div class="page-break-before">|<div class="appendices"|$)', original_content, re.DOTALL)
references_content = ref_match.group(1) if ref_match else ''

print("Extraction complete!")
print(f"Head section: {len(head_section)} chars")
print(f"Abstract: {len(abstract_content)} chars")
print(f"References: {len(references_content)} chars")
