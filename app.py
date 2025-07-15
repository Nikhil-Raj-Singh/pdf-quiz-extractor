from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import PyPDF2
import re
import json
import os
import base64
from io import BytesIO
import time
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-for-sessions-change-this'

class QuizManager:
    def __init__(self):
        self.questions = []
        self.current_question = 0
        
    def extract_content_from_pdf(self, pdf_path):
    """Extract text from PDF"""
    text_content = ""
    
    # Extract text using PyPDF2
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"Processing {len(pdf_reader.pages)} pages...")
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text_content += page_text
                print(f"Processed page {page_num + 1}")
    except Exception as e:
        print(f"Error reading PDF text: {e}")
        return None
    
    return text_content
    
    def parse_questions(self, text_content):
        """Parse questions, options, and answers separately"""
        questions = []
        
        # Clean the text
        text_content = re.sub(r'\s+', ' ', text_content)
        
        # Split by questions (Q1., Q2., etc.)
        question_blocks = re.split(r'(Q\d+\.)', text_content)
        
        for i in range(1, len(question_blocks), 2):
            if i + 1 < len(question_blocks):
                question_header = question_blocks[i]
                question_content = question_blocks[i + 1]
                
                # Extract question text (before options)
                question_match = re.search(r'(.*?)(?=A\.|Options:|$)', question_content, re.DOTALL)
                if question_match:
                    question_text = question_header + " " + question_match.group(1).strip()
                    
                    # Extract options
                    options = []
                    option_pattern = r'([A-D]\..*?)(?=[A-D]\.|Answer:|Explanation:|Q\d+\.|$)'
                    option_matches = re.findall(option_pattern, question_content, re.DOTALL)
                    
                    for option in option_matches:
                        cleaned_option = re.sub(r'\s+', ' ', option.strip())
                        # Remove answer and explanation from option
                        cleaned_option = re.sub(r'Answer.*$', '', cleaned_option, flags=re.IGNORECASE)
                        cleaned_option = re.sub(r'Explanation.*$', '', cleaned_option, flags=re.IGNORECASE)
                        if cleaned_option and len(cleaned_option) > 3:
                            options.append(cleaned_option)
                    
                    # Extract correct answer
                    answer_match = re.search(r'Answer:\s*(?:Option\s*)?([A-D])', question_content, re.IGNORECASE)
                    correct_answer = answer_match.group(1).upper() if answer_match else None
                    
                    # Extract explanation
                    explanation_match = re.search(r'Explanation:(.*?)(?=Q\d+\.|$)', question_content, re.DOTALL)
                    explanation = explanation_match.group(1).strip() if explanation_match else ""
                    explanation = re.sub(r'\s+', ' ', explanation)
                    
                    if len(options) >= 4 and correct_answer:
                        questions.append({
                            'id': len(questions) + 1,
                            'question': question_text,
                            'options': options[:4],  # Take only first 4 options
                            'correct_answer': correct_answer,
                            'explanation': explanation
                        })
        
        return questions
    
    def load_quiz(self, pdf_path):
        """Load quiz from PDF"""
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
            
        text_content = self.extract_content_from_pdf(pdf_path)
        if text_content is None:
            return False
            
        self.questions = self.parse_questions(text_content)
        print(f"Loaded {len(self.questions)} questions")
        return len(self.questions) > 0

quiz_manager = QuizManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        # Get PDF path from form
        pdf_path = request.form.get('pdf_path')
        
        if not pdf_path or not os.path.exists(pdf_path):
            return render_template('setup.html', error="Please provide a valid PDF file path")
        
        # Load quiz
        if quiz_manager.load_quiz(pdf_path):
            session['quiz_id'] = str(uuid.uuid4())
            session['current_question'] = 0
            session['score'] = 0
            session['answers'] = []
            session['start_time'] = time.time()
            session['time_per_question'] = int(request.form.get('time_per_question', 60))
            session['total_questions'] = len(quiz_manager.questions)
            
            return redirect(url_for('quiz'))
        else:
            return render_template('setup.html', error="Failed to load quiz from PDF. Please check the file format.")
    
    return render_template('setup.html')

@app.route('/quiz')
def quiz():
    if 'quiz_id' not in session:
        return redirect(url_for('setup'))
    
    current_q = session['current_question']
    if current_q >= len(quiz_manager.questions):
        return redirect(url_for('results'))
    
    question = quiz_manager.questions[current_q]
    
    # Don't send correct answer or explanation to frontend
    question_data = {
        'id': question['id'],
        'question': question['question'],
        'options': question['options'],
        'current': current_q + 1,
        'total': len(quiz_manager.questions),
        'time_limit': session['time_per_question']
    }
    
    return render_template('quiz.html', question=question_data)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'quiz_id' not in session:
        return jsonify({'error': 'No active quiz'})
    
    data = request.json
    user_answer = data.get('answer')
    time_taken = data.get('time_taken', 0)
    
    current_q = session['current_question']
    if current_q >= len(quiz_manager.questions):
        return jsonify({'error': 'Quiz completed'})
    
    question = quiz_manager.questions[current_q]
    
    # Check if answer is correct
    is_correct = user_answer == question['correct_answer']
    if is_correct:
        session['score'] += 1
    
    # Store answer details
    session['answers'].append({
        'question_id': question['id'],
        'question_text': question['question'],
        'options': question['options'],
        'user_answer': user_answer,
        'correct_answer': question['correct_answer'],
        'is_correct': is_correct,
        'time_taken': time_taken,
        'explanation': question['explanation']
    })
    
    # Update session
    session['current_question'] += 1
    
    # Check if quiz is complete
    if session['current_question'] >= len(quiz_manager.questions):
        session['end_time'] = time.time()
        return jsonify({'completed': True, 'redirect': url_for('results')})
    
    return jsonify({'completed': False, 'redirect': url_for('quiz')})

@app.route('/results')
def results():
    if 'quiz_id' not in session:
        return redirect(url_for('setup'))
    
    total_time = session.get('end_time', time.time()) - session['start_time']
    score = session['score']
    total_questions = session['total_questions']
    accuracy = (score / total_questions) * 100 if total_questions > 0 else 0
    
    results_data = {
        'score': score,
        'total_questions': total_questions,
        'accuracy': round(accuracy, 1),
        'total_time': round(total_time, 1),
        'avg_time': round(total_time / total_questions, 1) if total_questions > 0 else 0,
        'answers': session['answers']
    }
    
    return render_template('results.html', results=results_data)

@app.route('/restart')
def restart():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)