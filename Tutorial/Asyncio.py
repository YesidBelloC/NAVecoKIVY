import asyncio

from kivy.app import async_runTouchApp
from kivy.uix.label import Label


loop = asyncio.get_event_loop()
loop.run_until_complete(
    async_runTouchApp(Label(text='Hello, World!'), async_lib='asyncio'))
loop.close()