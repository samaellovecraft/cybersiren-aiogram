from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f
from aiogram.types import Message, CallbackQuery

from config import CREATOR_USERNAME, GODDESS_USERNAME
from core import data, keyboards
from core.utils import send_donate_message

router = Router()

@router.message(CommandStart())
async def start(message: Message) -> None:
    """
    This handler receives messages with `/start` command and greets the user
    """
    username = message.from_user.username
    if username == CREATOR_USERNAME:
        await message.answer(text=data.CREATOR_HELLO)
    elif username == GODDESS_USERNAME:
        await message.answer(text=data.GODDESS_HELLO)
    else:
        await message.answer(text=data.DEFAULT_HELLO)
    await message.delete()


@router.message(or_f(Command("help"), F.text == keyboards.ECHO_BTN_TEXT))
async def handle_help_message(message: Message) -> None:
    """
    This handler receives messages with `/help` command and provides a description of the bot's functionalities
    """
    await message.delete()
    await message.answer(text=data.HELP_TEXT,
                         reply_markup=keyboards.HELP_IKB)


@router.message(Command("donate"))
async def handle_donate_message(message: Message, bot: Bot) -> None:
    await message.delete()
    chat_id = message.chat.id
    await send_donate_message(chat_id=chat_id, bot=bot)


@router.callback_query(F.data == "donate")
async def handle_donate_callback(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    chat_id = callback.message.chat.id
    await send_donate_message(chat_id=chat_id, bot=bot)


# ? The `echo` function should be placed at the end to avoid overwriting other hadlers.
@router.message()
async def echo(message: Message) -> None:
    """
    This handler receives a message that doesn't match any of the messages handled above and responds by providing a help button
    """
    await message.answer(text=data.ECHO_TEXT,
                         reply_markup=keyboards.ECHO_KB)
