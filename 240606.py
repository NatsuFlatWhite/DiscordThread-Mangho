import discord
import asyncio
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

target_server_id = target_to_server_id
target_channel_id = target_to_channel_id

# 선장의 첫 채팅을 저장 할 딕셔너리
thread_first_message_time = {}

@client.event
async def on_ready():
    game = discord.Game(name="우왓..")
    await client.change_presence(activity=game)
    print(f'{client.user}으로 로그인 성공')

@client.event
async def on_message(message):
    if (
        isinstance(message.channel, discord.Thread)
        and not message.author.bot
        and message.guild.id == target_server_id
        and message.channel.parent_id == target_channel_id
    ):
        thread = message.channel

        # 선장의 첫 메시지인지 확인
        if thread.id not in thread_first_message_time:
            thread_first_message_time[thread.id] = message.created_at.replace(tzinfo=timezone.utc)
            await schedule_user_removal(thread)

async def schedule_user_removal(thread):
    time_to_wait = (thread_first_message_time[thread.id] + timedelta(seconds=12)) - datetime.now(timezone.utc)
    await asyncio.sleep(time_to_wait.total_seconds())

    try:
        members = await thread.fetch_members()
        for member in members:
            try:
                await thread.remove_user(member)
                print(f"{member}, {thread.name}에서 제거했습니다")
            except Exception as e:
                print(f"{member}를 제거하는 데 실패했어요: {e}")
        
        # 스레드에 더 이상 사용자가 남아 있지 않으면 스레드의 이름을 생성 날짜로 변경
        if not (await thread.fetch_members()):
            creation_date_utc = thread.created_at + timedelta(hours=9)
            creation_date = creation_date_utc.strftime("%Y-%m-%d")
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

client.run('')
