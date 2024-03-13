from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command, Filter
from keyboards import keyboard as kb


#
# @router.message(F.text & F(lambda message: "https://www.youtube.com/" in message.text))
# async def choices(callback: types.CallbackQuery):
#     await callback.message.answer("", reply_markup=kb.audio_or_video_button)
#
#
# @router.message("")
# async def get_video(callback: types.CallbackQuery):
#     await callback.message
