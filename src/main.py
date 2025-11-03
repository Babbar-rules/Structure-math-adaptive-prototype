import time
from adaptive_engine import get_difficulty
from tracker import record_answer
from puzzle_generator import generate_question



print("Welcome to the Math Quiz!")
username = input("Please enter your name: ")

difficulty=None
while True:
        difficulty_choice = input("Choose a difficulty (easy, medium, hard): ").lower()
        if difficulty_choice in ['easy', 'medium', 'hard']:
            difficulty=difficulty_choice
            break
        else:
            print("Invalid difficulty. Please choose from easy, medium, or hard.")

session_correct = 0
session_incorrect = 0

try:
    while True:
            difficulty = get_difficulty(username)
            question, correct_answer = generate_question(difficulty)
            
            start_time = time.time()
            try:
                user_answer = float(input(f"Difficulty: {difficulty} | {question} "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            end_time = time.time()
                
            time_taken = end_time - start_time
            correct = user_answer == correct_answer
            
            if correct:
                print("Correct!")
                session_correct += 1
            else:
                print(f"Wrong! The correct answer is {correct_answer}")
                session_incorrect += 1
                
            record_answer(username, question, correct_answer, user_answer, correct, time_taken, difficulty)
            
            print("Press Ctrl+C to exit")
except KeyboardInterrupt:
    print("\n--- Session Report ---")
    print(f"Total Correct Answers: {session_correct}")
    print(f"Total Incorrect Answers: {session_incorrect}")
    print("Thanks for playing!")