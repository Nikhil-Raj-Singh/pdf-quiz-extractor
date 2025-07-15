from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import PyPDF2
import re
import os
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def parse_questions(text):
    """Parse questions from extracted text"""
    questions = []
    
    # Pattern to match questions (adjust based on your PDF format)
    # This pattern looks for numbered questions followed by options A, B, C, D
    question_pattern = r'(\d+)\.\s*(.+?)(?=\n(?:A\)|a\)|\d+\.|$))'
    option_pattern = r'([A-Da-d])\)\s*(.+?)(?=\n(?:[A-Da-d]\)|\d+\.|$))'
    
    # Find all questions
    question_matches = re.findall(question_pattern, text, re.DOTALL)
    
    for match in question_matches:
        question_num = match[0]
        question_text = match[1].strip()
        
        # Find options for this question
        question_section = text[text.find(f"{question_num}. {question_text}"):text.find(f"{int(question_num)+1}." if int(question_num) < 100 else "END")]
        
        options = []
        option_matches = re.findall(option_pattern, question_section, re.DOTALL)
        
        for opt_match in option_matches:
            option_letter = opt_match[0].upper()
            option_text = opt_match[1].strip()
            options.append({
                'letter': option_letter,
                'text': option_text
            })
        
        if len(options) >= 2:  # Only include questions with at least 2 options
            questions.append({
                'number': int(question_num),
                'text': question_text,
                'options': options,
                'correct_answer': None  # Will be set based on answer key or user input
            })
    
    return questions

def parse_answer_key(text):
    """Parse answer key from text"""
    answer_key = {}
    
    # Pattern to match answer key (adjust based on your format)
    # Looks for patterns like "1. A", "2. B", etc.
    answer_pattern = r'(\d+)\.\s*([A-Da-d])'
    
    # Also try patterns like "1) A", "2) B"
    answer_pattern_alt = r'(\d+)\)\s*([A-Da-d])'
    
    matches = re.findall(answer_pattern, text, re.IGNORECASE)
    if not matches:
        matches = re.findall(answer_pattern_alt, text, re.IGNORECASE)
    
    for match in matches:
        question_num = int(match[0])
        correct_answer = match[1].upper()
        answer_key[question_num] = correct_answer
    
    return answer_key

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Extract text and parse questions
        text = extract_text_from_pdf(filepath)
        if not text:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        questions = parse_questions(text)
        if not questions:
            return jsonify({'error': 'No questions found in PDF'}), 400
        
        # Try to extract answer key
        answer_key = parse_answer_key(text)
        
        # Set correct answers if found
        for question in questions:
            if question['number'] in answer_key:
                question['correct_answer'] = answer_key[question['number']]
        
        # Store in session
        session['questions'] = questions
        session['current_question'] = 0
        session['user_answers'] = {}
        session['quiz_started'] = False
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'total_questions': len(questions),
            'questions_with_answers': len([q for q in questions if q['correct_answer']])
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/quiz_setup')
def quiz_setup():
    if 'questions' not in session:
        return redirect(url_for('home'))
    
    questions = session['questions']
    return render_template('quiz_setup.html', 
                         total_questions=len(questions),
                         questions_with_answers=len([q for q in questions if q['correct_answer']]))

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    if 'questions' not in session:
        return redirect(url_for('home'))
    
    # Get quiz settings
    time_per_question = int(request.form.get('time_per_question', 30))
    
    # Initialize quiz session
    session['quiz_started'] = True
    session['current_question'] = 0
    session['user_answers'] = {}
    session['time_per_question'] = time_per_question
    session['quiz_start_time'] = datetime.now().isoformat()
    
    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    if 'questions' not in session or not session.get('quiz_started', False):
        return redirect(url_for('home'))
    
    current_q = session['current_question']
    questions = session['questions']
    
    if current_q >= len(questions):
        return redirect(url_for('results'))
    
    question = questions[current_q]
    return render_template('quiz.html', 
                         question=question,
                         current=current_q + 1,
                         total=len(questions),
                         time_per_question=session.get('time_per_question', 30))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'questions' not in session or not session.get('quiz_started', False):
        return jsonify({'error': 'Quiz not started'}), 400
    
    current_q = session['current_question']
    answer = request.form.get('answer')
    
    if answer:
        session['user_answers'][current_q] = answer
    
    session['current_question'] = current_q + 1
    
    # Check if quiz is complete
    if session['current_question'] >= len(session['questions']):
        return jsonify({'redirect': url_for('results')})
    
    return jsonify({'redirect': url_for('quiz')})

@app.route('/results')
def results():
    if 'questions' not in session or not session.get('quiz_started', False):
        return redirect(url_for('home'))
    
    questions = session['questions']
    user_answers = session.get('user_answers', {})
    
    # Calculate results
    total_questions = len(questions)
    answered_questions = len(user_answers)
    correct_answers = 0
    
    detailed_results = []
    
    for i, question in enumerate(questions):
        user_answer = user_answers.get(i, None)
        correct_answer = question.get('correct_answer', None)
        
        is_correct = False
        if user_answer and correct_answer:
            is_correct = user_answer.upper() == correct_answer.upper()
            if is_correct:
                correct_answers += 1
        
        detailed_results.append({
            'question': question,
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'question_number': i + 1
        })
    
    # Calculate percentage
    if total_questions > 0:
        percentage = (correct_answers / total_questions) * 100
    else:
        percentage = 0
    
    return render_template('results.html',
                         total_questions=total_questions,
                         answered_questions=answered_questions,
                         correct_answers=correct_answers,
                         percentage=round(percentage, 2),
                         detailed_results=detailed_results)

@app.route('/reset')
def reset_quiz():
    # Clear session
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)