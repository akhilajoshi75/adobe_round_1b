import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
import pdfplumber
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def is_heading(text, avg_font, font_size, font_threshold=2):
    if not text.strip() or len(text) < 4:
        return False
    if text.isupper():
        return True
    if font_size >= avg_font + font_threshold:
        return True
    if len(text.split()) < 8 and font_size >= avg_font:
        return True
    return False

def extract_sections_from_pdf(pdf_path, docname):
    sections = []
    with pdfplumber.open(pdf_path) as pdf:
        all_fonts = []
        for p in pdf.pages:
            for w in p.extract_words(extra_attrs=["size"]):
                all_fonts.append(w["size"])
        avg_font = sum(all_fonts) / len(all_fonts) if all_fonts else 12

        for i, page in enumerate(pdf.pages):
            words = page.extract_words(extra_attrs=["size"])
            line_objs = []
            lines = {}
            for w in words:
                y0 = int(w["top"] // 2)
                if y0 not in lines:
                    lines[y0] = []
                lines[y0].append(w)
            for y0, wlist in lines.items():
                wlist.sort(key=lambda w: w["x0"])
                line_text = ' '.join(w["text"] for w in wlist)
                avg_line_font = sum(w["size"] for w in wlist) / len(wlist)
                line_objs.append((line_text.strip(), avg_line_font))

            current_section = {"section_title": None, "section_text": "", "page_number": i+1}
            for text, font_size in line_objs:
                if is_heading(text, avg_font, font_size) and len(text) > 4:
                    if current_section["section_title"] and current_section["section_text"]:
                        s = dict(current_section)
                        s["document"] = docname
                        sections.append(s)
                        current_section = {"section_title": None, "section_text": "", "page_number": i+1}
                    current_section["section_title"] = text.strip()
                    current_section["page_number"] = i+1
                else:
                    if current_section["section_title"]:
                        current_section["section_text"] += text.strip() + " "
            if current_section["section_title"] and current_section["section_text"]:
                s = dict(current_section)
                s["document"] = docname
                sections.append(s)
    return sections


BORING_HEADINGS = ["introduction", "about", "preface", "conclusion", "summary"]

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = set(w for w in words if len(w) > 3)
    return keywords

def heading_penalty(heading):
    h = heading.lower().strip()
    return -1 if h in BORING_HEADINGS else 0

def section_dynamic_score(section, persona, job):
    context_keywords = extract_keywords(persona + " " + job)
    heading_keywords = extract_keywords(section["section_title"])
    content_keywords = extract_keywords(section["section_text"])
    overlap = len((heading_keywords | content_keywords) & context_keywords)
    return overlap

def rank_sections(sections, persona, job, topk=5):
    context = persona + ". " + job
    section_texts = [s["section_title"] + ". " + s["section_text"] for s in sections]
    all_texts = [context] + section_texts
    vectorizer = TfidfVectorizer().fit(all_texts)
    vecs = vectorizer.transform(all_texts)
    query_vec = vecs[0]
    section_vecs = vecs[1:]
    tfidf_scores = np.dot(section_vecs, query_vec.T).toarray().reshape(-1)
    ranked = []
    for i, s in enumerate(sections):
        penalty = heading_penalty(s["section_title"])
        overlap = section_dynamic_score(s, persona, job)
        score = 0.7 * tfidf_scores[i] + 0.3 * overlap + penalty
        ranked.append((s, score))
    return sorted(ranked, key=lambda x: -x[1])[:topk]


def extract_refined_text(section, persona, job, max_chars=400):
    text = section["section_text"]
    sentences = re.split(r'(?<=[.!?]) +', text)
    keywords = set(re.findall(r'\b\w+\b', (persona + " " + job).lower()))
    scored = []
    for s in sentences:
        s_words = set(re.findall(r'\b\w+\b', s.lower()))
        overlap = len(s_words & keywords)
        scored.append((overlap, s))
    scored.sort(reverse=True)
    refined = ""
    for _, sent in scored:
        if len(refined) + len(sent) > max_chars:
            break
        refined += sent + " "
    return refined.strip() or " ".join(sentences[:2])

def process_collection(collection_path):
    input_path = os.path.join(collection_path, 'challenge1b_input.json')
    output_path = os.path.join(collection_path, 'challenge1b_output.json')
    pdf_dir = os.path.join(collection_path, 'PDFs')
    
    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    persona = input_data["persona"]["role"]
    job = input_data["job_to_be_done"]["task"]
    doclist = input_data["documents"]

    all_sections = []
    for doc in doclist:
        filename = doc["filename"]
        title = doc.get("title", "")
        pdf_path = os.path.join(pdf_dir, filename)
        sections = extract_sections_from_pdf(pdf_path, docname=filename)
        all_sections.extend(sections)

    ranked = rank_sections(all_sections, persona, job)

    metadata = {
        "input_documents": [doc["filename"] for doc in doclist],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.now().isoformat()
    }

    extracted_sections = []
    subsection_analysis = []
    for rank, (section, score) in enumerate(ranked, 1):
        extracted_sections.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": rank,
            "page_number": section["page_number"]
        })
        refined_text = extract_refined_text(section, persona, job)
        subsection_analysis.append({
            "document": section["document"],
            "refined_text": refined_text.strip(),
            "page_number": section["page_number"]
        })

    out_json = {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(out_json, f, indent=2, ensure_ascii=False)
    #print(f"Output written to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1].lower() == "all"):
        root = os.getcwd()
        collections = [d for d in os.listdir(root) if os.path.isdir(d) and d.lower().startswith("collection")]
        for coll in collections:
            #print(f"\n--- Processing {coll} ---")
            process_collection(coll)
    elif len(sys.argv) == 2:
        process_collection(sys.argv[1])
    else:
        #print("Usage: python combined_main.py <Collection Folder>")
        sys.exit(1)
