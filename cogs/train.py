import discord
from discord import app_commands
from discord.ui import Select, View
from discord.ext import commands
import requests
import json
from datetime import datetime
import os
import math

class Train(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lines = {"Orange": {"desc": "Midway - Loop", "emoji": "🟠", "rt": "Org"},
        "Red": {"desc": "Howard - 95th/Dan Ryan", "emoji": "🔴", "rt": "Red"}, 
        "Green": {"desc": "Harlem - Ashland/63rd", "emoji": "🟢", "rt": "G"}, 
        "Blue": {"desc": "O'hare - Forest Park", "emoji": "🔵", "rt": "Blue"}, 
        "Pink": {"desc": "54th/Cermak - Loop", "emoji": "🌸", "rt": "Pink"}, 
        "Purple": {"desc": "Linden - Loop", "emoji": "🟣", "rt": "P"}, 
        "Brown": {"desc": "Kimball - Loop", "emoji": "🟤", "rt": "Brn"},
        "Yellow": {"desc": "Skokie - Howard", "emoji": "🟡", "rt": "Y"}}
        self.data = json.load(open('./stations.json', 'r'))

    def normal_round(self, n):
        '''
        Helps with providing a more "accurate" time to each arrival
        Similar to what the boards at stations display in terms in minutes
        '''
        if n - math.floor(n) < 0.5:
            return math.floor(n)
        return math.ceil(n)

    def arrival_string(self, body: json, i: int, string: str):
        '''
        Called from get_arrival_times, provides string for each time presented from the request
        The predicted arrival time is subtracted from the current time (It takes from OS, but it SHOULD be CST)
        It checks for any flags, such as if the train is approaching the station or if it is delayed, it will be displayed in the message
        '''
        time = datetime.fromisoformat(body[i]["arrT"])
        current_time = datetime.now()
        minute_til_arrival = time - current_time
        status = None
        if body[i]["isApp"] == "1":
            status = "DUE"
        elif body[i]["isDly"] == "1":
            status = "DELAYED"
        string += f'*{str(self.normal_round(minute_til_arrival.total_seconds()/60))+"m" if status == None else status} {"📶" if body[i]["isSch"] == "0" else "🕒"}* '
        return string

    def get_arrival_times(self, params, rt: str):
        '''
        Gives the requested station's arrival times
        Takes params to put into the ttarrivals api link and get the response body to parse
        Loops through each entry to display all arrivals at a station
        '''
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'HIGH:!DH:!aNULL'
        response = requests.get('https://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?', params=params)
        resp_result = response.json()
        body = resp_result["ctatt"]["eta"]
        trDr1, trDr5 = "", ""
        string = f'**{body[0]["staNm"]}**\n*Displaying {rt["emoji"]} arrival times*\n'
        for i, _ in enumerate(body):
            if body[i]["trDr"] == "1" and body[i]["rt"] == rt["rt"]:
                if trDr1 == "":
                    trDr1 += f'**Service towards {body[i]["destNm"]}**\n'
                trDr1 = self.arrival_string(body, i, trDr1)
            elif body[i]["trDr"] == "5" and body[i]["rt"] == rt["rt"]:
                # make a special case for UIC-Halsted + Forest Park and 63rd/Ashland + Cottage Grove
                if trDr5 == "":
                    trDr5 += f'\n**Service towards {body[i]["destNm"]}**\n'
                trDr5 = self.arrival_string(body, i, trDr5)
        string += (trDr1 + trDr5)
        return string

    @app_commands.command(name="train", description="this is a train command")
    async def train(self, interaction: discord.Interaction):
        try:
            async def line_callback(interaction):

                async def get_arrivals(interaction):
                    if selectStations.values[0] == "Loop":
                        await choose_station(interaction)
                        return
                    params = {
                        "key": os.getenv("CTA_TRAIN_TOKEN"),
                        "mapid": self.data[selectLines.values[0]][selectStations.values[0]],
                        "outputType": "JSON"
                    }
                    stringtosend = self.get_arrival_times(params, rt=self.lines[selectLines.values[0]])
                    await interaction.response.edit_message(content=stringtosend, view=None)

                async def choose_station(interaction):

                    async def get_arrivalsExt(interaction):
                        params = {
                            "key": os.getenv("CTA_TRAIN_TOKEN"),
                            "mapid": self.data[selectLines.values[0]][selectBranch.values[0] if selectLines.values[0] in extended_lines 
                                     else selectStations.values[0]][selectExtStations.values[0]],
                            "outputType": "JSON"
                        }
                        stringtosend = self.get_arrival_times(params, rt=self.lines[selectLines.values[0]])
                        await interaction.response.edit_message(content=stringtosend, view=None)

                    selectExtStations = Select(
                        placeholder="Select a station",
                        options=[discord.SelectOption(label=station) for station in self.data[selectLines.values[0]][selectBranch.values[0] 
                                 if selectLines.values[0] in extended_lines else selectStations.values[0]]]
                    )
                    selectExtStations.callback = get_arrivalsExt
                    viewStations = View()
                    viewStations.add_item(selectExtStations)
                    await interaction.response.edit_message(content=f"Selected line: `{selectLines.values[0]}`\nWhich station are you at?", view=viewStations)

                # Two options can occur:
                selectStations = Select(
                    placeholder="Select a station",
                    options=[discord.SelectOption(label=station) for station in self.data[selectLines.values[0]]]
                )
                selectBranch = Select(
                    placeholder="Select a branch",
                    options=[discord.SelectOption(label=branch) for branch in self.data[selectLines.values[0]]]
                )

                extended_lines = ["Red", "Green", "Blue"]

                selectStations.callback = get_arrivals
                selectBranch.callback = choose_station

                viewStations, viewBranch = View(), View()

                viewStations.add_item(selectStations)
                viewBranch.add_item(selectBranch)

                if selectLines.values[0] not in extended_lines:
                    await interaction.response.edit_message(content=f"Selected line: `{selectLines.values[0]}`\nWhich station are you at?", view=viewStations)
                else:
                    await interaction.response.edit_message(content=f"Selected branch: `{selectLines.values[0]}`\nWhich branch are you on?", view=viewBranch)

            selectLines = Select(
                placeholder="Please select a line",
                options=[discord.SelectOption(label=line, description=info['desc'], emoji=info['emoji']) for line, info in self.lines.items()])
                          
            selectLines.callback = line_callback
            viewLines = View()
            viewLines.add_item(selectLines)
            
            await interaction.response.send_message("Hello! Which line are you taking?", view=viewLines)

        except Exception as e:
            print(e)
            await interaction.response.send_message("Oops! There was an error :c")

async def setup(bot):
    await bot.add_cog(Train(bot))