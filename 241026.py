import discord
from discord.ext import tasks
import asyncio
import os
import logging
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

target_server_id = target_server_id 
target_channel_id = target_channel_id

thread_last_message_time = {}
thread_removal_tasks = {}

backup_tasks = {}

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
        and message.guild.id == target_server_id
        and message.channel.parent_id == target_channel_id
    ):
        thread = message.channel

        if thread.id not in backup_tasks:
            backup_tasks[thread.id] = asyncio.create_task(backup_thread_messages(thread))

        thread_last_message_time[thread.id] = message.created_at.replace(tzinfo=timezone.utc)

        if thread.id in thread_removal_tasks:
            thread_removal_tasks[thread.id].cancel()

        await schedule_galler_removal(thread)

async def schedule_galler_removal(thread):
    # 마지막 메시지 시간을 기준으로 4시간 후에 작업 예약
    time_to_wait = (thread_last_message_time[thread.id] + timedelta(seconds=62)) - datetime.now(timezone.utc)
    task = asyncio.create_task(remove_galler_delay(thread, time_to_wait.total_seconds()))
    thread_removal_tasks[thread.id] = task

async def remove_galler_delay(thread, delay):
    await asyncio.sleep(delay)
    
    try:
        members = await thread.fetch_members()
        for member in members:
            try:
                await thread.remove_user(member)
                print(f"{member}, {thread.name}에서 제거했습니다")
            except Exception as e:
                print(f"{member}와 관련된 오류: {e}")
        
        if not (await thread.fetch_members()):
            creation_date_utc = thread.created_at + timedelta(hours=9)
            creation_date = creation_date_utc.strftime("%Y-%m-%d")
            new_thread_name = f"{thread.name.split('-')[0]}-{creation_date}" 

            await thread.edit(name=new_thread_name)
            print(f"스레드 '{thread.name}'의 제목을 '{new_thread_name}'로 변경했습니다.")
            
            if thread.id in backup_tasks:
                backup_tasks[thread.id].cancel()
                del backup_tasks[thread.id]
                print(f"스레드 '{new_thread_name}'의 백업 작업을 종료했습니다.")

    except Exception as e:
        print(f"오류: {e}")

async def backup_thread_messages(thread):
    os.makedirs("backup", exist_ok=True)
    
    creation_time_str = thread.created_at.strftime('%Y%m%d_%H%M%S')
    file_path = f"backup/{thread.id}_{thread.name}_{creation_time_str}.txt"

    while not thread.archived:
        async for message in thread.history(limit=100, oldest_first=True):
            with open(file_path, "a", encoding="utf-8") as f:
                handle = message.author.name
                nickname = message.author.display_name
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                content = message.content
                image_links = [attachment.url for attachment in message.attachments if attachment.content_type and attachment.content_type.startswith("image")]
                if image_links:
                    content += " " + " ".join(image_links)

                f.write(f"[{timestamp}] {nickname} ({handle}): {content}\n")
                
        await asyncio.sleep(60)

    del backup_tasks[thread.id]

@client.event
async def on_disconnect():
    print("Discord와의 연결이 끊어졌습니다. 재연결을 시도합니다.")

@client.event
async def on_error(event, *args, **kwargs):
    print(f"이벤트 오류: {event}")
    import traceback
    traceback.print_exc()

client.run('Your Token')
