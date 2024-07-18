import discord
import database
import freedv
import pyaudio
import audio_config
import rig_control
import rig_config
import audio
import queue

try:
    TOKEN = open('token.txt', 'rt').read()
except Exception as e:
    print('Error loading token.txt, ensure the file exists and contains only your bot token!')
    raise e

print('Loading Discord modules...')

bot = discord.Bot()
bot_db = database.BotDatabase('operators.db')
vc: discord.VoiceClient | None = None
vc_sink: audio.FreeDVSink | None = None
vc_source: audio.FreeDVSource | None = None

print('Loading FreeDV...')
try:
    fdv = freedv.FreeDV700D()
except Exception as e:
    print('Error loading FreeDV! Make sure all codec2 .dll / .so files are built correctly and in the lib directory.')
    print('Continuing to start without FreeDV capability! This may cause bugs!')
    fdv = None
    # raise e

print('Loading rigctld...')
try:
    rigctld = rig_control.RigControl(rig_config.rigctld_cmd)
except Exception as e:
    print('Error loading rigctld! Ensure the rigctld_command in rig_control.py is correct.')
    raise e

rigctld.set_mode(rig_config.default_mode, -1)
rigctld.set_freq(rig_config.default_freq * 1000)

rx_queue = queue.Queue()
tx_queue = queue.Queue()
ptt = False


def pa_callback(in_data, frame_count, time_info, status):
    global rx_queue, tx_queue, ptt

    tx_mod = b'\x00\x00' * frame_count
    if vc_sink is not None:
        for data in in_data:
            rx_queue.put(data.to_bytes(1))

        new_ptt = vc_sink.tx()

        if new_ptt and not ptt:
            ptt = True
            rigctld.set_ptt(ptt)

        elif ptt and not new_ptt:
            ptt = False
            rigctld.set_ptt(ptt)

        if tx_queue.qsize() > frame_count * 2:
            tx_mod = audio.get_bytes_from_queue_nowait(tx_queue, frame_count * 2)

    return tx_mod, pyaudio.paContinue


pa = pyaudio.PyAudio()
tx_volume = audio_config.tx_volume

input_device_name = pa.get_device_info_by_index(audio_config.audio_input_device)['name']
output_device_name = pa.get_device_info_by_index(audio_config.audio_output_device)['name']

print(f'Starting audio using input device [{input_device_name}] and output device [{output_device_name}]')
try:
    af_stream = pa.open(rate=8000, channels=1, format=pyaudio.paInt16, input=True, output=True, frames_per_buffer=1024,
                        stream_callback=pa_callback,
                        input_device_index=audio_config.audio_input_device,
                        output_device_index=audio_config.audio_output_device)
except Exception as e:
    print('Error starting audio! Ensure the input and output devices are correctly configured in audio_config.py')
    raise e


@bot.event
async def on_ready():
    print(f'{bot.user} is ready!')


@bot.slash_command(name='ping', description='Get current bot ping')
async def ping(ctx):
    await ctx.respond(f'Current bot ping is: {round(bot.latency, 5)}')


@bot.slash_command(name='analog_listen', description='Set whether the radio will play audio when not synced')
async def set_analog_listen(ctx: discord.ApplicationContext, value: bool):
    if not fdv:
        await ctx.respond('FreeDV mode is not supported!')
        return

    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        fdv.listen_to_analog(value)
        await ctx.respond(f'Analog listen is now set to: {value}')

    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='add_operator', description='Add a user to be able to use the radio')
async def add_operator(ctx: discord.ApplicationContext,
                       user: discord.Member, callsign: str, admin: bool):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        bot_db.add_operator(user.id, callsign, admin)
        await ctx.respond(f'{user.name} has been added as an operator!')

    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='remove_operator', description='Remove a users ability to operate the radio')
async def remove_operator(ctx: discord.ApplicationContext, user: discord.Member):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        bot_db.delete_operator(user.id)
        await ctx.respond(f'{user.name} can no longer operate the radio!')

    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='get_operators', description='Get all users that are able to operate the radio')
async def get_operators(ctx: discord.ApplicationContext):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        operators = bot_db.get_operators()
        message = 'All operators: '

        for operator in operators:
            user = await bot.fetch_user(operator.uuid)
            username = user.name
            message += f'{username} ({operator.callsign}), '

        await ctx.respond(message)

    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='get_operator_info', description='Get info about a users ability to operate the radio')
async def get_operator_info(ctx: discord.ApplicationContext, user: discord.Member):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        operator = bot_db.get_operator(user.id)
        await ctx.respond(f'Name: {user.name}, Callsign: {operator.callsign}, Admin? {bool(operator.admin)}')

    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='enable_tx', description='Enable radio transmit')
async def enable_tx(ctx: discord.ApplicationContext):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        if vc:
            vc_sink.enable_tx(True)
            await ctx.respond('TX is now enabled! '
                              'If you are permitted to operate the radio, '
                              'speaking in VC will trigger radio transmit!')
        else:
            await ctx.respond('The bot is not currently connected to a voice channel.')
    else:
        await ctx.respond('You are not permitted to run this command!')


@bot.slash_command(name='disable_tx', description='Disable radio transmit')
async def disable_tx(ctx: discord.ApplicationContext):
    if ctx.author.guild_permissions.administrator or bot_db.get_operator(ctx.author.id).admin:
        if vc:
            vc_sink.enable_tx(False)
            await ctx.respond('TX is now disabled! Speaking in VC will no longer trigger radio transmit.')
        else:
            await ctx.respond('The bot is not currently connected to a voice channel.')
    else:
        await ctx.respond('You are not permitted to run this command!')


async def on_voice_leave(sink: discord.sinks, channel: discord.TextChannel, *args):
    await sink.vc.disconnect()


@bot.slash_command(name='join', description='Make the bot join a voice channel to use the radio!')
async def join_voice_channel(ctx: discord.ApplicationContext):
    global vc, vc_sink, vc_source, rx_queue, tx_queue, fdv

    if vc:
        await ctx.respond('Bot is already in a voice channel!')
        return

    voice = ctx.author.voice
    vc_sink = audio.FreeDVSink(tx_queue, [operator.uuid for operator in bot_db.get_operators()], fdv)
    vc_sink.set_tx_volume(tx_volume)
    vc_source = audio.FreeDVSource(rx_queue, fdv)

    if not voice:
        await ctx.respond('You are not in a voice channel!')
        return

    vc = await voice.channel.connect()

    vc.start_recording(
        vc_sink,
        on_voice_leave,
        ctx.channel
    )

    vc.play(
        vc_source,
        wait_finish=False
    )

    await ctx.respond('Joined!')


@bot.slash_command(name='leave', description='Make the bot leave the voice channel')
async def leave_voice_channel(ctx: discord.ApplicationContext):
    global vc, vc_sink, vc_source

    if not vc:
        await ctx.respond('The bot is not currently in a voice channel!')
        return

    assert isinstance(vc, discord.VoiceClient)

    vc.stop()
    await vc.disconnect()
    vc = None
    vc_sink = None
    vc_source = None

    await ctx.respond('Left the voice channel!')


@bot.slash_command(name='set_freq', description='Set the frequency')
async def set_freq(ctx: discord.ApplicationContext, freq: float):
    operator_ids = [operator.uuid for operator in bot_db.get_operators()]
    if ctx.author.id not in operator_ids and not ctx.author.guild_permissions.administrator:
        await ctx.respond('You are not permitted to run this command!')
        return

    rigctld.set_freq(int(freq * 1000))
    await ctx.respond(f'Radio VFO set to: {freq} KHz')


@bot.slash_command(name='get_freq', description='Get the current frequency')
async def get_freq(ctx: discord.ApplicationContext):
    freq = rigctld.get_freq()
    await ctx.respond(f'Current VFO: {freq / 1000} KHz')


@bot.slash_command(name='set_mode', description='Set the radio modulation mode')
async def set_mode(ctx: discord.ApplicationContext, mode: str):
    rigctld.set_mode(mode, -1)
    await ctx.respond(f'Radio set to: {mode}')


@bot.slash_command(name='get_mode', description='Get the current radio modulation mode')
async def get_mode(ctx: discord.ApplicationContext):
    mode = rigctld.get_mode()
    await ctx.respond(f'The radio is currently set to: {mode}')


@bot.slash_command(name='analog_mode', description='Set the radio to transmit and receive in analog mode')
async def analog_mode(ctx: discord.ApplicationContext):
    global vc_sink, vc_source
    vc_sink.set_transmit_freedv(False)
    vc_source.set_receive_freedv(False)
    await ctx.respond('Set radio mode to analog')


@bot.slash_command(name='freedv_mode', description='Set the radio to transmit and receive in FreeDV mode')
async def freedv_mode(ctx: discord.ApplicationContext):
    global vc_sink, vc_source
    vc_sink.set_transmit_freedv(True)
    vc_source.set_receive_freedv(True)
    await ctx.respond('Set radio mode to FreeDV')


def cleanup_all():
    global fdv, rigctld, bot_db, af_stream, pa
    print('Cleaning everything up...')

    if fdv:
        fdv.close()

    rigctld.close()
    bot_db.close()
    af_stream.close()
    pa.terminate()
    print('ALl closed successfully!')


def main():
    global bot
    print('Starting bot...')
    bot.run(TOKEN)
    cleanup_all()


if __name__ == '__main__':
    main()
