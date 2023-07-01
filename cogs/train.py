import discord
from discord import app_commands
from discord.ui import Select, View
from discord.ext import commands
import requests
import json
from datetime import datetime
import os

class Train(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lines = {"Orange": {"desc": "Midway - Loop", "emoji": "🟠"}, 
        "Red": {"desc": "Howard - 95th/Dan Ryan", "emoji": "🔴"}, 
        "Green": {"desc": "Harlem - Ashland/63rd", "emoji": "🟢"}, 
        "Blue": {"desc": "O'hare - Forest Park", "emoji": "🔵"}, 
        "Pink": {"desc": "54th/Cermak - Loop", "emoji": "🌸"}, 
        "Purple": {"desc": "Linden - Loop", "emoji": "🟣"}, 
        "Brown": {"desc": "Kimball - Loop", "emoji": "🟤"},
        "Yellow": {"desc": "Skokie - Howard", "emoji": "🟡"}}
        self.data = json.load(open('./stations.json', 'r'))

    def time_converter(timestamp):
        pass

    @app_commands.command(name="train", description="this is a train command")
    async def train(self, interaction: discord.Interaction):
        try:
            selectLines = Select(
                placeholder="Please select a line",
                options=[discord.SelectOption(label=line, description=info['desc'], emoji=info['emoji']) for line, info in self.lines.items()])
            
            async def line_callback(interaction):
        
                async def get_arrivals(interaction):
                    params = {
                        "key": os.getenv("CTA_TRAIN_TOKEN"),
                        "mapid": self.data[selectLines.values[0]][selectStations.values[0]],
                        "outputType": "JSON"
                    }
                    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
                    response = requests.get(f'https://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?', params=params)
                    resp_result = response.json()
                    body = resp_result["ctatt"]["eta"]
                    trDr1, trDr5 = "", ""
                    stringtosend = f'**{body[0]["staNm"]}**\n\n'

                    for i in range(len(body)):
                        if body[i]["trDr"] == "1":
                            if trDr1 == "":
                                trDr1 += f'**{body[i]["stpDe"]}**\n'
                            time = datetime.fromisoformat(body[i]["arrT"]).time().minute
                            current_time = datetime.now().time().minute
                            minute_til_arrival = time - current_time
                            trDr1 += f'*{str(minute_til_arrival)+"m" if body[i]["isApp"] == "0" else "DUE"} {"📶" if body[i]["isSch"] == "0" else "🕒"}* '
                        else: 
                            if trDr5 == "":
                                trDr5 += f'\n**{body[i]["stpDe"]}**\n'
                            time = datetime.fromisoformat(body[i]["arrT"]).time().minute
                            current_time = datetime.now().time().minute
                            minute_til_arrival = time - current_time
                            trDr5 += f'*{str(minute_til_arrival)+"m" if body[i]["isApp"] == "0" else "DUE"} {"📶" if body[i]["isSch"] == "0" else "🕒"}* '

                    stringtosend += (trDr1 + trDr5)
                    await interaction.response.send_message(stringtosend)

                selectStations = Select(
                    placeholder="Select a station",
                    options=[discord.SelectOption(label=station) for station in self.data[selectLines.values[0]]]
                )
                selectStations.callback = get_arrivals
                viewStations = View()
                viewStations.add_item(selectStations)
                await interaction.response.send_message(f"Selected line: `{selectLines.values[0]}`\nWhich station are you at?", view=viewStations)


            selectLines.callback = line_callback
            viewLines = View()
            viewLines.add_item(selectLines)

            await interaction.response.send_message("Hello! Which line are you taking?", view=viewLines)

        except Exception as e:
            print(e)
            await interaction.response.send_message(f"Oops! There was an error :c")

async def setup(bot):
    await bot.add_cog(Train(bot))