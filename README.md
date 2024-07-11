# DiscDV: FreeDV on a real HF transceiver from a Discord voice call!

Please be aware that this program is in very early development stages.
Use on the air only if you are a licensed amateur radio operator,
and you understand that bugs are bound to occur!

# How to use:

## Step one: creating a Discord bot 
### (Skip if you've made bots before)
Go to https://discord.com/developers, sign in, and in the `Applications` tab, click `New Application`,
and create a new application. Once done, head to the `Bot` tab, and create a bot. Name it what you'd like,
and then hit `Reset Token` and copy the newly generated token. Paste this token into
`token.txt`, and make sure no one else sees it! At this point, you can now
generate an invite link for the bot by going to the `OAuth2` tab, checking
`applications.commands` and `bot`, and choosing the bot permissions (Administrator is recommended).
Viola! The invite link is ready to be used.

## Step two: installing Python
### (Skip if you already have Python)
This is operating system dependent, so I will not be explaining this here. The internet exists for a reason!

## Step three: installing packages
In the directory of the python files, open a terminal and run `pip3 install -r requirements.txt`

## Step four: setting up DiscDV
At this point, you should have your Discord bot's token in `token.txt`.
The next thing to do is download or build the required Codec2 libraries.

On **Linux**, this can be done by
going to the codec2 GitHub page at https://github.com/drowe67/codec2, 
following the build instructions, and copying the `libcodec2.so` into a folder named
`lib` in the directory of the python files.

On **Windows**, you can obtain the `libcodec2.dll`
file by building it yourself, however I have found this tricky. Instead, you can download the FreeDV GUI program
at https://freedv.org, then go to the installation folder and copying 
`libcodec2.dll` and `liblpcnetfreedv.dll` to the `lib` directory in the directory of the python files.

Then, run `audio_config.py`, and find the numbers for the audio devices connecting your PC and radio.
Edit the `audio_input_device` and `audio_output_device` variables in `audio_config.py` to match those device numbers.

Finally, edit the `rigctld_command` variable in `rig_config.py` to control your radio properly. Go to
https://hamlib.sourceforge.net/html/rigctld.1.html for help with rigctld.

## Step five: you should be good to go!
Run the `bot.py` file with `python3 bot.py` to start the bot!

# A note on OS compatibility
This program is designed for Windows and Linux, but only tested by me on Windows.
There may be some issues on Linux that do not exist when running this program on Windows.
This program is not designed to run on macOS.
