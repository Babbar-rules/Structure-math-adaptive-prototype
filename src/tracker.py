import json
import os

DATA_FILE = 'user_progress.json'

def load_progress():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_progress(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def record_answer(username, question, correct_answer, user_answer, correct, time_taken, difficulty):
    progress = load_progress()
    if username not in progress:
        progress[username] = {'history': []}
    
    progress[username]['history'].append({
        'question': question,
        'correct_answer': correct_answer,
        'user_answer': user_answer,
        'correct': correct,
        'time_taken': time_taken,
        'difficulty': difficulty
    })
    save_progress(progress)

def get_history(username):
    progress = load_progress()
    return progress.get(username, {}).get('history', [])
