"""
PART 2: Complete the thesis with Chapters 3, 4, 5 and references
This continues from the partial thesis and creates the complete document
"""

import re

def extract_chapters():
    """Extract all chapters from original thesis"""
    with open('thesis_final.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    chapters = {}
    chapter_pattern = r'<div class="chapter" id="chapter(\d+)">(.*?)(?=<div class="chapter" id="chapter|<div class="references"|<div class="appendices"|<div class="page-break-before">|</body>)'
    
    for match in re.finditer(chapter_pattern, content, re.DOTALL):
        chapter_num = match.group(1)
        chapter_content = match.group(2)
        chapters[chapter_num] = chapter_content
    
    # Extract references
    ref_match = re.search(r'<div class="references" id="references">(.*?)</div>\s*<div class="appendices"|<div class="page-break-before">|$', content, re.DOTALL)
    references = ref_match.group(1) if ref_match else ''
    
    if not references:
        # Try alternative pattern
        ref_match = re.search(r'<div class="references" id="references">(.*?)(?=<div class="appendices"|</body>)', content, re.DOTALL)
        references = ref_match.group(1) if ref_match else ''
    
    return chapters, references

def create_chapter3(ch3_orig, ch4_orig):
    """Create Chapter 3: Research Methodology from original Chapters 3 and 4"""
    
    html = '''
    <!-- ============================================
     CHAPTER 3: RESEARCH METHODOLOGY
     ============================================ -->
    <div class="chapter page-break-before" id="chapter3">
        <h1><span class="chapter-number">CHAPTER 3</span><br>RESEARCH METHODOLOGY</h1>
        
        <p>This chapter presents our research methodology, encompassing system requirements analysis, design approach, architectural decisions, and development workflows that guided the implementation of the AI-powered document chatbot system.</p>
        
        <h2>3.1 SYSTEM REQUIREMENTS ANALYSIS</h2>
'''
    
    # Extract functional and non-functional requirements from Chapter 3
    func_req = re.search(r'(<h2 id="ch3-1">.*?Functional Requirements</h2>.*?)(?=<h2 id="ch3-2">)', ch3_orig, re.DOTALL)
    if func_req:
        content = func_req.group(1)
        content = re.sub(r'<h2 id="ch3-1">.*?</h2>', '<h3>3.1.1 Functional Requirements</h3>', content)
        # Fix subsection headers
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    nonfunc_req = re.search(r'(<h2 id="ch3-2">.*?Non-Functional Requirements</h2>.*?)(?=<h2 id="ch3-3">)', ch3_orig, re.DOTALL)
    if nonfunc_req:
        content = nonfunc_req.group(1)
        content = re.sub(r'<h2 id="ch3-2">.*?</h2>', '<h3>3.1.2 Non-Functional Requirements</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    # Add System Design section from Chapter 4
    html += '''
        <h2>3.2 SYSTEM DESIGN APPROACH</h2>
        <p>The system design follows a modern three-tier architecture with clear separation of concerns, designed to be modular, scalable, and maintainable.</p>
'''
    
    # Extract architecture sections from Chapter 4
    arch_match = re.search(r'(<h2 id="ch4-1">.*?High-Level Architecture</h2>.*?)(?=<h2 id="ch4-2">)', ch4_orig, re.DOTALL)
    if arch_match:
        content = arch_match.group(1)
        content = re.sub(r'<h2 id="ch4-1">.*?</h2>', '<h3>3.2.1 High-Level Architecture</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    backend_match = re.search(r'(<h2 id="ch4-2">.*?Backend Architecture</h2>.*?)(?=<h2 id="ch4-3">)', ch4_orig, re.DOTALL)
    if backend_match:
        content = backend_match.group(1)
        content = re.sub(r'<h2 id="ch4-2">.*?</h2>', '<h3>3.2.2 Backend Architecture</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        content = re.sub(r'<h4>(.*?Module)</h4>', r'<p><strong>\1</strong></p>', content)
        html += content
    
    frontend_match = re.search(r'(<h2 id="ch4-3">.*?Frontend Architecture</h2>.*?)(?=<h2 id="ch4-4">)', ch4_orig, re.DOTALL)
    if frontend_match:
        content = frontend_match.group(1)
        content = re.sub(r'<h2 id="ch4-3">.*?</h2>', '<h3>3.2.3 Frontend Architecture</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    db_match = re.search(r'(<h2 id="ch4-4">.*?Database Design</h2>.*?)(?=<h2 id="ch4-5">)', ch4_orig, re.DOTALL)
    if db_match:
        content = db_match.group(1)
        content = re.sub(r'<h2 id="ch4-4">.*?</h2>', '<h3>3.2.4 Database Design</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    # Add Use Case Analysis
    usecase_match = re.search(r'(<h2 id="ch3-3">.*?Use Case Analysis</h2>.*?)(?=<h2 id="ch3-4">)', ch3_orig, re.DOTALL)
    if usecase_match:
        content = usecase_match.group(1)
        content = re.sub(r'<h2 id="ch3-3">.*?</h2>', '<h2>3.3 USE CASE ANALYSIS</h2>', content)
        content = re.sub(r'<h3>(Use Case \d+:.*?)</h3>', r'<h3>\1</h3>', content)
        html += content
    
    # Add Data Flow
    dataflow_match = re.search(r'(<h2 id="ch4-5">.*?Data Flow and Workflows</h2>.*?)(?=</div>)', ch4_orig, re.DOTALL)
    if dataflow_match:
        content = dataflow_match.group(1)
        content = re.sub(r'<h2 id="ch4-5">.*?</h2>', '<h2>3.4 DATA FLOW AND WORKFLOWS</h2>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h3>\1', content)
        html += content
    
    # Add Summary
    html += '''
        <h2>3.5 SUMMARY</h2>
        <p>This chapter presented the comprehensive research methodology employed in developing the AI-powered document chatbot system. We detailed the systematic requirements analysis process that identified both functional and non-functional requirements,  ensuring the system meets user needs while maintaining quality attributes such as performance, security, and usability.</p>
        <p>The system design approach emphasized modularity and separation of concerns, resulting in a three-tier architecture comprising presentation, business logic, and data layers. The backend architecture leverages Flask for API development with specialized modules for authentication, document processing, hybrid retrieval, and vision AI. The frontend provides an intuitive, responsive interface built with vanilla JavaScript for optimal performance.</p>
        <p>The database design normalization principles while optimizing for query performance, with strategic indexing to support frequent operations. Data flow workflows were carefully designed to handle document upload, indexing, query processing, and response generation efficiently. Use case analysis validated that the system addresses real-world scenarios effectively.</p>
        <p>This methodology provided a solid foundation for implementation, ensuring that technical decisions were guided by clear requirements and established design principles. The modular architecture facilitates testing, maintenance, and future enhancements, positioning the system for long-term evolution and improvement.</p>
    </div>
'''
    
    return html

def create_chapter4(ch5_orig, ch6_orig, ch7_orig):
    """Create Chapter 4: Results and Discussion from original Chapters 5, 6, 7"""
    
    html = '''
    <!-- ============================================
     CHAPTER 4: RESULTS AND DISCUSSION
     ============================================ -->
    <div class="chapter page-break-before" id="chapter4">
        <h1><span class="chapter-number">CHAPTER 4</span><br>RESULTS AND DISCUSSION</h1>
        
        <p>This chapter presents the implementation details, testing methodology, results analysis, and discussion of our AI-powered document chatbot system. We describe the technology stack, demonstrate system capabilities, analyze performance metrics, and discuss challenges encountered during development.</p>
        
        <h2>4.1 IMPLEMENTATION</h2>
'''
    
    # Extract Technology Stack from Chapter 5
    tech_match = re.search(r'(<h2 id="ch5-1">.*?Technology Stack</h2>.*?)(?=<h2 id="ch5-2">)', ch5_orig, re.DOTALL)
    if tech_match:
        content = tech_match.group(1)
        content = re.sub(r'<h2 id="ch5-1">.*?</h2>', '<h3>4.1.1 Technology Stack</h3>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h4>\1', content)
        html += content
    
    # Add key implementation sections from Chapter 5
    auth_match = re.search(r'(<h2 id="ch5-2">.*?Authentication System</h2>.*?)(?=<h2 id="ch5-3">)', ch5_orig, re.DOTALL)
    if auth_match:
        content = auth_match.group(1)
        content = re.sub(r'<h2 id="ch5-2">.*?</h2>', '<h3>4.1.2 Authentication System</h3>', content)
        html += content
    
    rag_match = re.search(r'(<h2 id="ch5-3">.*?RAG Pipeline Implementation</h2>.*?)(?=<h2 id="ch5-4">)', ch5_orig, re.DOTALL)
    if rag_match:
        content = rag_match.group(1)
        content = re.sub(r'<h2 id="ch5-3">.*?</h2>', '<h3>4.1.3 RAG Pipeline Implementation</h3>', content)
        html += content
    
    vision_match = re.search(r'(<h2 id="ch5-4">.*?Vision AI Integration</h2>.*?)(?=<h2 id="ch5-5">)', ch5_orig, re.DOTALL)
    if vision_match:
        content = vision_match.group(1)
        content = re.sub(r'<h2 id="ch5-4">.*?</h2>', '<h3>4.1.4 Vision AI Integration</h3>', content)
        html += content
    
    frontend_match = re.search(r'(<h2 id="ch5-8">.*?Frontend Development</h2>.*?)(?=</div>)', ch5_orig, re.DOTALL)
    if frontend_match:
        content = frontend_match.group(1)
        content = re.sub(r'<h2 id="ch5-8">.*?</h2>', '<h3>4.1.5 Frontend Development</h3>', content)
        html += content
    
    # Add Testing section from Chapter 6
    html += '''
        <h2>4.2 TESTING AND VALIDATION</h2>
'''
    
    # Extract testing sections
    test_strategy = re.search(r'(<h2 id="ch6-1">.*?Testing Strategy</h2>.*?)(?=<h2 id="ch6-2">)', ch6_orig, re.DOTALL)
    if test_strategy:
        content = test_strategy.group(1)
        content = re.sub(r'<h2 id="ch6-1">.*?</h2>', '<h3>4.2.1 Testing Strategy</h3>', content)
        html += content
    
    func_test = re.search(r'(<h2 id="ch6-2">.*?Functional Testing</h2>.*?)(?=<h2 id="ch6-3">)', ch6_orig, re.DOTALL)
    if func_test:
        content = func_test.group(1)
        content = re.sub(r'<h2 id="ch6-2">.*?</h2>', '<h3>4.2.2 Functional Testing</h3>', content)
        html += content
    
    perf_test = re.search(r'(<h2 id="ch6-3">.*?Performance Testing</h2>.*?)(?=<h2 id="ch6-4">)', ch6_orig, re.DOTALL)
    if perf_test:
        content = perf_test.group(1)
        content = re.sub(r'<h2 id="ch6-3">.*?</h2>', '<h3>4.2.3 Performance Testing</h3>', content)
        html += content
    
    sec_test = re.search(r'(<h2 id="ch6-4">.*?Security Testing</h2>.*?)(?=<h2 id="ch6-5">)', ch6_orig, re.DOTALL)
    if sec_test:
        content = sec_test.group(1)
        content = re.sub(r'<h2 id="ch6-4">.*?</h2>', '<h3>4.2.4 Security Testing</h3>', content)
        html += content
    
    # Add Results Analysis from Chapter 7
    html += '''
        <h2>4.3 RESULTS ANALYSIS</h2>
'''
    
    capabilities = re.search(r'(<h2 id="ch7-1">.*?System Capabilities</h2>.*?)(?=<h2 id="ch7-2">)', ch7_orig, re.DOTALL)
    if capabilities:
        content = capabilities.group(1)
        content = re.sub(r'<h2 id="ch7-1">.*?</h2>', '<h3>4.3.1 System Capabilities</h3>', content)
        html += content
    
    perf_analysis = re.search(r'(<h2 id="ch7-2">.*?Performance Analysis</h2>.*?)(?=<h2 id="ch7-3">)', ch7_orig, re.DOTALL)
    if perf_analysis:
        content = perf_analysis.group(1)
        content = re.sub(r'<h2 id="ch7-2">.*?</h2>', '<h3>4.3.2 Performance Analysis</h3>', content)
        html += content
    
    comparative = re.search(r'(<h2 id="ch7-4">.*?Comparative Analysis</h2>.*?)(?=<h2 id="ch7-5">)', ch7_orig, re.DOTALL)
    if comparative:
        content = comparative.group(1)
        content = re.sub(r'<h2 id="ch7-4">.*?</h2>', '<h3>4.3.3 Comparative Analysis</h3>', content)
        html += content
    
    # Add Discussion
    html += '''
        <h2>4.4 DISCUSSION</h2>
'''
    
    challenges = re.search(r'(<h2 id="ch7-3">.*?Challenges and Solutions</h2>.*?)(?=<h2 id="ch7-4">)', ch7_orig, re.DOTALL)
    if challenges:
        content = challenges.group(1)
        content = re.sub(r'<h2 id="ch7-3">.*?</h2>', '<h3>4.4.1 Challenges and Solutions</h3>', content)
        html += content
    
    limitations = re.search(r'(<h2 id="ch7-5">.*?Limitations</h2>.*?)(?=</div>)', ch7_orig, re.DOTALL)
    if limitations:
        content = limitations.group(1)
        content = re.sub(r'<h2 id="ch7-5">.*?</h2>', '<h3>4.4.2 Limitations</h3>', content)
        html += content
    
    # Add Summary
    html += '''
        <h2>4.5 SUMMARY</h2>
        <p>This chapter presented the comprehensive implementation, testing, and evaluation of the AI-powered document chatbot system. The implementation successfully integrated multiple technologies including Flask, SentenceTransformers, FAISS, BM25, BLIP, and Tesseract into a cohesive, production-ready application.</p>
        <p>Testing and validation demonstrated that the system meets all functional and non-functional requirements. Performance testing showed query response times averaging under 3 seconds, with the hybrid retrieval approach outperforming single-method alternatives. Security testing confirmed robust authentication and data protection mechanisms. Usability testing revealed high user satisfaction with the intuitive interface and responsive design.</p>
        <p>Results analysis highlighted the system's capabilities in handling diverse document formats, processing complex queries, and providing accurate responses grounded in retrieved context. The hybrid retrieval strategy proved particularly effective, combining the precision of keyword matching with the semantic understanding of embedding-based search.</p>
        <p>Discussion of challenges revealed valuable insights into RAG system development, including the importance of proper chunking strategies, index management, and error handling. Identified limitations provide clear directions for future enhancements, while the overall evaluation confirms the system's readiness for deployment in educational and small business contexts.</p>
    </div>
'''
    
    return html

def create_chapter5(ch8_orig):
    """Create Chapter 5: Conclusion and Future Directions from original Chapter 8"""
    
    html = '''
    <!-- ============================================
     CHAPTER 5: CONCLUSION AND FUTURE DIRECTIONS
     ============================================ -->
    <div class="chapter page-break-before" id="chapter5">
        <h1><span class="chapter-number">CHAPTER 5</span><br>CONCLUSION AND FUTURE DIRECTIONS</h1>
        
        <p>This final chapter summarizes the achievements of this project, reflects on lessons learned during development, and outlines potential directions for future enhancement and research.</p>
'''
    
    # Extract sections from Chapter 8
    achievements = re.search(r'(<h2 id="ch8-1">.*?Summary of Achievements</h2>.*?)(?=<h2 id="ch8-2">)', ch8_orig, re.DOTALL)
    if achievements:
        content = achievements.group(1)
        content = re.sub(r'<h2 id="ch8-1">.*?</h2>', '<h2>5.1 SUMMARY OF ACHIEVEMENTS</h2>', content)
        html += content
    
    lessons = re.search(r'(<h2 id="ch8-2">.*?Lessons Learned</h2>.*?)(?=<h2 id="ch8-3">)', ch8_orig, re.DOTALL)
    if lessons:
        content = lessons.group(1)
        content = re.sub(r'<h2 id="ch8-2">.*?</h2>', '<h2>5.2 LESSONS LEARNED</h2>', content)
        html += content
    
    future = re.search(r'(<h2 id="ch8-3">.*?Future Enhancements</h2>.*?)(?=<h2 id="ch8-4">)', ch8_orig, re.DOTALL)
    if future:
        content = future.group(1)
        content = re.sub(r'<h2 id="ch8-3">.*?</h2>', '<h2>5.3 FUTURE ENHANCEMENTS</h2>', content)
        content = re.sub(r'<h3>(\d+\.\d+\.\d+)', r'<h3>\1', content)
        html += content
    
    concluding = re.search(r'(<h2 id="ch8-4">.*?Concluding Remarks</h2>.*?)(?=</div>)', ch8_orig, re.DOTALL)
    if concluding:
        content = concluding.group(1)
        content = re.sub(r'<h2 id="ch8-4">.*?</h2>', '<h2>5.4 CONCLUDING REMARKS</h2>', content)
        html += content
    
    #  Summary for Chapter 5
    html += '''
        <h2>5.5 SUMMARY</h2>
        <p>This thesis successfully demonstrated the design, implementation, and evaluation of an AI-powered document chatbot system leveraging Retrieval-Augmented Generation technology. The project achieved all stated objectives, delivering a production-ready system that combines semantic search, lexical retrieval, and vision AI capabilities in an intuitive web interface.</p>
        <p>Key achievements include the successful integration of hybrid retrieval methods, comprehensive multimodal document processing, robust authentication and user management, and extensive testing demonstrating superior performance compared to single-method approaches. The system represents a significant contribution to making advanced AI technologies accessible and practical for real-world document interaction scenarios.</p>
        <p>Lessons learned throughout this project encompass technical insights into RAG architecture, the critical importance of user experience design, and practical considerations for deploying AI systems. These insights will inform future development efforts and contribute to the broader knowledge base of conversational AI implementation.</p>
        <p>Future directions outlined in this chapter provide a clear roadmap for evolution, from short-term optimizations to long-term enterprise features and research opportunities. The modular architecture and comprehensive documentation position this system as both a practical solution and a foundation for continued innovation in intelligent document interaction.</p>
    </div>
'''
    
    return html

def main():
    print("Extracting chapters from original thesis...")
    chapters, references = extract_chapters()
    
    print(f"Found {len(chapters)} chapters")
    print(f"References: {len(references)} chars")
    
    # Read the partial thesis
    with open('thesis_restructured_partial.html', 'r', encoding='utf-8') as f:
        partial = f.read()
    
    # Create remaining chapters
    print("\nGenerating Chapter 3...")
    ch3 = create_chapter3(chapters['3'], chapters['4'])
    
    print("Generating Chapter 4...")
    ch4 = create_chapter4(chapters['5'], chapters['6'], chapters['7'])
    
    print("Generating Chapter 5...")
    ch5 = create_chapter5(chapters['8'])
    
    # Combine everything
    full_thesis = partial + ch3 + ch4 + ch5
    
    # Add references
    full_thesis += '''
    <!-- ============================================
     REFERENCES
     ============================================ -->
    <div class="references page-break-before" id="references">
'''    + references + '''
    </div>

</body>
</html>
'''
    
    # Write final file
    output_file = 'thesis_restructured.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_thesis)
    
    print(f"\n✓ Complete restructured thesis generated:")
    print(f"  Output file: {output_file}")
    print(f"  Total size: {len(full_thesis):,} characters")
    print("\nStructure:")
    print("  - Front Matter (Certificate, Declaration, Copyright, Dedication, Acknowledgements, Abstract)")
    print("  - Chapter 1: Introduction")
    print("  - Chapter 2: Background")
    print("  - Chapter 3: Research Methodology")
    print("  - Chapter 4: Results and Discussion")
    print("  - Chapter 5: Conclusion and Future Directions")
    print("  - References")
    print("\nNext steps:")
    print("  1. Review the generated file")
    print("  2. Add Table of Contents, List of Tables, List of Figures, Abbreviations")
    print("  3. Renumber tables and figures according to new chapter structure")
    print("  4. Fill in student registration numbers in cover page")
    print("  5. Add dedication text")

if __name__ == '__main__':
    main()
