# Mechanic Monke

import discord
import requests
import time
import json
import urllib

import bot_details

from discord import app_commands

intents=discord.Intents(message_content = True)

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def sync_repos():
    print("Syncing repos")
    mod_update_channel = client.get_channel(bot_details.mod_update_channel)

    if bot_details.online_tracking_url != None or bot_details.online_tracking_url != "":
        await check_web_releases(mod_update_channel, bot_details.online_tracking_url)
    else:
        await check_releases(mod_update_channel)
        
    print("Synced repos")

async def check_web_releases(mod_update_channel, endpoint_url):
    with urllib.request(endpoint_url) as mods_json:
       repos = json.loads(mods_json.readline())

       if repos == None:
            print(("Error: endpoint URL is not valid JSON: {}", endpoint_url))
            exit(1)

    index = 0

    for repoc in repos:
        user = repoc[0]
        repo = repoc[1]
        current_version = repoc[2]

        response = requests.get("https://api.github.com/repos/{}/{}/releases/latest".format(user, repo))

        if response == None:
            print("{}/{}: Could not fetch releases".format(user, repo))
            return
        else:
            version = response.json()["name"]

            print("{}/{}: Current version is {}, release version is {}.".format(user, repo, current_version, version))

            if current_version != version:
                embed = discord.Embed(
                    title="{}/{}".format(user, repo),
                    description="""
                    {} -> {}

                    [Download](https://github.com/{}/{}/releases/latest)
                    """.format(current_version, version, user, repo),
                    color=0x00ff00
                )

                await mod_update_channel.send(embed=embed)
            
            index += 1

async def check_releases(mod_update_channel):
    with open(bot_details.mods_file, "r") as mods_json:
        repos = json.loads(mods_json.readline())

    index = 0

    for repoc in repos:
        user = repoc[0]
        repo = repoc[1]
        current_version = repoc[2]

        response = requests.get("https://api.github.com/repos/{}/{}/releases/latest".format(user, repo))

        if response == None:
            print("{}/{}: Could not fetch releases".format(user, repo))
            return
        else:
            version = response.json()["name"]

            print("{}/{}: Current version is {}, release version is {}.".format(user, repo, current_version, version))

            if current_version != version:
                embed = discord.Embed(
                    title="{}/{}".format(user, repo),
                    description="""
                    {} -> {}

                    [Download](https://github.com/{}/{}/releases/latest)
                    """.format(current_version, version, user, repo),
                    color=0x00ff00
                )

                await mod_update_channel.send(embed=embed)
                
                repos[index].insert(2, version)
                repos[index].pop()
                print("{}/{}: Version bumped to {}".format(user, repo, version))
            
            index += 1
    
    # updates all the versions, now time to pack it back into JSON

    with open("mods.json", "w") as mods_json:
	    json.dump(repos, mods_json)

@tree.command(name="addrepo", description="Add repository", guild=discord.Object(id=bot_details.guild_id))
async def add_repo(interaction: discord.Interaction, github_username: str, github_repository: str):
    if bot_details.allow_add_repositories:
        # await interaction.response.send_message("Repo {}/{}".format(github_username, github_repository))
        print("{}/{}: begin tracking (checks are running..)".format(github_repository, github_username))
        await interaction.response.defer()
        response = requests.get("https://api.github.com/repos/{}/{}/releases/latest".format(github_repository, github_repository))

        if response == None:
            await interaction.command.error("{}/{}: Could not fetch releases".format(github_username, github_repository))
            print("{}/{}: killed \"begin tracking\" (checks failed)".format(github_repository, github_username))
        else:
            with open("mods.json", "r") as mods_json:
                repos = json.loads(mods_json.readline())

            repos.append([github_username, github_repository, "v0.0.0"])
            
            with open("mods.json", "w") as mods_json:
                json.dump(repos, mods_json)

            await interaction.response.send_message("Your mod is now being tracked.")
            print("{}/{}: begin tracking (checks are passing)".format(github_repository, github_username))
    else:
        await interaction.command.error("The /addrepo command is disabled by the bot administrators.")

def check_for_admin(user_id: int):
    for admin_user_id in bot_details.bot_admin_ids:
        if admin_user_id == user_id:
            return True
    
    return False

@tree.command(name="stop", description="Stop the bot [admins only]", guild=discord.Object(id=bot_details.guild_id))
async def stop():
    if check_for_admin(interaction.user.id) == True:
        await interaction.response.send_message("OK")

        # stop the bot
        print("Bot stopped by user with an admin ID")
        exit(0)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    print("Syncing tree")
    await tree.sync(guild=discord.Object(id=bot_details.guild_id))
    print("Synced tree")

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=bot_details.bot_playing_text or "monkeying around", url=bot_details.bot_playing_url or "https://github.com/drumkitgorilla/MechanicMonke"))

    while True:
        print("Syncing repos")
        mod_update_channel = client.get_channel(bot_details.mod_update_channel)
        await check_releases(mod_update_channel)
        print("Synced repos")

        time.sleep(60)
try:
    token = bot_details.bot_token
    client.run(token)
except discord.HTTPException as e:
    print("exception: {}".format(e))
    exit(1)
