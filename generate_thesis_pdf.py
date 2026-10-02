
import os

# 1. Fix the empty header in HTML
html_file = 'thesis_restructured.html'

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the target string (the empty header)
# We use a flexible approach to find it
target_header = "<h4>3.2.13 Key Frontend"
replacement_text = """<h4>3.2.13 Key Frontend Components</h3>
                                                                                                <p>
                                                                                                    The frontend architecture is modular, with distinct components responsible for specific user interactions and data display. These components leverage the vanilla JavaScript foundation for optimal performance and maintainability.
                                                                                                </p>"""

if "<h4>3.2.13 Key Frontend Components</h3>" in content:
    # It might be split across lines like in the view_file output
    # Let's try to normalize valid usage
    pass
else:
    # Try to find it with the weird whitespace from view_file
    # We will search for the specific lines index if text search fails
    # But for now, let's try a simpler replace based on the structure we saw
    pass

# Read lines to handle line-based replacement safely
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found = False
for i, line in enumerate(lines):
    if "<h4>3.2.13 Key Frontend" in line:
        # Check next line for Components</h3>
        if i + 1 < len(lines) and "Components</h3>" in lines[i+1]:
             new_lines.append(line)
             new_lines.append(lines[i+1])
             new_lines.append('                                                                                                <p>\n')
             new_lines.append('                                                                                                    The frontend architecture is modular, with distinct components responsible for specific user interactions and data display. These components leverage the vanilla JavaScript foundation for optimal performance and maintainability.\n')
             new_lines.append('                                                                                                </p>\n')
             found = True
             continue
        elif "Components</h3>" in line: # Single line case
             new_lines.append(line.replace("</h3>", "</h3>\n<p>The frontend architecture is modular, with distinct components responsible for specific user interactions and data display.</p>"))
             found = True
             continue
    
    # Skip the next line if we handled the 2-line header in previous iteration
    if found and "Components</h3>" in line and "<h4>" not in line and lines[i-1].strip().endswith("Frontend"):
        continue

    new_lines.append(line)

with open(html_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("HTML fixed.")

# 2. Generate PDF
try:
    from weasyprint import HTML
    print("Generating PDF...")
    HTML(html_file).write_pdf('thesis_final.pdf')
    print("PDF generated: thesis_final.pdf")
except ImportError:
    print("WeasyPrint not found, skipping PDF generation.")
except Exception as e:
    print(f"Error generating PDF: {e}")
