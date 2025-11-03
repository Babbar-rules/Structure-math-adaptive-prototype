from sklearn.linear_model import LogisticRegression
import numpy as np
from tracker import get_history

DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
current_difficulty_index = 0  # Default to easy

# Map difficulty names to integers and back
difficulty_map = {'easy': 0, 'medium': 1, 'hard': 2}
difficulty_map_inv = {v: k for k, v in difficulty_map.items()}

# Dummy training data for the ML model
X_dummy = np.array([
    [0, 10, 1],  # Answered easy correctly in 10s -> next is easy
    [0, 8, 1],   # Answered easy correctly in 8s -> next is medium
    [0, 15, 0],  # Answered easy incorrectly in 15s -> next is easy
    [1, 12, 1],  # Answered medium correctly in 12s -> next is medium
    [1, 20, 1],  # Answered medium correctly in 20s -> next is hard
    [1, 25, 0],  # Answered medium incorrectly in 25s -> next is easy
    [2, 18, 1],  # Answered hard correctly in 18s -> next is hard
    [2, 30, 0]   # Answered hard incorrectly in 30s -> next is medium
])
y_dummy = np.array([0, 1, 0, 1, 2, 0, 2, 1])

model = LogisticRegression(max_iter=1000)
model.fit(X_dummy, y_dummy)



def get_difficulty(username):

    """  Adjusts difficulty based on streaks, falling back to an ML model. """
    global current_difficulty_index
    history = get_history(username)
    
    if not history:
        return DIFFICULTY_LEVELS[current_difficulty_index]

    # --- Primary Logic: Streak-based rules ---
    # Increase difficulty after 3 consecutive correct answers
    if len(history) >= 3 and all(item['correct'] for item in history[-3:]):
        if current_difficulty_index < len(DIFFICULTY_LEVELS) - 1:
            current_difficulty_index += 1
        return DIFFICULTY_LEVELS[current_difficulty_index]

    # Decrease difficulty after 2 consecutive incorrect answers
    if len(history) >= 2 and not any(item['correct'] for item in history[-2:]):
        if current_difficulty_index > 0:
            current_difficulty_index -= 1
        return DIFFICULTY_LEVELS[current_difficulty_index]

    # --- Fallback Logic: ML Model Prediction ---
    # If no streak rule was met, use the model.
    if len(history) > 1:
        X_train = np.array([[difficulty_map[item['difficulty']], item['time_taken'], int(item['correct'])] for item in history[:-1]])
        y_train = np.array([difficulty_map[item['difficulty']] for item in history[1:]])
        if len(set(y_train)) > 1:
            model.fit(X_train, y_train)

    last_answer = history[-1]
    X_predict = np.array([[difficulty_map[last_answer['difficulty']], last_answer['time_taken'], int(last_answer['correct'])]])
    prediction = model.predict(X_predict)
    
    current_difficulty_index = prediction[0]
    return difficulty_map_inv[current_difficulty_index]