"""
Complete Thesis Restructuring - Generate 5-Chapter Format
This script reads the original 8-chapter thesis and creates a new file
following the University of Sindh 5-chapter template format.
"""

import re
from datetime import datetime

def extract_content():
    """Extract all sections from original thesis"""
    with open('thesis_final.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract chapters
    chapters = {}
    chapter_pattern = r'<div class="chapter" id="chapter(\d+)">(.*?)(?=<div class="chapter" id="chapter|<div class="references"|<div class="appendices"|<div class="page-break-before">|</body>)'
    
    for match in re.finditer(chapter_pattern, content, re.DOTALL):
        chapter_num = match.group(1)
        chapter_content = match.group(2)
        chapters[chapter_num] = chapter_content
    
    # Extract other sections
    head = re.search(r'(<head>.*?</head>)', content, re.DOTALL)
    abstract = re.search(r'<div class="abstract">(.*?)</div>', content, re.DOTALL)
    references_match = re.search(r'<div class="references" id="references">(.*?)</div>\s*(?=<div class="page-break-before">|<div class="appendices"|$)', content, re.DOTALL)
    
    # Extract student names from cover page
    students_match = re.findall(r'<strong>(.*?)</strong>', content[:1000])
    
    return {
        'head': head.group(1) if head else '',
        'abstract': abstract.group(1) if abstract else '',
        'chapters': chapters,
        'references': references_match.group(1) if references_match else '',
        'students': students_match[:3] if students_match else []
    }

def create_front_matter(data):
    """Create all front matter pages"""
    students = data['students']
    
    front_matter = f'''
    <!-- ============================================
     COVER PAGE
     ============================================ -->
    <div class="cover-page">
        <p style="text-align: center; margin-bottom: 2rem;"><strong>INSTITUTE OF MATHEMATICS AND COMPUTER SCIENCE</strong></p>
        <p style="text-align: center;"><strong>BS(CS) Thesis</strong></p>
        
        <h1 style="text-align: center; margin: 3rem 0;">AI-POWERED DOCUMENT CHATBOT<br>WITH RAG CAPABILITIES</h1>
        
        <p style="text-align: center; margin: 2rem 0;"><strong>THESIS SUBMITTED TOWARDS THE PARTIAL FULFILMENT OF THE REQUIREMENT OF THE<br>
        UNIVERSITY OF SINDH, FOR THE AWARD OF BACHELOR OF SCIENCE IN<br>
        COMPUTER SCIENCE DEGREE.</strong></p>
        
        <div style="margin: 3rem 0; text-align: center;">
            <p><strong>By</strong></p>
            <p>1. {students[0] if len(students) > 0 else 'Student Name1'} (Group Leader) 2K22/CS/XXX</p>
            <p>2. {students[1] if len(students) > 1 else 'Student Name2'} 2K22/CS/XXX</p>
            <p>3. {students[2] if len(students) > 2 else 'Student Name3'} 2K22/CS/XXX</p>
        </div>
        
        <p style="text-align: center; margin-top: 4rem;"><strong>February 2026</strong></p>
        <p style="text-align: center;"><strong>University of Sindh, Jamshoro</strong></p>
    </div>

    <!-- ============================================
     CERTIFICATE
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">CERTIFICATE</h2>
        <p>This is to certify that the project entitled "AI-Powered Document Chatbot with RAG Capabilities" has been carried out by {', '.join(students[:2]) if len(students) >= 2 else 'the students'}, and {students[2] if len(students) > 2 else 'Student Name3'}, during the academic year 2024-2026 as a partial requirement for the degree of Bachelor of Science in Computer Science (BSCS).</p>
        
        <div style="margin-top: 4rem;">
            <p>_______________________</p>
            <p>Supervisor Name</p>
            <p>Department of Computer Science</p>
        </div>
    </div>

    <!-- ============================================
     DECLARATION
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">DECLARATION</h2>
        <p>This thesis is our original work and has not been ever submitted, in whole or in part for a degree at this or any other university. Nor it contain, to the best of our knowledge and belief any material published or written by any other person, except as acknowledged in the text.</p>
        
        <div style="margin-top: 3rem;">
            <p>_______________________</p>
            <p>{students[0] if len(students) > 0 else 'STUDENT NAME1'}</p>
            <br>
            <p>_______________________</p>
            <p>{students[1] if len(students) > 1 else 'STUDENT NAME2'}</p>
            <br>
            <p>_______________________</p>
            <p>{students[2] if len(students) > 2 else 'STUDENT NAME3'}</p>
        </div>
    </div>

    <!-- ============================================
     COPY RIGHTS
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">COPY RIGHTS</h2>
        <p>We hereby authorize University of Sindh, Jamshoro to supply copies of our thesis to individuals or libraries for study purposes only. However, no any part of this thesis or the information contained therein may be included in a publication or referred in any publication without prior written permission of the authors. Any reference must be fully acknowledged.</p>
        
        <div style="margin-top: 3rem;">
            <p>_______________________</p>
            <p>{students[0] if len(students) > 0 else 'STUDENT NAME1'}</p>
            <br>
            <p>_______________________</p>
            <p>{students[1] if len(students) > 1 else 'STUDENT NAME2'}</p>
            <br>
            <p>_______________________</p>
            <p>{students[2] if len(students) > 2 else 'STUDENT NAME3'}</p>
        </div>
    </div>

    <!-- ============================================
     DEDICATION
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">DEDICATION</h2>
        <p style="font-style: italic; text-align: center; margin-top: 3rem;">
        [To be filled by students]
        </p>
    </div>

    <!-- ============================================
     ACKNOWLEDGEMENTS
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">ACKNOWLEDGEMENTS</h2>
        <p>We would like to express our sincere gratitude to all those who contributed to the successful completion of this project.</p>
        <p>First and foremost, we thank our project supervisor for their invaluable guidance, expertise, and continuous support throughout the development of this system. Their insights into artificial intelligence and software engineering were instrumental in shaping the technical approach and ensuring the project's success.</p>
        <p>We extend our appreciation to the Department of Computer Science at the University of Sindh for providing the necessary resources and infrastructure that made this research possible. The academic environment fostered learning and innovation that were crucial to this work.</p>
        <p>We acknowledge the open-source community and the developers of the libraries and frameworks used in this project, particularly the teams behind SentenceTransformers, FAISS, Transformers, Flask, and all other tools that formed the foundation of our system.</p>
        <p>Special thanks to our fellow students and friends who participated in user testing and provided honest feedback that helped improve the system's usability and functionality.</p>
        <p>Finally, we are deeply grateful to our families for their unwavering support, patience, and encouragement throughout our academic journey and especially during the intensive period of this project's development.</p>
    </div>

    <!-- ============================================
     ABSTRACT
     ============================================ -->
    <div class="page-break-before">
        {data['abstract']}
    </div>
    '''
    
    return front_matter

def main():
    print("Extracting content from original thesis...")
    data = extract_content()
    
    print(f"Found {len(data['chapters'])} chapters")
    print("Generating restructured thesis...")
    
    # Start building the new HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">

{data['head']}

<body>

{create_front_matter(data)}

    <!-- TABLE OF CONTENTS will be added here manually by user -->
    
    <!-- ============================================
     CHAPTER 1: INTRODUCTION
     ============================================ -->
    <div class="chapter page-break-before" id="chapter1">
        <h1><span class="chapter-number">CHAPTER 1</span><br>INTRODUCTION</h1>
'''
    
    # Extract Chapter 1 content (sections 1.1-1.6)
    ch1 = data['chapters']['1']
    
    # Extract sections from Chapter 1
    motivation_match = re.search(r'(<h2 id="ch1-3">.*?Motivation and Significance</h2>.*?)(?=<h2 id=|<h3>|</div>)', ch1, re.DOTALL)
    objectives_match = re.search(r'(<h2 id="ch1-4">.*?Project Objectives</h2>.*?)(?=<h2 id=|</div>)', ch1, re.DOTALL)
    org_match = re.search(r'(<h2 id="ch1-6">.*?Thesis Organization</h2>.*?)(?=</div>)', ch1, re.DOTALL)
    
    # Build Chapter 1
    html_content += '''
        <h2>1.1 MOTIVATION</h2>
'''
    if motivation_match:
        content = motivation_match.group(1)
        # Remove the h2 tag and id
        content = re.sub(r'<h2 id="ch1-3">.*?</h2>', '', content)
        html_content += content
    
    html_content += '''
        <h2>1.2 CONTRIBUTIONS OF THE THESIS</h2>
        <p>This project makes several significant contributions to the field of conversational AI and intelligent document interaction:</p>
'''
    if objectives_match:
        content = objectives_match.group(1)
        # Extract main objectives
        html_content += '''
        <h3>1.2.1 Technical Contributions</h3>
        <ul>
            <li><strong>Hybrid Retrieval Implementation:</strong> Successfully integrated semantic search (FAISS) with lexical search (BM25) to achieve superior retrieval accuracy</li>
            <li><strong>Multimodal Processing:</strong> Combined text extraction, OCR, and image captioning for comprehensive document understanding</li>
            <li><strong>Modular RAG Architecture:</strong> Designed and implemented a extensible system architecture that separates concerns and enables easy maintenance</li>
        </ul>
        
        <h3>1.2.2 Practical Contributions</h3>
        <ul>
            <li><strong>Production-Ready System:</strong> Developed a fully functional web application with authentication, user management, and data persistence</li>
            <li><strong>User Experience Design:</strong> Created an intuitive interface with features like chat history, bookmarks, and templates</li>
            <li><strong>Documentation and Evaluation:</strong> Comprehensive testing and performance analysis demonstrating real-world viability</li>
        </ul>
'''
    
    html_content += '''
        <h2>1.3 STRUCTURE OF THE THESIS</h2>
        <p>This thesis is organized into five chapters, each addressing specific aspects of the project:</p>
        <ul>
            <li><strong>Chapter 1 (Introduction)</strong> provides the motivation, contributions, and structure of this thesis.</li>
            <li><strong>Chapter 2 (Background)</strong> examines existing research and technologies related to RAG systems, chatbots, semantic search, and vision AI.</li>
            <li><strong>Chapter 3 (Research Methodology)</strong> details the system requirements, design approach, and architectural decisions.</li>
            <li><strong>Chapter 4 (Results and Discussion)</strong> presents the implementation details, testing results, performance analysis, and discussion of challenges.</li>
            <li><strong>Chapter 5 (Conclusion and Future Directions)</strong> summarizes achievements, reflects on lessons learned, and outlines potential future enhancements.</li>
        </ul>
    </div>
'''
    
    # Chapter 2: Background (from original Chapter 2 - Literature Review)
    html_content += '''
    <!-- ============================================
     CHAPTER 2: BACKGROUND
     ============================================ -->
    <div class="chapter page-break-before" id="chapter2">
        <h1><span class="chapter-number">CHAPTER 2</span><br>BACKGROUND</h1>
        
        <p>This chapter presents the theoretical foundation and related work that underpins our AI-powered document chatbot system. We examine the evolution of chatbot technology, explore the principles of Retrieval-Augmented Generation, discuss document processing techniques, and review vision AI capabilities.</p>
'''
    
    # Add all of Chapter 2 content
    ch2 = data['chapters']['2']
    # Remove the chapter wrapper and title
    ch2_content = re.sub(r'<h1>.*?</h1>', '', ch2)
    ch2_content = re.sub(r'id="ch2-', 'id="ch2-', ch2_content)  # Keep IDs
    
    html_content += ch2_content
    
    # Add Summary for Chapter 2
    html_content += '''
        <h2>2.8 SUMMARY</h2>
        <p>This chapter provided a comprehensive review of the theoretical foundations and related technologies underlying our RAG-powered document chatbot system. We traced the evolution of chatbot technology from rule-based systems to modern transformer-based models, highlighting the paradigm shift that RAG represents.</p>
        <p>Key insights from this review include: (1) RAG systems effectively address the knowledge cutoff limitation of large language models by combining retrieval with generation; (2) Hybrid retrieval methods that merge semantic and lexical search outperform single-method approaches; (3) Vision AI capabilities extend document processing beyond text to include image understanding; (4) The integration of multiple AI technologies requires careful architectural design to balance performance, accuracy, and usability.</p>
        <p>The comparative analysis of existing systems revealed that while commercial solutions like ChatGPT offer powerful capabilities, they lack customization and raise data privacy concerns. Framework-based solutions like LangChain provide flexibility but require extensive configuration. Our system aims to bridge this gap by providing a complete, self-hosted solution with integrated hybrid retrieval and vision AI, packaged in a user-friendly interface suitable for educational and small business applications.</p>
    </div>
'''
    
    # Save to file
    output_file = 'thesis_restructured_partial.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nGenerated partial thesis: {output_file}")
    print("This includes: Front matter, Chapter 1, Chapter 2")
    print("\nNext: Will create Chapters 3, 4, 5 and complete the document...")

if __name__ == '__main__':
    main()
