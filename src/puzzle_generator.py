
import random

def generate_question(difficulty):
    if difficulty == 'easy':
        num1 = random.randint(1, 5)
        num2 = random.randint(1, 10)
        operator = random.choice(['+', '-'])
    elif difficulty == 'medium':
        num1 = random.randint(1,9)
        num2 = random.randint(10, 50)
        operator = random.choice(['+', '-', '*'])
    else:  # hard
        num1 = random.randint(1, 50)
        num2 = random.randint(5, 30)
        operator = random.choice(['-', '*', '/'])
    
    # Ensure no negative answers for easy and medium subtraction
    if difficulty in ['easy', 'medium'] and operator == '-' and num1 < num2:
        num1, num2 = num2, num1

    if operator == '/':
        # Ensure division results in an integer
        num1 = num1 * num2
        
    question = f"What is {num1} {operator} {num2}?"
    answer = eval(f"{num1} {operator} {num2}")
    
    return question, answer