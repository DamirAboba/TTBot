import logging
import os
import re
from io import BytesIO

import aiohttp
import requests
from aiogram import types, Router, F
from aiogram.client import bot
from aiogram.filters import CommandStart, Filter
from aiogram.fsm import state
from aiogram.fsm.context import FSMContext
from aiogram.types import InputFile, BufferedInputFile, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, \
    URLInputFile, Message
import yt_dlp
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pytube import YouTube
from TikTokApi import TikTokApi
import moviepy.editor as mp
import instaloader

from keyboards.keyboard import audio_or_video_button, youtube_button

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = TikTokApi()
L = instaloader.Instaloader()


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
        await message.delete_reply_markup()


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
@router.callback_query(lambda F: F.data in ['144p', '240p', '360p', '480p', '720p', '1080p'])
async def process_resolution(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        resolution = callback_query.data
        data = await state.get_data()
        url = data.get('youtube_url')
        yt = YouTube(url)
        print("YouTube object:", yt)
        video = yt.streams.filter(res=f'{resolution}').first()
        print(f'video data {video}')
        print("Selected video stream:", video)
        if video:
            title = yt.title
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
            print(f'title: {safe_title}')
            video_file_path = f"{safe_title}.mp4"
            video.download(filename=video_file_path)
            print("Video downloaded successfully.")
            with open(video_file_path, 'rb') as file:
                video_input_file = types.input_file.BufferedInputFile(file=file.read(), filename=video_file_path)
                await callback_query.message.answer_video(video=video_input_file)
            await callback_query.message.delete_reply_markup()
            await callback_query.message.delete()

        else:
            print("Failed to select video stream.")
    except Exception as e:
        logger.error(f"An error occurred in process_resolution: {e}")


######
class LinkFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text.startswith("http")


@router.message()
async def process_tt(message: types.Message):
    if 'www.tiktok.com' in message.text:
        link = message.text
        print(message.text)
        msg = await message.answer("Происходит обработка видео")
        url = "https://tiktok-video-no-watermark2.p.rapidapi.com/"
        querystring = {"url": link, "hd": "1"}
        headers = {
            "X-RapidAPI-Key": "4da7179647msh3eade03715c2792p1232a9jsn957eaf4605a1",
            "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=querystring) as response:
                try:
                    data = await response.json()
                    video_link = data['data']['play']
                    await msg.edit_text("Отправляем видео. \nсекунду...")
                    await message.answer_video(URLInputFile(video_link))
                except (KeyError, aiohttp.ClientError) as e:
                    await msg.edit_text("Произошла ошибка при обработке видео.")
                    print(f"Error: {e}")
