"""
Add clickable TOC links and insert all images into the restructured thesis
"""

import re

def add_toc_links_and_images():
    # Read the restructured thesis
    with open('thesis_restructured.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. First, make sure all sections have proper IDs
    # Update TOC with clickable links - Replace the current TOC section
    toc_section = '''    <!-- ============================================
     TABLE OF CONTENTS
     ============================================ -->
    <div class="page-break-before">
        <h2 style="text-align: center;">TABLE OF CONTENTS</h2>
        
        <div style="margin-top: 2rem;">
            <p><strong>DECLARATION</strong> .................................................. IV</p>
            <p><strong>COPY RIGHTS</strong> .................................................. V</p>
            <p><strong>DEDICATION</strong> .................... VI</p>
            <p><strong>ACKNOWLEDGEMENTS</strong> .................................................. VII</p>
            <p><strong>ABSTRACT</strong> .................................................. VIII</p>
            <p><strong>TABLE OF CONTENTS</strong> .................................................. IX</p>
            <p><strong>LIST OF TABLES</strong> .................................................. XI</p>
            <p><strong>LIST OF FIGURES</strong> .................................................. XII</p>
            <p><strong>ABBREVIATIONS</strong> .................................................. XIII</p>
            
            <br>
            
            <p><strong><a href="#chapter1" style="text-decoration: none; color: inherit;">CHAPTER 1: INTRODUCTION</a></strong> .................................................. 1</p>
            <p style="margin-left: 2rem;"><a href="#ch1-1" style="text-decoration: none; color: inherit;">1.1 MOTIVATION</a> .................................................. 1</p>
            <p style="margin-left: 2rem;"><a href="#ch1-2" style="text-decoration: none; color: inherit;">1.2 CONTRIBUTIONS OF THE THESIS</a> .................................................. 2</p>
            <p style="margin-left: 4rem;"><a href="#ch1-2-1" style="text-decoration: none; color: inherit;">1.2.1 Technical Contributions</a> .................................................. 2</p>
            <p style="margin-left: 4rem;"><a href="#ch1-2-2" style="text-decoration: none; color: inherit;">1.2.2 Practical Contributions</a> .................................................. 2</p>
            <p style="margin-left: 2rem;"><a href="#ch1-3" style="text-decoration: none; color: inherit;">1.3 STRUCTURE OF THE THESIS</a> .................................................. 3</p>
            
            <br>
            
            <p><strong><a href="#chapter2" style="text-decoration: none; color: inherit;">CHAPTER 2: BACKGROUND</a></strong> .................................................. 4</p>
            <p style="margin-left: 2rem;"><a href="#ch2-1" style="text-decoration: none; color: inherit;">2.1 Evolution of Chatbot Technology</a> .................................................. 4</p>
            <p style="margin-left: 2rem;"><a href="#ch2-2" style="text-decoration: none; color: inherit;">2.2 Retrieval-Augmented Generation (RAG)</a> .................................................. 5</p>
            <p style="margin-left: 2rem;"><a href="#ch2-3" style="text-decoration: none; color: inherit;">2.3 Document Processing and Embeddings</a> .................................................. 6</p>
            <p style="margin-left: 2rem;"><a href="#ch2-4" style="text-decoration: none; color: inherit;">2.4 Vector Databases and Semantic Search</a> .................................................. 7</p>
            <p style="margin-left: 2rem;"><a href="#ch2-5" style="text-decoration: none; color: inherit;">2.5 Hybrid Retrieval Methods</a> .................................................. 8</p>
            <p style="margin-left: 2rem;"><a href="#ch2-6" style="text-decoration: none; color: inherit;">2.6 Vision AI and Multimodal Learning</a> .................................................. 9</p>
            <p style="margin-left: 2rem;"><a href="#ch2-7" style="text-decoration: none; color: inherit;">2.7 Related Systems and Comparative Analysis</a> .................................................. 10</p>
            <p style="margin-left: 2rem;"><a href="#ch2-8" style="text-decoration: none; color: inherit;">2.8 SUMMARY</a> .................................................. 11</p>
            
            <br>
            
            <p><strong><a href="#chapter3" style="text-decoration: none; color: inherit;">CHAPTER 3: RESEARCH METHODOLOGY</a></strong> .................................................. 12</p>
            <p style="margin-left: 2rem;"><a href="#ch3-1" style="text-decoration: none; color: inherit;">3.1 SYSTEM REQUIREMENTS ANALYSIS</a> .................................................. 12</p>
            <p style="margin-left: 2rem;"><a href="#ch3-2" style="text-decoration: none; color: inherit;">3.2 SYSTEM DESIGN APPROACH</a> .................................................. 17</p>
            <p style="margin-left: 2rem;"><a href="#ch3-3" style="text-decoration: none; color: inherit;">3.3 USE CASE ANALYSIS</a> .................................................. 21</p>
            <p style="margin-left: 2rem;"><a href="#ch3-4" style="text-decoration: none; color: inherit;">3.4 DATA FLOW AND WORKFLOWS</a> .................................................. 22</p>
            <p style="margin-left: 2rem;"><a href="#ch3-5" style="text-decoration: none; color: inherit;">3.5 SUMMARY</a> .................................................. 23</p>
            
            <br>
            
            <p><strong><a href="#chapter4" style="text-decoration: none; color: inherit;">CHAPTER 4: RESULTS AND DISCUSSION</a></strong> .................................................. 24</p>
            <p style="margin-left: 2rem;"><a href="#ch4-1" style="text-decoration: none; color: inherit;">4.1 IMPLEMENTATION</a> .................................................. 24</p>
            <p style="margin-left: 2rem;"><a href="#ch4-2" style="text-decoration: none; color: inherit;">4.2 TESTING AND VALIDATION</a> .................................................. 29</p>
            <p style="margin-left: 2rem;"><a href="#ch4-3" style="text-decoration: none; color: inherit;">4.3 RESULTS ANALYSIS</a> .................................................. 33</p>
            <p style="margin-left: 2rem;"><a href="#ch4-4" style="text-decoration: none; color: inherit;">4.4 DISCUSSION</a> .................................................. 36</p>
            <p style="margin-left: 2rem;"><a href="#ch4-5" style="text-decoration: none; color: inherit;">4.5 SUMMARY</a> .................................................. 38</p>
            
            <br>
            
            <p><strong><a href="#chapter5" style="text-decoration: none; color: inherit;">CHAPTER 5: CONCLUSION AND FUTURE DIRECTIONS</a></strong> .................................................. 39</p>
            <p style="margin-left: 2rem;"><a href="#ch5-1" style="text-decoration: none; color: inherit;">5.1 SUMMARY OF ACHIEVEMENTS</a> .................................................. 39</p>
            <p style="margin-left: 2rem;"><a href="#ch5-2" style="text-decoration: none; color: inherit;">5.2 LESSONS LEARNED</a> .................................................. 40</p>
            <p style="margin-left: 2rem;"><a href="#ch5-3" style="text-decoration: none; color: inherit;">5.3 FUTURE ENHANCEMENTS</a> .................................................. 41</p>
            <p style="margin-left: 2rem;"><a href="#ch5-4" style="text-decoration: none; color: inherit;">5.4 CONCLUDING REMARKS</a> .................................................. 42</p>
            <p style="margin-left: 2rem;"><a href="#ch5-5" style="text-decoration: none; color: inherit;">5.5 SUMMARY</a> .................................................. 43</p>
            
            <br>
            
            <p><strong><a href="#references" style="text-decoration: none; color: inherit;">REFERENCES</a></strong> .................................................. 44</p>
        </div>
    </div>'''
    
    # Replace current TOC
    content = re.sub(
        r'<!-- ============================================\s+TABLE OF CONTENTS\s+============================================ -->(.*?)<!-- ============================================',
        toc_section + '\n\n    <!-- ============================================',
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # 2. Add IDs to headings in Chapter 1
    content = re.sub(r'<h2>1\.1 MOTIVATION</h2>', '<h2 id="ch1-1">1.1 MOTIVATION</h2>', content)
    content = re.sub(r'<h2>1\.2 CONTRIBUTIONS OF THE THESIS</h2>', '<h2 id="ch1-2">1.2 CONTRIBUTIONS OF THE THESIS</h2>', content)
    content = re.sub(r'<h3>1\.2\.1 Technical Contributions</h3>', '<h3 id="ch1-2-1">1.2.1 Technical Contributions</h3>', content)
    content = re.sub(r'<h3>1\.2\.2 Practical Contributions</h3>', '<h3 id="ch1-2-2">1.2.2 Practical Contributions</h3>', content)
    content = re.sub(r'<h2>1\.3 STRUCTURE OF THE THESIS</h2>', '<h2 id="ch1-3">1.3 STRUCTURE OF THE THESIS</h2>', content)
    
    # Add IDs to Chapter 2-5 summary sections
    content = re.sub(r'<h2>2\.8 SUMMARY</h2>', '<h2 id="ch2-8">2.8 SUMMARY</h2>', content)
    content = re.sub(r'<h2>3\.1 SYSTEM REQUIREMENTS ANALYSIS</h2>', '<h2 id="ch3-1">3.1 SYSTEM REQUIREMENTS ANALYSIS</h2>', content)
    content = re.sub(r'<h2>3\.2 SYSTEM DESIGN APPROACH</h2>', '<h2 id="ch3-2">3.2 SYSTEM DESIGN APPROACH</h2>', content)
    content = re.sub(r'<h2>3\.3 USE CASE ANALYSIS</h2>', '<h2 id="ch3-3">3.3 USE CASE ANALYSIS</h2>', content)
    content = re.sub(r'<h2>3\.4 DATA FLOW AND WORKFLOWS</h2>', '<h2 id="ch3-4">3.4 DATA FLOW AND WORKFLOWS</h2>', content)
    content = re.sub(r'<h2>3\.5 SUMMARY</h2>', '<h2 id="ch3-5">3.5 SUMMARY</h2>', content)
    content = re.sub(r'<h2>4\.1 IMPLEMENTATION</h2>', '<h2 id="ch4-1">4.1 IMPLEMENTATION</h2>', content)
    content = re.sub(r'<h2>4\.2 TESTING AND VALIDATION</h2>', '<h2 id="ch4-2">4.2 TESTING AND VALIDATION</h2>', content)
    content = re.sub(r'<h2>4\.3 RESULTS ANALYSIS</h2>', '<h2 id="ch4-3">4.3 RESULTS ANALYSIS</h2>', content)
    content = re.sub(r'<h2>4\.4 DISCUSSION</h2>', '<h2 id="ch4-4">4.4 DISCUSSION</h2>', content)
    content = re.sub(r'<h2>4\.5 SUMMARY</h2>', '<h2 id="ch4-5">4.5 SUMMARY</h2>', content)
    content = re.sub(r'<h2>5\.1 SUMMARY OF ACHIEVEMENTS</h2>', '<h2 id="ch5-1">5.1 SUMMARY OF ACHIEVEMENTS</h2>', content)
    content = re.sub(r'<h2>5\.2 LESSONS LEARNED</h2>', '<h2 id="ch5-2">5.2 LESSONS LEARNED</h2>', content)
    content = re.sub(r'<h2>5\.3 FUTURE ENHANCEMENTS</h2>', '<h2 id="ch5-3">5.3 FUTURE ENHANCEMENTS</h2>', content)
    content = re.sub(r'<h2>5\.4 CONCLUDING REMARKS</h2>', '<h2 id="ch5-4">5.4 CONCLUDING REMARKS</h2>', content)
    content = re.sub(r'<h2>5\.5 SUMMARY</h2>', '<h2 id="ch5-5">5.5 SUMMARY</h2>', content)
    
    # 3. Now add images to appropriate sections
    
    # Chapter 2: Background - Add chatbot evolution image
    ch2_1_insert = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/chatbot evolution eliza.jpg" alt="Evolution of Chatbot Technology" style="max-width: 80%; height: auto;">
            <figcaption><strong>FIGURE 2 1:</strong> Evolution of Chatbot Technology - From ELIZA to Modern AI</figcaption>
        </figure>
'''
    content = content.replace('<h2 id="ch2-2">2.2 Retrieval-Augmented Generation (RAG)</h2>', 
                             ch2_1_insert + '\n        <h2 id="ch2-2">2.2 Retrieval-Augmented Generation (RAG)</h2>')
    
    # Chapter 3: Add architecture diagrams
    ch3_architecture = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/6-layer_architecture.png" alt="High-Level System Architecture" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 3 1:</strong> High-Level 6-Layer System Architecture</figcaption>
        </figure>
'''
    
    ch3_erd = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/ERD of database.png" alt="Database Entity-Relationship Diagram" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 3 2:</strong> Database Entity-Relationship Diagram</figcaption>
        </figure>
'''
    
    ch3_doc_flow = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/doc and image upload work flow.png" alt="Document Processing Workflow" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 3 3:</strong> Document and Image Upload Workflow</figcaption>
        </figure>
'''
    
    ch3_query_flow = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/user query detailed flow chart process.png" alt="Query Processing Flow" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 3 4:</strong> User Query Processing Detailed Flow</figcaption>
        </figure>
'''
    
    ch3_rag_pipeline = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/FAISS BM25 Docs Pipeline-2026-01-20-190558.png" alt="RAG Pipeline Architecture" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 3 5:</strong> Hybrid RAG Pipeline with FAISS and BM25</figcaption>
        </figure>
'''
    
    # Insert Chapter 3 images at appropriate places
    content = content.replace('<h2 id="ch3-2">3.2 SYSTEM DESIGN APPROACH</h2>',
                             ch3_architecture + '\n        <h2 id="ch3-2">3.2 SYSTEM DESIGN APPROACH</h2>')
    content = content.replace('<h2 id="ch3-3">3.3 USE CASE ANALYSIS</h2>',
                             ch3_erd + '\n        <h2 id="ch3-3">3.3 USE CASE ANALYSIS</h2>')
    content = content.replace('<h2 id="ch3-4">3.4 DATA FLOW AND WORKFLOWS</h2>',
                             ch3_doc_flow + '\n        ' + ch3_query_flow + '\n        ' + ch3_rag_pipeline + '\n        <h2 id="ch3-4">3.4 DATA FLOW AND WORKFLOWS</h2>')
    
    # Chapter 4: Add UI screenshots and performance charts
    ch4_ui_screenshots = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/chatuiscreen-dark.PNG" alt="Chat Interface - Dark Mode" style="max-width: 90%; height: auto;">
            <figcaption><strong>FIGURE 4 1:</strong> User Interface - Chat Screen (Dark Mode)</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/login.PNG" alt="Login Screen" style="max-width: 70%; height: auto;">
            <figcaption><strong>FIGURE 4 2:</strong> User Authentication - Login Interface</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/Registration.PNG" alt="Registration Screen" style="max-width: 70%; height: auto;">
            <figcaption><strong>FIGURE 4 3:</strong> User Registration Interface with OTP Verification</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/profile.PNG" alt="Profile Screen" style="max-width: 70%; height: auto;">
            <figcaption><strong>FIGURE 4 4:</strong> User Profile Management Interface</figcaption>
        </figure>
'''
    
    ch4_benchmark = '''
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/benchmark_results.png" alt="Performance Benchmark Results" style="max-width: 80%; height: auto;">
            <figcaption><strong>FIGURE 4 5:</strong> Retrieval Accuracy Comparison - Hybrid vs Single Methods</figcaption>
        </figure>
'''
    
    # Insert Chapter 4 images
    content = content.replace('<h2 id="ch4-2">4.2 TESTING AND VALIDATION</h2>',
                             ch4_ui_screenshots + '\n        <h2 id="ch4-2">4.2 TESTING AND VALIDATION</h2>')
    content = content.replace('<h2 id="ch4-4">4.4 DISCUSSION</h2>',
                             ch4_benchmark + '\n        <h2 id="ch4-4">4.4 DISCUSSION</h2>')
    
    # Save the updated file
    with open('thesis_restructured.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Added clickable links to Table of Contents")
    print("✓ Added IDs to all section headings")
    print("✓ Inserted images:")
    print("  - Chapter 2: Chatbot evolution diagram")
    print("  - Chapter 3: 6-layer architecture, ERD, workflows (5 images)")
    print("  - Chapter 4: UI screenshots (4 images) + performance chart")
    print("\nTotal images added: 11 figures")

if __name__ == '__main__':
    add_toc_links_and_images()
