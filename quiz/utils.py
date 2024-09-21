from pprint import pprint

from quiz.data import QUIZ, PROGRESS_KEY_MAPPING

quiz_progress: dict[str, dict[str, int]] = {
#    "user_id": dict(QUIZ_PROGRESS_TEMPLATE)
}

async def reset_quiz_progress(user_id: int) -> None:
    global quiz_progress
    del quiz_progress[user_id]
    print(f"The progress for user with ID {user_id} has been reset: {'exists' if user_id in quiz_progress else 'does not exist'} in the quiz_progress.") # ! quiz status check
    pprint(quiz_progress) # ! quiz status check


async def get_next_question(question_counter: int) -> str:
    question = QUIZ[question_counter]['q']
    quiz_text = f"*{question}*\n\n"
    answer_options = list(QUIZ[question_counter]['a'].values())
    for index, answer_option in enumerate(answer_options, start=1):
        quiz_text = quiz_text + f"{index}. {answer_option}\n\n"
    return quiz_text


async def increment_character_points(selected_option: str, user_id: int) -> str:
    # ? Takes an option and returns a character_id
    global quiz_progress
    character_id = PROGRESS_KEY_MAPPING.get(selected_option)
    quiz_progress[user_id]['character_points'][character_id]+=1
    return character_id


async def decrement_character_points(character_id: str, user_id: int) -> None:
    global quiz_progress
    quiz_progress[user_id]['character_points'][character_id]-=1


async def determine_quiz_result(user_id: int) -> list:
    global quiz_progress
    # Find the maximum points
    max_points = max(quiz_progress[user_id]['character_points'].values())
    # Find all characters with the maximum points
    top_characters = [character for character, points in quiz_progress[user_id]['character_points'].items() if points == max_points]
    print("Characters with the most points:", top_characters) # ! quiz status check
    return top_characters
