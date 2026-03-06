from flask import Flask, request, jsonify
import re

app = Flask(__name__)

def strip_markdown(text):
    """Remove markdown formatting from text"""
    if not text:
        return ''
    
    # Remove bold+italic ***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)
    # Remove bold **
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Remove italic *
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove headers ###
    text = re.sub(r'###\s*', '', text)
    # Remove horizontal rules
    text = re.sub(r'---+', '', text)
    # Convert bullets to •
    text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
    # Remove numbered list markers
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()

def extract_section(lesson_content, num):
    """Extract a section and its time from lesson content"""
    pattern = rf'###\s*\*\*{num}\.(.+?)(?=###\s*\*\*{num + 1}\.|$)'
    match = re.search(pattern, lesson_content, re.IGNORECASE | re.DOTALL)
    
    if not match:
        return {'content': '', 'time': ''}
    
    full_section = match.group(1)
    
    # Extract time
    time_match = re.search(r'\*\((\d+\s*minutes?)\)\*', full_section, re.IGNORECASE)
    time = time_match.group(1) if time_match else ''
    
    return {
        'content': strip_markdown(full_section.strip()),
        'time': time
    }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/parse-lesson', methods=['POST'])
def parse_lesson():
    try:
        data = request.json
        lesson_content = data.get('lessonContent', '')
        grade_level = data.get('gradeLevel', 'Middle School')
        topic = data.get('topic', '')
        
        # Extract metadata
        rubric_match = re.search(r'\*\*Rubric Focus:\*\*\s*(.+)', lesson_content, re.IGNORECASE)
        rubric_focus = rubric_match.group(1).strip() if rubric_match else ''
        
        outcome_match = re.search(r'\*\*Learning Target:\*\*\s*(.+)', lesson_content, re.IGNORECASE)
        outcome = outcome_match.group(1).strip() if outcome_match else ''
        
        activity_match = re.search(r'\*\*Activity:\*\*\s*(.+)', lesson_content, re.IGNORECASE)
        activity_name = activity_match.group(1).strip() if activity_match else ''
        
        standard_match = re.search(r'\*\*Connection to Standard:\*\*[\s\S]*?"(.+?)"', lesson_content, re.IGNORECASE)
        standard = standard_match.group(1).strip() if standard_match else ''
        
        # Extract sections
        section1 = extract_section(lesson_content, 1)
        section2 = extract_section(lesson_content, 2)
        section3 = extract_section(lesson_content, 3)
        section4 = extract_section(lesson_content, 4)
        
        # Build replacements
        replacements = {
            '{{GRADE_LEVEL}}': grade_level,
            '{{TOPIC}}': topic,
            '{{TIMEFRAME}}': '60 minutes',
            '{{STANDARD}}': strip_markdown(standard),
            '{{OUTCOME}}': strip_markdown(outcome),
            '{{RUBRIC_FOCUS}}': strip_markdown(rubric_focus),
            '{{ACTIVITY_NAME}}': strip_markdown(activity_name),
            '{{SECTION_1_CONTENT}}': section1['content'],
            '{{SECTION_1_TIME}}': section1['time'],
            '{{SECTION_2_CONTENT}}': section2['content'],
            '{{SECTION_2_TIME}}': section2['time'],
            '{{SECTION_3_CONTENT}}': section3['content'],
            '{{SECTION_3_TIME}}': section3['time'],
            '{{SECTION_4_CONTENT}}': section4['content'],
            '{{SECTION_4_TIME}}': section4['time']
        }
        
        # Build Google Docs API requests array
        requests = []
        for placeholder, value in replacements.items():
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': placeholder,
                        'matchCase': True
                    },
                    'replaceText': value or ''
                }
            })
        
        return jsonify({
            'success': True,
            'requests': requests
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
