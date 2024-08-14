import discord
from discord.ext import tasks
import asyncio
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

gall_server_id = server_id
channel_id = Channel_id

thread_last_message_time = {}
thread_removal_tasks = {}

@client.event
async def on_ready():
    print(f'{client.user}으로 로그인 성공')
    update_status.start()

@tasks.loop(minutes=30)
async def update_status():
    await client.change_presence(activity=discord.Game(name="안녕하세요"))    

@client.event
async def on_message(message):
    if (
        isinstance(message.channel, discord.Thread)
        and not message.author.bot
        and message.guild.id == gall_server_id
        and message.channel.parent_id == channel_id
    ):
        thread = message.channel

        thread_last_message_time[thread.id] = message.created_at.replace(tzinfo=timezone.utc)

        if thread.id in thread_removal_tasks:
            thread_removal_tasks[thread.id].cancel()

        await schedule_galler_remove(thread)

async def schedule_galler_remove(thread):
    # 마지막 메시지 시간을 기준으로 4시간 후에 작업 예약
    time_to_wait = (thread_last_message_time[thread.id] + timedelta(hours=4)) - datetime.now(timezone.utc)
    task = asyncio.create_task(remove_galler(thread, time_to_wait.total_seconds()))
    thread_removal_tasks[thread.id] = task

async def remove_galler(thread, delay):
    await asyncio.sleep(delay)
    
    try:
        members = await thread.fetch_members()
        for member in members:
            try:
                await thread.remove_user(member)
                print(f"{member}, {thread.name}에서 제거했습니다")
            except Exception as e:
                print(f"{member}를 제거하는 데 실패했어요: {e}")
        if not (await thread.fetch_members()):
            creation_date_utc = thread.created_at + timedelta(hours=9)
            creation_date = creation_date_utc.strftime("%Y-%m-%d")
#            24-08-14 제목 부분 추가 스레드이름-날짜 (아마도 마지막 유지보수 일 가능성이 큼)
#            new_name = f"{thread.name.split('-')[0]}-{creation_date}"
#            if thread.name != new__name: 
#                await thread.edit(name=new_name)
            await thread.edit(name=f"{creation_date}")
    except Exception as e:
        print(f"스레드의 멤버를 가져오는 데 실패했습니다: {e}")

@client.event
async def on_disconnect():
    print("Discord와의 연결이 끊어졌습니다. 재연결을 시도합니다.")

@client.event
async def on_error(event, *args, **kwargs):
    print(f"이벤트에 오류가 발생했습니다: {event}")
    import traceback
    traceback.print_exc()

client.run('Token')
