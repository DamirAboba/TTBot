import logging
import os
import re

from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm import state
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, BufferedInputFile
from aiogram.utils.formatting import Text

from pytube import YouTube

from keyboards.keyboard import audio_or_video_button, youtube_button

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_valid_youtube_url(url):
    regex = (r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?["
             r"?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})")
    return re.match(regex, url)


@router.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("Привет! Пришли мне ссылку на видео.")


@router.message()
async def process_link(message: types.Message, state: FSMContext):
    url = message.text
    if is_valid_youtube_url(url):
        await state.update_data(youtube_url=url)
        print(url)
        await message.answer("Что ты хочешь скачать?", reply_markup=audio_or_video_button)


@router.callback_query(F.data == 'get_audio')
async def process_audio(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        url = data.get('youtube_url')
        yt = YouTube(url)
        print("YouTube object:", yt)
        audio = yt.streams.filter(only_audio=True).first()
        print("Selected audio stream:", audio)
        if audio:
            title = re.sub(r'[^\w\s]+', '', yt.title)
            audio_file_path = f"{title}.mp3"
            audio.download(output_path=".", filename=title)
            print("Audio downloaded successfully.")
            with open(audio_file_path, 'rb') as file:
                audio_input_file = BufferedInputFile(file=file.read(), filename=audio_file_path)
                await callback_query.message.answer_audio(audio=audio_input_file)
            return None
        else:
            print("Failed to select audio stream.")
    except Exception as e:
        logger.error(f"An error occurred in process_audio: {e}")


@router.callback_query(F.data == 'get_video')
async def process_video(callback_query: types.CallbackQuery):
    url = callback_query.message.text
    await callback_query.message.answer("Выберите разрешение:", reply_markup=youtube_button)


# Video_downloader
@router.callback_query(F.data == '720p')
async def process_resolution(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        resolution = callback_query.data
        data = await state.get_data()
        url = data.get('youtube_url')
        yt = YouTube(url)
        print("YouTube object:", yt)
        video = yt.streams.filter(res=f'{resolution}p', progressive=True).first()
        print("Selected video stream:", video)
        if video:
            title = re.sub(r'[^\w\s]+', '', yt.title)
            video_file_path = f"{title}.mp4"
            video.download(output_path=".", filename=title)
            print("Video downloaded successfully.")
            with open(video_file_path, 'rb') as file:
                video_input_file = types.input_file.BufferedInputFile(file=file.read(), filename=video_file_path)
                await callback_query.message.answer_video(video=video_input_file)
        else:
            print("Failed to select video stream.")
    except Exception as e:
        logger.error(f"An error occurred in process_resolution: {e}")