from aiogram import Bot

from core.keyboards import DONATE_IKB

async def check_membership(user_id: int, chat_id: str | int, bot: Bot) -> bool:
    try:
        chat_member = await bot.get_chat_member(user_id=user_id, chat_id=chat_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print("Error checking membership:", e)
        return False

async def send_donate_message(chat_id: int, bot: Bot) -> None:
    await bot.send_sticker(
        chat_id=chat_id,
        sticker="CAACAgIAAxkBAAEJ9l5k0xurZzCnsCyaSZvNDArsHvLUTwACNRgAAmThiUg4NXyZ6hlB6zAE",
        reply_markup=DONATE_IKB
    )
