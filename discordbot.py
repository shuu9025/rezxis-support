import asyncio
import datetime
import json
import os

import discord
import requests
from discord.ext import commands
# ここまでテンプレ ここからいろいろやってく
from discord.ext.commands import CommandInvokeError, CommandError


def is_ticketpanel():
    async def predicate(ctx):
        return ctx.message.channel.id == 682250694648135710
    return commands.check(predicate)


def is_ticket():
    async def predicate(ctx):
        return ctx.message.channel.topic == "ticket-beta"
    return commands.check(predicate)


bot = commands.Bot(command_prefix='/', owner_id=422081938489344000)
bot.remove_command("help")
watchids = []
ignorelink = []
reactions = {
    "🇦": "処罰解除申請",
    "🇧": "「IPアドレスがブロックされています」と表示されてログインできない",
    "🇨": "サーバーが起動中のまま/終了中のまま",
    "🇩": "バグ報告",
    "🇪": "ルール違反者報告",
    "🇫": "その他",
    "🇬": "その他(Adminのみが閲覧可能)"
}


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    logchannel = discord.utils.get(
        message.guild.text_channels, id=679972852908294155)
    embed = discord.Embed(title=f"Sent a message", description=message.content, color=discord.Colour.blue(),
                          timestamp=message.created_at)
    embed.set_author(name=message.author)
    embed.set_footer(text=f"in {message.channel.name}")
    embed.add_field(name="Message URL", value=message.jump_url)
    files = []
    for f in message.attachments:
        files.append(f"[{f.filename} ({f.size / 1024}kb)]({f.url})")
    embed.add_field(name="Attachments",
                    value=f"{len(message.attachments)} files\n" + ("\n".join(files)), inline=False)
    await logchannel.send(embed=embed)
    if message.channel.id == 682250694648135710:
        await message.delete()
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    if after.author.bot:
        return
    if before.content == after.content:
        return
    logchannel = discord.utils.get(
        after.guild.text_channels, id=679972852908294155)
    embed = discord.Embed(title=f"Edit a message", description=after.content, color=discord.Colour.gold(),
                          timestamp=after.created_at)
    embed.add_field(name="Before", value=before.content, inline=False)
    embed.set_author(name=after.author)
    embed.set_footer(text=f"in {after.channel.name}")
    embed.add_field(name="Message URL", value=after.jump_url)
    await logchannel.send(embed=embed)


@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    logchannel = discord.utils.get(
        message.guild.text_channels, id=679972852908294155)
    embed = discord.Embed(title=f"Delete a message", description=message.content, color=discord.Colour.red(),
                          timestamp=datetime.datetime.utcnow())
    embed.set_author(name=message.author)
    embed.set_footer(text=f"in {message.channel.name}")
    embed.add_field(name="Message URL", value=message.jump_url)
    files = []
    for f in message.attachments:
        files.append(f"[{f.filename} ({f.size / 1024}kb)]({f.url})")
    embed.add_field(name="Attachments",
                    value=f"{len(message.attachments)} files\n" + ("\n".join(files)), inline=False)
    await logchannel.send(embed=embed)


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=discord.Game(name='/help'))


@bot.command(name="help")
async def help(ctx, page="1"):
    try:
        page = int(page)
    except ValueError:
        pass
    if page in bot.all_commands:
        cmds = bot.commands
        command = None
        for cmd in cmds:
            for alias in cmd.aliases:
                if alias == page:
                    command = cmd
                    break
            if cmd.name == page:
                command = cmd
                break
        if command is None:
            await ctx.message.channel.send("コマンドが見つかりませんでした！")
            return
        with open("commands.json", encoding="UTF-8") as f:
            cmdinfo: dict = json.load(f)
        embed = discord.Embed(
            title=command.name,
            description=cmdinfo.get(command.name, {}).get("description", "Undefined"),
            color=discord.Color.orange()
        )
        embed.add_field(
            name="使用法",
            value=cmdinfo.get(command.name, {}).get("usage", "Undefined")
        )
        if command.aliases:
            embed.add_field(
                name="エイリアス",
                value=", ".join(command.aliases)
            )
        try:
            avaliable = await command.can_run(ctx)
        except CommandError:
            avaliable = False
        embed.add_field(
            name="利用可能かどうか",
            value="利用可能" if avaliable else "利用不可"
        )
        await ctx.message.channel.send(embed=embed)
    else:
        cmds = bot.commands
        embed = discord.Embed(
            title="Help",
            description="このBotに登録されているコマンドのうち、あなたが実行可能なコマンドの一覧です。",
            color=discord.Color.blue()
        )
        with open("commands.json", encoding="UTF-8") as f:
            cmdinfos: dict = json.load(f)
        i = -1
        for cmd in cmds:
            try:
                if not await cmd.can_run(ctx):
                    continue
            except CommandError:
                continue
            i += 1
            if (page - 1) * 5 <= i < page * 5:
                embed.add_field(
                    name=cmd.name,
                    value=cmdinfos.get(cmd.name, {}).get("brief", "Undefined")
                )
        await ctx.send(embed=embed)


@bot.command(aliases=["new"])
@is_ticketpanel()
async def sendticket(ctx):
    await ctx.message.channel.purge(limit=100)
    embed = discord.Embed(
        title="Ticketの作成",
        description="要件に該当するリアクションをクリックして、Ticketを作成できます。\n"
                    "Ticketの作成にはMinecraftアカウントとDiscordアカウントを連携している必要があります。\n\n"
                    ":regional_indicator_a: 処罰解除申請\n"
                    ":regional_indicator_b: 「IPアドレスがブロックされています」と表示されてログインできない\n"
                    ":regional_indicator_c: サーバーが起動中のまま/終了中のまま\n"
                    ":regional_indicator_d: バグ報告\n"
                    ":regional_indicator_e: ルール違反者報告\n"
                    ":regional_indicator_f: その他(作成されたチャンネルで用件を話してください)\n"
                    ":regional_indicator_g: Adminのみが閲覧可能なTicketを作成する\n\n"
                    "Webmoneyでの寄付など、支払いについての問題は:regional_indicator_g:を使用してください。",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Ticketパネル作成者: {ctx.message.author} ({ctx.message.author.id})")
    message = await ctx.message.channel.send(embed=embed,content="リアクションをクリックしても応答がない場合、`/sendticket`と送信してください。\n"
                                                                 "(問題が起きた場合、この機能は削除される可能性があります。)")
    for reaction in reactions.keys():
        await message.add_reaction(reaction)
    await asyncio.sleep(1)
    watchids.append(message.id)


@sendticket.error
async def sendticket_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("このチャンネルでTicketパネルを作成することはできません！")


@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    if message.id in watchids:
        await reaction.remove(user)
        global ignorelink
        message: discord.Message = message
        channel: discord.TextChannel = message.channel
        server = message.guild
        category = discord.utils.get(
            message.guild.channels, id=672687617309147146)
        for alrch in bot.get_all_channels():
            if alrch.name == f"ticket-{user.id}":
                message = await channel.send("既にTicketが作成されています。")
                await asyncio.sleep(5)
                await message.delete()
                return
        mcid = "Not Found"
        print(user.id)
        print(f"{os.environ['API_URL']}{user.id}")
        if str(user.id) not in ignorelink:
            userdata = json.loads(requests.get(
                f"{os.environ['API_URL']}{user.id}").text)
            print(userdata)
            if userdata["code"] != 0:
                message = await channel.send("Discordとのリンクがされていません。\n" +
                                             "リンクを行っているのにも関わらずこのメッセージが表示されたり、\n" +
                                             "リンクを必要としない、またはリンク関連のTicketを作成する場合はshuu_9025#1141にお問い合わせください。")
                await asyncio.sleep(5)
                await message.delete()
                return
            mcid = json.loads(requests.get(
                f"https://api.mojang.com/user/profiles/{userdata['message'].replace('-', '')}/names").text)[-1]["name"]
        sadmin = discord.utils.get(server.roles, id=573179356273442817)
        admin = discord.utils.get(server.roles, id=517992434366545960)
        staff = discord.utils.get(server.roles, id=517993102867169280)
        if reaction.emoji == "🇬":
            overwrites = {
                server.default_role:
                    discord.PermissionOverwrite(
                        read_messages=False, send_messages=False),
                user:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                sadmin:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                admin:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                staff:
                    discord.PermissionOverwrite(
                        read_messages=False, send_messages=False)
            }
        else:
            overwrites = {
                server.default_role:
                    discord.PermissionOverwrite(
                        read_messages=False, send_messages=False),
                user:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                sadmin:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                admin:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True),
                staff:
                    discord.PermissionOverwrite(
                        read_messages=True, send_messages=True)
            }
        chid = user.id
        ticket = await server.create_text_channel("ticket-" + str(chid), overwrites=overwrites, category=category)
        notify = discord.utils.get(server.channels, name="ticket-notify")
        await ticket.edit(topic="ticket-beta")
        embed = discord.Embed(description="チケットを作成しました", color=0x00ff00)
        embed.add_field(
            name="作成者", value=user.mention, inline=True)
        embed.add_field(name="チケット", value=ticket.mention, inline=True)
        embed.add_field(name="要件", value=reactions[reaction.emoji], inline=False)
        embed.add_field(name="MCID", value=mcid, inline=False)
        await notify.send(embed=embed)
        men = await ticket.send(user.mention)
        await men.delete()
        await ticket.send(
            "Ticketを作成しました。要件を入力し、運営の対応をお待ちください。\n"
            "```\n" +
            reactions[reaction.emoji] + "\n" +
            "```\n" +
            f"リンク済みのMCID: `{mcid}`"
        )


@bot.command(pass_context=True)
@commands.is_owner()
async def bypasslink(ctx, userid=None):
    global ignorelink
    if userid is None:
        await ctx.message.channel.send("ユーザーIDを入力してください！")
        return
    if userid in ignorelink:
        ignorelink.remove(userid)
        await ctx.message.channel.send(f"ユーザーID `{userid}` をignorelinkリストから削除しました。")
        return
    if userid not in ignorelink:
        ignorelink.append(userid)
        await ctx.message.channel.send(f"ユーザーID `{userid}` をignorelinkリストに追加しました。")
        return


@bypasslink.error
async def bypasslink_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("権限がありません！")


@bot.command(pass_context=True)
@is_ticket()
async def close(ctx):
    if isinstance(ctx.message.channel, discord.abc.GuildChannel):
        server = ctx.message.guild
        channel = ctx.message.channel
        openuser = discord.utils.get(server.members, id=int(channel.name.replace("ticket-", "")))
        with open("ticket-history.txt", mode='a') as f:
            async for i in ctx.message.channel.history(oldest_first=True):
                f.write(i.author.display_name + "\t" + i.content + "\n")
            await channel.delete()
            notify = discord.utils.get(
                server.channels, name="ticket-notify")
            embed = discord.Embed(description="チケットを閉じました", color=0xff0000)
            embed.add_field(name="チケット", value=channel.name, inline=True)
            embed.add_field(
                name="実行者", value=ctx.message.author.mention, inline=True)
        with open("ticket-history.txt", mode='rb') as f:
            await notify.send(embed=embed, file=discord.File(f))
        os.remove("ticket-history.txt")
        dm = await openuser.create_dm()
        try:
            dmmessage = await dm.send("今回の対応はいかがでしたか？\n"
                                      "対応にご満足いただけた場合は:+1:を、\n"
                                      "ご満足いただけなかった場合は:-1:を**60秒以内に**クリックしてください。\n"
                                      "(どちらをクリックしたかは運営に送信されます。また、回答は必須ではありません。)")
        except CommandInvokeError:
            return
        await dmmessage.add_reaction("👍")
        await dmmessage.add_reaction("👎")
        await asyncio.sleep(1)

        def help_react_check(react, user):
            emoji = str(react.emoji)
            if react.message.id != dmmessage.id:
                return 0
            if emoji == "👍" or emoji == "👎":
                return 1

        while not bot.is_closed():
            try:
                reaction, user = await bot.wait_for('reaction_add', check=help_react_check, timeout=60.0)
            except asyncio.TimeoutError:
                break
            else:
                emoji = str(reaction.emoji)
                notify = discord.utils.get(server.channels, name="ticket-notify")
                if emoji == "👍":
                    await notify.send(f"`{openuser}`の評価: :+1:")
                if emoji == "👎":
                    await notify.send(f"`{openuser}`の評価: :-1:")
                await dm.send("ご回答いただきありがとうございます。")
                break


@close.error
async def close_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Ticketチャンネルではありません！")


@bot.command()
async def play(ctx):
    result = json.loads(requests.get(
        "https://api.mcsrvstat.us/2/play.rezxis.net").text)
    if result['online']:
        await ctx.message.channel.send(f"Rezxis is online! (`play.rezxis.net`)\n"
                                       f"`{int(result['players']['online'])}`/`{int(result['players']['max'])}` players "
                                       f"are online!\n "
                                       f"Supported by: <https://mcsrvstat.us/>")
    else:
        await ctx.message.channel.send(f"Rezxis is offline.\n"
                                       f"Supported by: <https://mcsrvstat.us/>")


@bot.command()
async def play2(ctx):
    result = json.loads(requests.get(
        "https://api.mcsrvstat.us/2/play2.rezxis.net").text)
    if result['online']:
        await ctx.message.channel.send(f"Rezxis is online! (`play2.rezxis.net`)\n"
                                       f"`{int(result['players']['online'])}`/`{int(result['players']['max'])}` players "
                                       f"are online!\n "
                                       f"Supported by: <https://mcsrvstat.us/>")
    else:
        await ctx.message.channel.send(f"Rezxis is offline.\n"
                                       f"Supported by: <https://mcsrvstat.us/>")


@bot.command()
async def mchosting(ctx):
    result = json.loads(requests.get(
        "https://api.mcsrvstat.us/2/mchosting.rezxis.net").text)
    if result['online']:
        await ctx.message.channel.send(f"Rezxis is online! (`mchosting.rezxis.net`)\n"
                                       f"`{int(result['players']['online'])}`/`{int(result['players']['max'])}` players "
                                       f"are online!\n "
                                       f"Supported by: <https://mcsrvstat.us/>")
    else:
        await ctx.message.channel.send(f"Rezxis is offline.\n"
                                       f"Supported by: <https://mcsrvstat.us/>")


@bot.command()
async def whoami(ctx):
    userdata = json.loads(requests.get(
        f"{os.environ['API_URL']}{ctx.message.author.id}").text)
    if userdata["code"] != 0:
        await ctx.channel.send(f"あなたは…誰ですか…？\n"
                               f"DiscordアカウントとMinecraftアカウントをリンクしていないようです。\n"
                               f"<#681345663908577294>でアカウントをリンクしてください！")
        return
    mcid = json.loads(requests.get(
        f"https://api.mojang.com/user/profiles/{userdata['message'].replace('-', '')}/names").text)[-1]["name"]
    await ctx.message.channel.send(f"あなたは`{mcid}`さんですね！\n"
                                   f"タブン…")


# こっからまたテンプレ
bot.run(os.environ['DISCORD_BOT_TOKEN'])
