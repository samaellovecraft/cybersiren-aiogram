from pprint import pprint
from copy import deepcopy

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import CHANNEL
from core.utils import check_membership
from quiz.data import (
    CHARACTERS, QUESTIONS_TOTAL, PROGRESS_TEMPLATE, INIT_PROMPT,
    SINGLE_RESULT_MSG, DOUBLE_RESULT_MSG, MULTIPLE_RESULT_MSG,
    ERROR_MSG, SUBSCRIBE_MSG, NOT_SUBSCRIBED_MSG
)
from quiz.keyboards import INIT_IKB, QUESTION_IKB, RETAKE_IKB
from quiz.utils import (
    quiz_progress, reset_quiz_progress, get_next_question, determine_quiz_result,
    increment_character_points, decrement_character_points
)

router = Router()

@router.message(Command("quiz"))
@router.callback_query(F.data == "check_membership")
async def init_quiz(message_or_callback: Message | CallbackQuery, bot: Bot) -> None:
    user_id = message_or_callback.from_user.id
    is_member = await check_membership(user_id=user_id, chat_id=CHANNEL, bot=bot)

    # Handle message
    if isinstance(message_or_callback, Message):
        if is_member:
            await message_or_callback.answer(text=INIT_PROMPT,
                                             reply_markup=INIT_IKB)
        else:
            await message_or_callback.answer(text=SUBSCRIBE_MSG,
                                             reply_markup=INIT_IKB)
        await message_or_callback.delete()

    # Handle callback
    elif isinstance(message_or_callback, CallbackQuery):
        if is_member:
            await message_or_callback.answer()

            global quiz_progress
            quiz_progress[user_id] = deepcopy(PROGRESS_TEMPLATE)
            pprint(quiz_progress) # ! quiz status check

            question_counter = quiz_progress[user_id]['question_counter']
            print(f"Initializing counter: {question_counter}\n") # ! quiz status check

            # Prepare next question
            quiz_text = await get_next_question(question_counter)

            await bot.edit_message_text(chat_id=message_or_callback.message.chat.id,
                                        message_id=message_or_callback.message.message_id,
                                        text=quiz_text,
                                        reply_markup=QUESTION_IKB)
        else:
            await message_or_callback.answer(NOT_SUBSCRIBED_MSG)

# Quiz callback queries handler
@router.callback_query(F.data.startswith("option_"))
async def iter_quiz(callback_query: CallbackQuery, bot: Bot) -> None:

    # Answer the callback
    user_id = callback_query.from_user.id
    callback_data = callback_query.data
    await bot.answer_callback_query(callback_query.id, f"Received callback: {callback_data}")

    # Increment the question counter to account for the question that was just answered
    global quiz_progress
    try:
        quiz_progress[user_id]['question_counter']+=1
    except KeyError:
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        text=ERROR_MSG,
                                        reply_markup=RETAKE_IKB)
        return
    question_counter = quiz_progress[user_id]['question_counter']
    #print(f"Counter incremented: {question_counter}") # ! quiz status check

    # ! Step 1: Handle character points.
    match callback_data:
        case 'option_quit':
            try:
                await bot.delete_message(chat_id=callback_query.message.chat.id,
                                         message_id=callback_query.message.message_id)
            except Exception as e: # ? Expected `MessageCantBeDeleted`: A message can only be deleted if it was sent less than 48 hours ago. (https://core.telegram.org/bots/api#deletemessage)
                print(f"An exception occurred inside `option_quit` block: {e}")
                await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                       message_id=callback_query.message.message_id,
                                       text=ERROR_MSG,
                                       reply_markup=RETAKE_IKB)
            await reset_quiz_progress(user_id=user_id)
            return # ? to avoid executing the code below, which could result in 'aiogram.utils.exceptions.MessageToEditNotFound'
        case 'option_back':
            if question_counter <= 1:
                # ? It means it's the first question
                quiz_progress[user_id]['question_counter']-=1 # decrement already incremented (at the beginning) counter and do nothing
                question_counter = quiz_progress[user_id]['question_counter']
                print(f"It's already the 1st ({question_counter}) question!") # ! quiz status check
                return # # ? to avoid executing the code below, which could result in 'aiogram.utils.exceptions.MessageNotModified'
            else:
                # ? Otherwise, decrement character points and go to the previous question
                previous_option_character = quiz_progress[user_id]['previous_option_characters'].pop()
                await decrement_character_points(character_id=previous_option_character, user_id=user_id)
                quiz_progress[user_id]['question_counter']-=2
                question_counter = quiz_progress[user_id]['question_counter']
                print(f"Counter decremented: {question_counter}\nProgress: {quiz_progress[user_id]['character_points']}\nPrevious options: {quiz_progress[user_id]['previous_option_characters']}\n") # ! quiz status check
        case _:
            previous_option_character = await increment_character_points(selected_option=callback_data, user_id=user_id)
            quiz_progress[user_id]['previous_option_characters'].append(previous_option_character)
            print(f"Counter incremented: {question_counter}\nProgress: {quiz_progress[user_id]['character_points']}\nPrevious options: {quiz_progress[user_id]['previous_option_characters']}\n") # ! quiz status check

    # ! Step 2: Determine if the current question is the last one.
    # !         If it is, display the quiz result and reset the quiz progress; otherwise, present the next question.
    if question_counter == QUESTIONS_TOTAL:
        # Display quiz result
        top_characters: list = await determine_quiz_result(user_id=user_id)
        match len(top_characters):
            case 1:
                character, = top_characters # iterable unpacking
                result_text = SINGLE_RESULT_MSG.format(**CHARACTERS[character])
                await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id,
                                            text=result_text)
            case 2:
                markdown_character_names = [f"*{CHARACTERS[character]['name']}*" for character in top_characters]
                result_text = DOUBLE_RESULT_MSG.format(' and '.join(markdown_character_names))
                for character in top_characters:
                    result_text+=f"*{CHARACTERS[character]['name']}:*\n\n_{CHARACTERS[character]['description']}_\n\n"
                await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id,
                                            text=result_text)
            case _:
                await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id,
                                            text=MULTIPLE_RESULT_MSG,
                                            reply_markup=RETAKE_IKB)

        await reset_quiz_progress(user_id=user_id)

    else:
        try:
            # Prepare the next question
            quiz_text = await get_next_question(question_counter)
            # Present the next question
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        text=quiz_text,
                                        reply_markup=QUESTION_IKB)

        # ? Safeguard against errors when the user attempts to take multiple quizzes simultaneously
        # ? by handling potential issues with the quiz progresses interfering with each other.
        except Exception as e: # ? Expected `MessageNotModified` or `IndexError`
            print(f"An exception occurred: {e}")
            # Edit the flawed quiz message notifying the user and inviting them to retake the quiz
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                        message_id=callback_query.message.message_id,
                                        text=ERROR_MSG,
                                        reply_markup=RETAKE_IKB)
