from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from back1 import generate_flashcards
from supabase import create_client

app = Flask(__name__)
app.secret_key = 'flashcard-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Supabase Configuration
SUPABASE_URL = "https://kgpetshsaulbhhyfobqq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtncGV0c2hzYXVsYmhoeWZvYnFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAyODgxMTEsImV4cCI6MjA3NTg2NDExMX0.rzNkjuoIUK5RTzJWWMY6OSxS-eUAWkiJw5etLJpFwxY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper functions for Supabase
def save_flashcards_to_db(user_id, pdf_name, flashcards):
    """Save flashcards to Supabase database"""
    saved_count = 0
    for card in flashcards:
        data = {
            'user_id': user_id,
            'title': f"Flashcard from {pdf_name}",
            'question': card['question'],
            'answer': card['answer'],
            'source_pdf': pdf_name
        }
        try:
            response = supabase.table('flashcards').insert(data).execute()
            if response.data:
                saved_count += 1
        except Exception as e:
            print(f"Error saving flashcard: {e}")
            continue
    return saved_count

def get_user_flashcards_from_db(user_id):
    """Get all flashcards for a user from Supabase"""
    try:
        response = supabase.table('flashcards')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error fetching flashcards: {e}")
        return []

def get_user_stats(user_id):
    """Get user statistics from Supabase"""
    try:
        flashcards = get_user_flashcards_from_db(user_id)
        total = len(flashcards)
        unique_pdfs = len(set(card.get('source_pdf', '') for card in flashcards))
        return {
            'total_flashcards': total,
            'unique_pdfs': unique_pdfs
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total_flashcards': 0, 'unique_pdfs': 0}

# Authentication routes
@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Registration page"""
    return render_template('register.html')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Handle user login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if email:
            session['user'] = {
                'id': email.replace('@', '-at-').replace('.', '-dot-'),
                'email': email
            }
            return jsonify({'success': True, 'message': 'Login successful!'})
        else:
            return jsonify({'success': False, 'error': 'Email required'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/auth/register', methods=['POST'])
def auth_register():
    """Handle user registration"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if email:
            session['user'] = {
                'id': email.replace('@', '-at-').replace('.', '-dot-'),
                'email': email
            }
            return jsonify({'success': True, 'message': 'Registration successful!'})
        else:
            return jsonify({'success': False, 'error': 'Email required'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('user', None)
    return redirect('/')

# Main application routes
@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard with all saved flashcards"""
    if 'user' not in session:
        return redirect('/login')
    
    user_id = session['user']['id']
    flashcards = get_user_flashcards_from_db(user_id)
    stats = get_user_stats(user_id)
    
    print(f"DEBUG: User {user_id} has {len(flashcards)} flashcards")
    
    return render_template('dashboard.html', 
                         user=session['user'],
                         flashcards=flashcards,
                         stats=stats,
                         total_count=len(flashcards))

@app.route('/generate', methods=['POST'])
def generate():
    """Generate flashcards from PDF and save to Supabase"""
    print("DEBUG: Generate route called")
    
    if 'user' not in session:
        print("DEBUG: User not logged in")
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        if 'pdf' not in request.files:
            print("DEBUG: No PDF file in request")
            return jsonify({'error': 'No PDF file provided'}), 400
        
        pdf_file = request.files['pdf']
        print(f"DEBUG: PDF file received: {pdf_file.filename}")
        
        if pdf_file.filename == '':
            print("DEBUG: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Please upload a PDF file'}), 400
        
        # Save uploaded file temporarily
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        pdf_path = os.path.join(upload_dir, pdf_file.filename)
        pdf_file.save(pdf_path)
        print(f"DEBUG: File saved to: {pdf_path}")
        
        # Generate flashcards using AI
        print("DEBUG: Generating flashcards using back1.py...")
        try:
            flashcards = generate_flashcards(pdf_path)
            print(f"DEBUG: Generated {len(flashcards)} flashcards")
        except Exception as e:
            print(f"DEBUG: Error in generate_flashcards: {e}")
            # Fallback to demo flashcards
            flashcards = [
                {'question': 'What is machine learning?', 'answer': 'A subset of AI that enables computers to learn without being explicitly programmed.'},
                {'question': 'What is a neural network?', 'answer': 'A series of algorithms that mimic the human brain to recognize relationships in data.'},
                {'question': 'What is deep learning?', 'answer': 'A type of machine learning using neural networks with multiple layers.'}
            ]
            print("DEBUG: Using demo flashcards due to error")
        
        # Save flashcards to Supabase
        user_id = session['user']['id']
        saved_count = save_flashcards_to_db(user_id, pdf_file.filename, flashcards)
        print(f"DEBUG: Saved {saved_count} flashcards to database")
        
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully generated {len(flashcards)} flashcards! Saved {saved_count} to your library.',
            'flashcards': flashcards,
            'count': len(flashcards),
            'saved_count': saved_count
        })
        
    except Exception as e:
        print(f"DEBUG: Error in generate route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/flashcards')
def view_flashcards():
    """View flashcards from Supabase (NEW FIXED VERSION)"""
    if 'user' not in session:
        return redirect('/login')
    
    try:
        user_id = session['user']['id']
        flashcards = get_user_flashcards_from_db(user_id)
        
        # Generate text content from Supabase flashcards
        if flashcards:
            # Questions only
            questions_content = "=== YOUR FLASHCARDS (LATEST FIRST) ===\n\n"
            # Questions with answers
            answers_content = "=== YOUR FLASHCARDS WITH ANSWERS (LATEST FIRST) ===\n\n"
            
            for i, card in enumerate(flashcards, 1):
                # Format: Q1: Question text
                questions_content += f"Q{i}: {card['question']}\n\n"
                
                # Format: Q1: Question text\nA: Answer text
                answers_content += f"Q{i}: {card['question']}\n"
                answers_content += f"A: {card['answer']}\n"
                answers_content += f"Source: {card.get('source_pdf', 'Unknown')}\n"
                answers_content += "-" * 50 + "\n\n"
        else:
            questions_content = "No flashcards found in your library.\nGenerate some flashcards first!"
            answers_content = "No flashcards found in your library.\nGenerate some flashcards first!"
        
        return render_template('flashcards.html', 
                             questions=questions_content,
                             answers=answers_content,
                             total_count=len(flashcards))
                             
    except Exception as e:
        return render_template('flashcards.html', 
                             questions="Error loading flashcards from database",
                             answers=str(e),
                             total_count=0)

@app.route('/api/flashcards')
def get_flashcards_api():
    """API endpoint to get user's flashcards"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user']['id']
    flashcards = get_user_flashcards_from_db(user_id)
    return jsonify({'flashcards': flashcards})

@app.route('/api/flashcards/<flashcard_id>', methods=['DELETE'])
def delete_flashcard(flashcard_id):
    """Delete a flashcard"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_id = session['user']['id']
        response = supabase.table('flashcards')\
            .delete()\
            .eq('id', flashcard_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if response.data:
            return jsonify({'success': True, 'message': 'Flashcard deleted'})
        else:
            return jsonify({'success': False, 'error': 'Flashcard not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flashcard Generator with Supabase...")
    print("📊 Supabase Integration: ACTIVE")
    print("🐛 Debug Mode: ENABLED")
    print("🌐 Home: http://localhost:5000")
    print("👤 Login: http://localhost:5000/login")
    print("📁 Dashboard: http://localhost:5000/dashboard")
    print("📝 Text Flashcards: http://localhost:5000/flashcards")
    app.run(debug=True, port=5000)