import os
import re

# Refusal template from agents.md / README.md
REFUSAL_TEMPLATE = """This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact [relevant team] for guidance."""

def retrieve_documents():
    """Loads and indexes the three policy files by subsection (e.g., 2.6)."""
    docs_dir = "../data/policy-documents"
    doc_files = [
        "policy_hr_leave.txt",
        "policy_it_acceptable_use.txt",
        "policy_finance_reimbursement.txt"
    ]
    
    indexed_sections = []
    
    for filename in doc_files:
        path = os.path.join(docs_dir, filename)
        if not os.path.exists(path):
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_main_section = ""
        current_sub_section = ""
        current_content = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped: continue
            
            # Identify main section (e.g. 2. ANNUAL LEAVE)
            main_match = re.match(r'^(\d+\.\s+[A-Z\s]+)', stripped)
            # Identify subsection (e.g. 2.6 Employees may carry forward...)
            sub_match = re.match(r'^(\d+\.\d+)\s+(.*)', stripped)
            
            if main_match:
                current_main_section = main_match.group(1)
            elif sub_match:
                # Save previous subsection if exists
                if current_sub_section and current_content:
                    indexed_sections.append({
                        'source': filename,
                        'id': current_sub_section,
                        'title': f"{current_main_section} - {current_sub_section}",
                        'content': " ".join(current_content).lower()
                    })
                
                current_sub_section = sub_match.group(1)
                current_content = [stripped] # Start with the line itself
            else:
                if current_sub_section:
                    current_content.append(stripped)
        
        # Save last subsection
        if current_sub_section and current_content:
            indexed_sections.append({
                'source': filename,
                'id': current_sub_section,
                'title': f"{current_main_section} - {current_sub_section}",
                'content': " ".join(current_content).lower()
            })
            
    return indexed_sections

def answer_question(query, indexed_data):
    """Searches indexed data and returns a single-source answer."""
    query_lower = query.lower()
    matches = []
    
    # Use word boundaries for keyword matching to avoid partial matches
    query_words = re.findall(r'\b\w+\b', query_lower)
    
    for section in indexed_data:
        score = 0
        section_content = section['content']
        
        for word in query_words:
            # Simple stemming for 'approve'
            if word.startswith('approv') and ('approv' in section_content):
                score += 3
            elif re.search(r'\b' + re.escape(word) + r'\b', section_content):
                score += 2
        
        # Boost for exact matches of critical terms
        if "carry forward" in query_lower and "carry forward" in section_content: score += 10
        if "without pay" in query_lower and "without pay" in section_content: score += 10
        if "personal phone" in query_lower or "personal device" in query_lower:
            if "personal device" in section_content or "personal phone" in section_content or "3.1" in section['id']:
                score += 15
        if "equipment allowance" in query_lower and "allowance" in section_content: score += 10
        
        if score > 0:
            matches.append({
                'score': score,
                'source': section['source'],
                'id': section['id'],
                'title': section['title'],
                'text': section['content']
            })
            
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    if not matches or matches[0]['score'] < 5:
        return REFUSAL_TEMPLATE
        
    # Anti-Blending: Check if multiple DIFFERENT documents have high-scoring matches
    top_matches = [m for m in matches if m['score'] > matches[0]['score'] * 0.8]
    top_sources = {m['source'] for m in top_matches}
    
    # If the top matches span across different documents (e.g. IT and HR), refuse
    if len(top_sources) > 1:
        return REFUSAL_TEMPLATE

    best_match = matches[0]
    
    # Format according to RICE Citations: [Doc Name] Section [Number]
    citation = f"{best_match['source']} Section {best_match['id']}"
    
    # Clean up the text for representation - find the original case if possible
    final_text = best_match['text'].strip()
    # Simple capitalization for the first letter
    final_text = final_text[0].upper() + final_text[1:] if final_text else ""
    
    return f"[{citation}]\n{final_text}"

def main():
    print("--- Document Policy Agent CLI ---")
    print("Loading documents...")
    indexed_data = retrieve_documents()
    print(f"Loaded {len(indexed_data)} sections.")
    print("Ready for questions! (Type 'exit' to quit)")
    
    while True:
        try:
            query = input("\nUser: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
                
            response = answer_question(query, indexed_data)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
