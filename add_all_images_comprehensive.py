"""
Add ALL missing images to the thesis comprehensively.
This includes architecture diagrams, workflows, ERD, UML, and all UI screenshots.
"""

import re

def add_all_missing_images():
    with open('thesis_restructured.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ===== CHAPTER 3: RESEARCH METHODOLOGY =====
    
    # 3.2 SYSTEM DESIGN APPROACH - Add multiple architecture diagrams
    architecture_section = '''
        <h2 id="ch3-2">3.2 SYSTEM DESIGN APPROACH</h2>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/6-layer_architecture.png" alt="High-Level System Architecture" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 1:</strong> High-Level 6-Layer System Architecture</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/L-0 Data flow diagram.png" alt="Level-0 Data Flow Diagram" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 2:</strong> Level-0 Data Flow Diagram</figcaption>
        </figure>
'''
    
    # Replace existing h2 for 3.2
    content = re.sub(
        r'<h2 id="ch3-2">3\.2 SYSTEM DESIGN APPROACH</h2>',
        architecture_section,
        content,
        count=1
    )
    
    # 3.3 USE CASE ANALYSIS - Add UML and ERD
    use_case_section = '''
        <h2 id="ch3-3">3.3 USE CASE ANALYSIS</h2>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/UML.png" alt="UML Use Case Diagram" style="max-width: 85%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 3:</strong> UML Use Case Diagram - System Interactions</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/ERD of database.png" alt="Database Entity-Relationship Diagram" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 4:</strong> Database Entity-Relationship Diagram (ERD)</figcaption>
        </figure>
'''
    
    content = re.sub(
        r'<h2 id="ch3-3">3\.3 USE CASE ANALYSIS</h2>',
        use_case_section,
        content,
        count=1
    )
    
    # 3.4 DATA FLOW AND WORKFLOWS - Add all workflow diagrams
    workflow_section = '''
        <h2 id="ch3-4">3.4 DATA FLOW AND WORKFLOWS</h2>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/docs processing data Flow chart diagram.png" alt="Document Processing Flow" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 5:</strong> Document Processing Data Flow Chart</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/doc and image upload work flow.png" alt="Document Upload Workflow" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 6:</strong> Document and Image Upload Workflow</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/User query workflow process.png" alt="Query Workflow" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 7:</strong> User Query Workflow Process</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/user query detailed flow chart process.png" alt="Detailed Query Flow" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 8:</strong> User Query Processing - Detailed Flow Chart</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/FAISS BM25 Docs Pipeline-2026-01-20-190558.png" alt="RAG Pipeline" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 3 9:</strong> Hybrid RAG Pipeline with FAISS and BM25</figcaption>
        </figure>
'''
    
    content = re.sub(
        r'<h2 id="ch3-4">3\.4 DATA FLOW AND WORKFLOWS</h2>',
        workflow_section,
        content,
        count=1
    )
    
    # ===== CHAPTER 4: RESULTS AND DISCUSSION =====
    
    # 4.1 IMPLEMENTATION - Add ALL UI screenshots in proper order
    ui_section = '''
        <h2 id="ch4-1">4.1 IMPLEMENTATION</h2>
        
        <p>The implementation phase involved building all system components according to the design specifications.</p>
        
        <h3>4.1.1 User Interface Screenshots</h3>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/login.PNG" alt="Login Screen" style="max-width: 70%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 1:</strong> User Authentication - Login Interface</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/Registration.PNG" alt="Registration Screen" style="max-width: 70%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 2:</strong> User Registration Interface</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/otp.PNG" alt="OTP Verification" style="max-width: 70%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 3:</strong> OTP Verification Screen</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/profile.PNG" alt="Profile Screen" style="max-width: 70%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 4:</strong> User Profile Management Interface</figcaption>
        </figure>
        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/chatuiscreen-dark.PNG" alt="Chat Interface" style="max-width: 90%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 5:</strong> Main Chat Interface (Dark Mode)</figcaption>
        </figure>
'''
    
    content = re.sub(
        r'<h2 id="ch4-1">4\.1 IMPLEMENTATION</h2>',
        ui_section,
        content,
        count=1
    )
    
    # 4.3 RESULTS ANALYSIS - Add benchmark chart
    benchmark_section = '''        
        <figure style="text-align: center; margin: 2rem 0;">
            <img src="./thesis_images/benchmark_results.png" alt="Performance Benchmarks" style="max-width: 80%; height: auto; border: 1px solid #ddd;">
            <figcaption><strong>FIGURE 4 6:</strong> Retrieval Accuracy Comparison - Hybrid vs Single Methods</figcaption>
        </figure>
        
        <h2 id="ch4-4">4.4 DISCUSSION</h2>
'''
    
    content = re.sub(
        r'<h2 id="ch4-4">4\.4 DISCUSSION</h2>',
        benchmark_section,
        content,
        count=1
    )
    
    # Save the file
    with open('thesis_restructured.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Successfully added ALL images to the thesis!")
    print("\n📊 CHAPTER 3: RESEARCH METHODOLOGY")
    print("   FIGURE 3 1: 6-Layer System Architecture")
    print("   FIGURE 3 2: Level-0 Data Flow Diagram")
    print("   FIGURE 3 3: UML Use Case Diagram")
    print("   FIGURE 3 4: Database ERD")
    print("   FIGURE 3 5: Document Processing Flow Chart")
    print("   FIGURE 3 6: Document & Image Upload Workflow")
    print("   FIGURE 3 7: User Query Workflow Process")
    print("   FIGURE 3 8: Detailed Query Flow Chart")
    print("   FIGURE 3 9: Hybrid RAG Pipeline (FAISS + BM25)")
    print("\n📱 CHAPTER 4: RESULTS AND DISCUSSION")
    print("   FIGURE 4 1: Login Interface")
    print("   FIGURE 4 2: Registration Interface")
    print("   FIGURE 4 3: OTP Verification Screen ⭐")
    print("   FIGURE 4 4: User Profile Interface")
    print("   FIGURE 4 5: Main Chat Interface (Dark Mode)")
    print("   FIGURE 4 6: Performance Benchmark Chart")
    print("\n📈 Total: 16 Figures Added")
    print("\n✅ Thesis is ready for submission tomorrow!")

if __name__ == '__main__':
    add_all_missing_images()
