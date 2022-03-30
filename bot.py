import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio
from datetime import datetime
import os
import aiohttp
from googletrans import Translator
import traceback
import sys
import wikipediaapi

intents = discord.Intents.default()
intents.members = True
intents.presences = True

client = commands.Bot(command_prefix=commands.when_mentioned_or('r:'), intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name="people requesting"), status=discord.Status.online)
client.launch_time = datetime.utcnow()
client.remove_command('help')

@tasks.loop(seconds=120)
async def change_activity():
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="r:help"))
  await asyncio.sleep(60)
  await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="people requesting"))

change_activity.start()

@change_activity.before_loop
async def before_change_activity():
  await client.wait_until_ready()

@client.event
async def on_ready():
  print('Ready to request!')
        
@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):
    await ctx.message.add_reaction("❓")
  else:
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
  
  if isinstance(error, commands.MissingPermissions):
    perms = ", ".join(error.missing_perms)
    if error.missing_perms == 1:
      await ctx.send(f"I am missing the following permission: {perms}")
    elif error.missing_perms > 1:
      await ctx.send(f"I am missing the following permissions: {perms}")

@commands.is_owner()
@client.command()
async def servers(ctx):
  await ctx.send(len(client.guilds))

from replit import db

@client.command(aliases=['set announcement chnannel', 'sac'])
async def set_announcement_channel(ctx, channel:discord.TextChannel):
  db[ctx.guild.id] = channel.id
  await ctx.send("Announcement channel has been set!")

@set_announcement_channel.error
async def set_announcement_channel_error(ctx, error):
  if isinstance(error, commands.ChannelNotFound):
    await ctx.send(f"{error.argument} doesn't exist in this server")

@commands.is_owner()
@client.command()
async def send(ctx, news, *, message):
  if ctx.guild.id in db.keys():
    announcement_channel_set = False
    if announcement_channel_set:
      for messages_send in db.get(db.keys()):
        embed=discord.Embed(
          title=f"{news.capitalize()} News",
          description=message + "\n\n@everyone",
          color=0x5865F2
        )
        embed.set_footer(text="<> - Required | [] - Optional")

        announcement_channel_set = True

        await db.keys().send(embed=embed)
      else:
        for guild in client.guilds:
          system_channel = guild.system_channel
          embed=discord.Embed(
            title=f"{news.capitalize()} News",
            description=message + "\n\n@everyone",
            color=0x5865F2
          )
          embed.set_footer(text="<> - Required | [] - Optional")
          try:
            await system_channel.send(embed=embed)
            await ctx.reply("Message sent!")
          except discord.Forbidden:
            pass

@send.error
async def send_error(ctx, error):
  if isinstance(error, commands.NotOwner):
    await ctx.send("You're not my owner.")
    
@client.command()
async def help(ctx):
  help = discord.Embed(
    title="Help",
    description="I am a bot based on APIs, my prefix is `r:`.\nI am coded with Python and made by LAVIESTES#8692.",
    color=0x39ff1f,
  )
  help.add_field(
    name="Command List",
    value="-covid [country]\n-weather <city>\n-translate <language> <message>\n-forecast <city/country> [hour]\n-meme [subreddit]\n-astro <city>\n-quote [topic]\n-invite",
    inline=False
  )
  help.add_field(
    name="For more info",
    value="Check out this website: soon",
    inline=False
  )
  help.set_footer(text="<> - Required | [] - Optional")

  await ctx.send(embed=help)

@commands.has_permissions(embed_links=True)
@client.command()
async def wiki(ctx, *, question):
  wiki_wiki = wikipediaapi.Wikipedia('en')

  page = wiki_wiki.page(question)

  if page.exists() == True:
    result = discord.Embed(
      title=page.title,
      url=page.fullurl,
      color=0xfffff1
    )

    # await ctx.send(embed=result)

    sections = {}

    for num, section in enumerate(page.sections):
      await ctx.send(str(num+1) + ") " + str(section.title))
      sections[num+1] = section.text[0:3997] + '...'

    def check(m):
      return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id and m.content.isdigit()

    try:
      msg = await client.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
      await ctx.send("Timeout! Try again.")
    else:
      await ctx.send(sections[int(msg.content)])      

    # await ctx.send(page.summary[0:1997] + '...')
    
  else:
    await ctx.send("Page does not exist.")

@commands.has_permissions(embed_links=True)
@client.command()
async def quote(ctx, topic=None):
  async with aiohttp.ClientSession() as session:
    if not topic:
      async with session.get(f'https://api.quotable.io/random') as resp:
        js = await resp.json()
        
        quote = discord.Embed(
          title=f"{js['author']} says:",
          description=f"{js['content']}",
          color=0x4af6ff
        )

        quote.set_footer(text="#" + " #".join(quote for quote in js["tags"]))

        await ctx.send(embed=quote)
    else:
      async with session.get(f'https://api.quotable.io/random?tags={topic.replace(" ", ",")}') as resp:
        js = await resp.json()

        quote = discord.Embed(
          title=f"{js['author']} says:",
          description=f"{js['content']}",
          color=0x4af6ff
        )

        quote.set_footer(text="#" + " #".join(quote for quote in js["tags"]))

        await ctx.send(embed=quote)

@quote.error
async def quote_handler(ctx, error):
  if isinstance(error, commands.CommandError):
    await ctx.send("Could not find any matching quote.")

@commands.has_permissions(embed_links=True, attach_files=True)
@client.command()
async def meme(ctx, topic=None):
  async with aiohttp.ClientSession() as session:
    if topic is not None:
      async with session.get(f'https://meme-api.herokuapp.com/gimme/{topic}') as resp:
        js = await resp.json()
        embed = discord.Embed(
          title=js['title'].capitalize(),
          url=js['url'],
          color=0x000001
        )
        embed.set_image(url=js['url'])
        embed.set_footer(text=f'👍{str(js["ups"])}')
    else:
      async with session.get(f'https://meme-api.herokuapp.com/gimme') as resp:
        js = await resp.json()
        embed = discord.Embed(
          title=js['title'].capitalize(),
          url=js['url'],
          color=0x000001
        )
        embed.set_image(url=js['url'])
        embed.set_footer(text=f'👍{str(js["ups"])}')
    await ctx.send(embed=embed)

@client.command()
async def yt(ctx, *, question):
  async with aiohttp.ClientSession() as session:
    async with session.get(f'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={question}&key={os.environ.get("YOUTUBE_API_KEY")}') as resp:
      js = await resp.json()
      print(js)
      youtube = discord.Embed(
        title=f"Youtube Search Results For {question.capitalize()[:2] + '...'}",
        color=0xff0000
      )
      description = None
      description1 = None
      description2 = None
      description3 = None
      description4 = None

      if js['items'][0]['id']['kind'] == 'youtube#channel':
        title = js['items'][0]['snippet']['title'][:10] + ' - Channel'
        if len(js['items'][0]['snippet']['description']) > 29:
          description = f"[{js['items'][0]['snippet']['description'][:20] + '...' + js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][0]['id']['channelId']})"
        elif len(js['items'][0]['snippet']['description']) <= 29:
          description = f"[{js['items'][0]['snippet']['description'][:20] + ' - ' + js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][0]['id']['channelId']})"
        elif js['items'][0]['snippet']['description'] == '':
          description = f"[None](https://www.youtube.com/channel/{js['items'][0]['snippet']['channelId']})"
      elif js['items'][0]['id']['kind'] == 'youtube#video':
        title = js['items'][0]['snippet']['title'][:8] + ' - Video'
        if len(js['items'][0]['snippet']['description']) > 29:
          description = f"[{js['items'][0]['snippet']['description'][:20] + '...' + js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][0]['id']['videoId']})"
        elif len(js['items'][0]['snippet']['description']) <= 29:
          description = f"[{js['items'][2]['snippet']['description'][:20] + ' - ' + js['items'][0]['snippet']['publishedAt'][8]}](https://www.youtube.com/watch?v={js['items'][0]['id']['videoId']})"
        elif js['items'][0]['snippet']['description'] == '':
          description = f"[None](https://www.youtube.com/watch?v={js['items'][0]['id']['videoId']})"
      elif js['items'][0]['id']['kind'] == 'youtube#playlist':
        title = js['items'][0]['snippet']['title'][:11] + ' - Playlist'
        if len(js['items'][0]['snippet']['description']) > 29:
          description = f"[{js['items'][0]['snippet']['description'][:20] + '...' + js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?list={js['items'][0]['id']})"
        elif len(js['items'][0]['snippet']['description']) <= 29:
          description = f"[{js['items'][0]['snippet']['description'][:20] + ' - ' + js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/playlist?list={js['items'][0]['id']['playlistId']})"
        elif js['items'][0]['snippet']['description'] == '':
          description = f"[None - {js['items'][0]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?list={js['items'][0]['id']['playlistId']})"

      if js['items'][1]['id']['kind'] == 'youtube#channel':
        title1 = js['items'][1]['snippet']['title'][:10] + ' - Channel'
        if len(js['items'][1]['snippet']['description']) > 29:
          description1 = f"[{js['items'][1]['snippet']['description'][:20] + '...' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][1]['snippet']['channelId']})"
        elif len(js['items'][1]['snippet']['description']) <= 29:
          description2 = f"[{js['items'][1]['snippet']['description'][:20] + ' - ' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][1]['id']['channelId']})"
        elif js['items'][1]['snippet']['description'] == '':
          description1 = f"[None](https://www.youtube.com/c/{js['items'][1]['snippet']['channelId']})"
      elif js['items'][1]['id']['kind'] == 'youtube#video':
        title1 = js['items'][1]['snippet']['title'][:8] + ' - Video'
        if len(js['items'][1]['snippet']['description']) > 29:
          description1 = f"[{js['items'][1]['snippet']['description'][:20] + '...' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][1]['id']['videoId']})"
        elif len(js['items'][1]['snippet']['description']) <= 29:
          description1 = f"[{js['items'][1]['snippet']['description'][:20] + ' - ' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?list={js['items'][1]['id']['channelId']})"
        elif js['items'][1]['snippet']['description'] == '':
          description1 = f"[None](https://www.youtube.com/watch?v={js['items'][1]['id']['videoId']})"
      elif js['items'][1]['id']['kind'] == 'youtube#playlist':
        title1 = js['items'][1]['snippet']['title'][:11] + ' - Playlist'
        if len(js['items'][1]['snippet']['description']) > 29:
          description1 = f"[{js['items'][1]['snippet']['description'][:20] + '...' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][1]['id']['videoId']})"
        elif len(js['items'][1]['snippet']['description']) <= 29:
          description1 = f"[{js['items'][1]['snippet']['description'][:20] + ' - ' + js['items'][1]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?list={js['items'][1]['id']['playlistId']})"
        elif js['items'][1]['snippet']['description'] == '':
          description1 = f"[None - {js['items'][1]['snippet']['publishedAt'][:9]}](https://www.youtube.com/watch?list={js['items'][1]['id']['playlistId']})"
      
      if js['items'][2]['id']['kind'] == 'youtube#channel':
        title2 = js['items'][2]['snippet']['title'][10:] + ' - Channel'
        if len(js['items'][2]['snippet']['description']) > 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + '...' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][2]['id']['channelId']})"
        elif len(js['items'][2]['snippet']['description']) <= 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + ' - ' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][2]['id']['channelId']})"
        elif len(js['items'][2]['snippet']['description']) >= 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + ' - ' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?list={js['items'][2]['id']['channelId']})"
        elif js['items'][2]['snippet']['description'] == '':
          description2 = f"[None](https://www.youtube.com/c/{js['items'][2]['snippet']['channelId']})"
      elif js['items'][2]['id']['kind'] == 'youtube#video':
        title2 = js['items'][2]['snippet']['title'][10:] + ' - Video'
        if len(js['items'][2]['snippet']['description']) > 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + '...' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][2]['id']['videoId']})"
        elif len(js['items'][2]['snippet']['description']) <= 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + ' - ' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][2]['id']['videoId']})"
        elif js['items'][2]['snippet']['description'] == '':
          description2 = f"[None](https://www.youtube.com/watch?v={js['items'][2]['id']['videoId']})"
      elif js['items'][2]['id']['kind'] == 'youtube#playlist':
        title2 = js['items'][2]['snippet']['title'][:11] + ' - Playlist'
        if len(js['items'][2]['snippet']['description']) > 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + '...' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/playlist?list={js['items'][2]['id']['playlistId']})"
        elif len(js['items'][2]['snippet']['description']) >= 29:
          description2 = f"[{js['items'][2]['snippet']['description'][:20] + ' - ' + js['items'][2]['snippet']['publishedAt'][:10]}](https://www.youtube.com/playlist?list={js['items'][2]['id']['playlistId']})"
        elif js['items'][2]['snippet']['description'] == '':
          description2 = f"[None - {js['items'][2]['snippet']['publishedAt'][:9]}](https://www.youtube.com/playlist?list={js['items'][2]['id']['playlistId']})"
      
      if js['items'][3]['id']['kind'] == 'youtube#channel':
        title3 = js['items'][3]['snippet']['title'][10:] + ' - Channel'
        if len(js['items'][3]['snippet']['description']) > 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + '...' + js['items'][3]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][3]['snippet']['channelId']})"
        elif len(js['items'][3]['snippet']['description']) <= 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + ' - ' + js['items'][3]['snippet']['publishedAt'][:10]}](https://www.youtube.com/channel/{js['items'][3]['id']['channelId']})"
        elif js['items'][3]['snippet']['description'] == '':
          description3 = f"[None](https://www.youtube.com/channel/{js['items'][3]['snippet']['channelId']})"
      elif js['items'][3]['id']['kind'] == 'youtube#video':
        title3 = js['items'][3]['snippet']['title'][10:] + ' - Video'
        if len(js['items'][3]['snippet']['description']) > 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + '...' + js['items'][3]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?v={js['items'][3]['id']['videoId']})"
        elif len(js['items'][3]['snippet']['description']) <= 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + ' - ' + js['items'][3]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][3]['id']['videoId']})"
        elif js['items'][3]['snippet']['description'] == '':
          description3 = f"[None](https://www.youtube.com/watch?v={js['items'][3]['id']['videoId']})"
      elif js['items'][3]['id']['kind'] == 'youtube#playlist':
        title3 = js['items'][3]['snippet']['title'][11:] + ' - Playlist'
        if len(js['items'][3]['snippet']['description']) > 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + '...' + js['items'][3]['snippet']['publishedAt'][:10]}](https://www.youtube.com/watch?v={js['items'][3]['id']['videoId']})"
        elif len(js['items'][3]['snippet']['description']) <= 29:
          description3 = f"[{js['items'][3]['snippet']['description'][:20] + ' - ' + js['items'][3]['snippet']['publishedAt'][:8]}](https://www.youtube.com/playlist?list={js['items'][3]['id']['playlistId']})"
        elif js['items'][3]['snippet']['description'] == '':
          description3 = f"[None - {js['items'][3]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?list={js['items'][3]['id']['playlistId']}))"
      
      if js['items'][4]['id']['kind'] == 'youtube#channel':
        title4 = js['items'][4]['snippet']['title'][:10] + ' - Channel'
        if len(js['items'][4]['snippet']['description']) > 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + '...' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/channel/{js['items'][4]['snippet']['channelId']})"
        elif len(js['items'][4]['snippet']['description']) <= 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + ' - ' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/channel/{js['items'][4]['id']['channelId']})"
        elif js['items'][4]['snippet']['description'] == '':
          description4 = f"[None](https://www.youtube.com/channel/{js['items'][4]['snippet']['channelId']})"
      elif js['items'][4]['id']['kind'] == 'youtube#video':
        title4 = js['items'][4]['snippet']['title'][:8] + ' - Video'
        if len(js['items'][4]['snippet']['description']) > 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + '...' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?v={js['items'][4]['id']['videoId']})"
        elif len(js['items'][4]['snippet']['description']) <= 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + ' - ' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?v={js['items'][4]['id']['videoId']})"
        elif js['items'][4]['snippet']['description'] == '':
          description4 = f"[None](https://www.youtube.com/watch?v={js['items'][4]['id']['videoId']})"
      elif js['items'][4]['id']['kind'] == 'youtube#playlist':
        title4 = js['items'][4]['snippet']['title'][:11] + ' - Playlist'
        if len(js['items'][4]['snippet']['description']) > 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + '...' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?v={js['items'][4]['id']['videoId']})"
        elif len(js['items'][4]['snippet']['description']) >= 29:
          description4 = f"[{js['items'][4]['snippet']['description'][:20] + ' - ' + js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/playlist?list={js['items'][4]['id']['channelId']})"
        elif js['items'][4]['snippet']['description'] == '':
          description4 = f"[None - {js['items'][4]['snippet']['publishedAt'][:8]}](https://www.youtube.com/watch?list={js['items'][4]['id']['playlistId']})"

      youtube.add_field(
        name=title,
        value=description,
        inline=False
      )
      youtube.add_field(
        name=title1,
        value=description1,
        inline=False
      )
      youtube.add_field(
        name=title2,
        value=description2,
        inline=False
      )
      youtube.add_field(
        name=title3,
        value=description3,
        inline=False
      )
      youtube.add_field(
        name=title4,
        value=description4,
        inline=False
      )
      youtube.set_thumbnail(url="https://play-lh.googleusercontent.com/lMoItBgdPPVDJsNOVtP26EKHePkwBg-PkuY9NOrc-fumRtTFP4XhpUNk_22syN4Datc")
      await ctx.send(embed=youtube)

@commands.has_permissions(embed_links=True)
@client.command()
async def invite(ctx):
  resp = discord.Embed(
    title="Invite Link",
    description="Invite me [here](https://discord.com/api/oauth2/authorize?client_id=896485914245734480&permissions=322624&scope=bot)",
    color=0xf8ff1f
  )
  await ctx.send(embed=resp)
@commands.has_permissions(embed_links=True)
@client.command()
async def translate(ctx, lang, *, message):
  translator = Translator(service_urls=['translate.google.com'])
  result = translator.translate(message, dest=lang)
  await ctx.message.delete()
  title1 = translator.translate(f"Translation From", dest=lang)
  title2 = translator.translate(f"To", dest=lang)
  description = translator.translate("Sentence", dest=lang)
  resp = discord.Embed(
    title=f"{title1.text} {result.src.capitalize()} {title2.text} {result.dest.capitalize()}",
    description=f"**{description.text}:** {result.origin}",
    color=0xff801f
  )
  translation_result = translator.translate("Translation Result", dest=lang)
  resp.add_field(
    name=f"{translation_result.text}:",
    value=result.text.capitalize(),
    inline=False
  )

  pronunciation = translator.translate("Pronunciation", dest=lang)
  resp.add_field(
    name=f"{pronunciation.text}",
    value=result.pronunciation
  )
  resp.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
  
  
  await ctx.send(embed=resp)

@translate.error
async def translate_error(ctx, error):
  if isinstance(error, commands.CommandError):
    await ctx.send("Message is too long/Invalid language")

@commands.has_permissions(embed_links=True)
@client.command()
async def covid(ctx, country=None):
  if country is None:
    async with aiohttp.ClientSession() as session:
      async with session.get('https://disease.sh/v3/covid-19/all') as resp:
        js = await resp.json()
        virus = discord.Embed(
          title="COVID Stats",
          description=f"**-Total Cases:** {js['cases']:,}\n**-Today cases:** {js['todayCases']:,}\n**-Deaths:** {js['deaths']:,}\n**-Todays deaths:** {js['todayDeaths']:,}\n**-Recoveries:** {js['recovered']:,}\n**-Today recoveries:** {js['todayRecovered']}\n**-Active:** {js['active']:,}\n**-Critical:** {js['critical']:,}\n**-Tests:** {js['tests']:,}",
          color=0x666666
        )
        virus.set_thumbnail(url='https://www.apsf.org/wp-content/uploads/newsletters/2020/3502/coronavirus-covid-19.png')

        await ctx.send(embed=virus)
  else:
    async with aiohttp.ClientSession() as session:
      async with session.get(f'https://disease.sh/v3/covid-19/countries/{country}') as resp:
        js = await resp.json()
        virus = discord.Embed(
          title=f"COVID Stats For {country.capitalize()}",
          description=f"**-Total Cases:** {js['cases']:,}\n**-Deaths:** {js['deaths']:,}\n**-Todays deaths:** {js['todayDeaths']:,}\n**-Recoveries:** {js['recovered']:,}\n**-Today recoveries:** {js['todayRecovered']}\n**-Today cases:** {js['todayCases']:,}\n**-Active:** {js['active']:,}\n**-Critical:** {js['critical']:,}\n**-Tests:** {js['tests']:,}",
          color=0x666666
        )
        virus.set_thumbnail(url='https://www.apsf.org/wp-content/uploads/newsletters/2020/3502/coronavirus-covid-19.png')
        virus.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=virus)

@covid.error
async def covid_error(ctx, error):
  if isinstance(error, commands.CommandError):
    await ctx.send("Make sur to put a valid country name.")
        
@commands.has_permissions(embed_links=True)
@client.command()
async def ggl(ctx, *, question):
  params = {'key': os.environ.get("GOOGLE_API_KEY"), "cx": "e367fa34ef717987e", "q": question}
  async with aiohttp.ClientSession() as session:
    async with session.get("https://www.googleapis.com/customsearch/v1", params=params) as resp:
      js = await resp.json()
      articles = []
      for _ in list(js['items']):
        articles.append({
          'title': _['title'],
          'link': _['link'],
          'snippet': _['snippet']
        })
      search_title = articles[0]['title']
      if len(search_title) > 29:
        search_title = search_title[:29] + '...'
      search_title1 = articles[1]['title']
      if len(search_title1) > 29:
        search_title1 = search_title1[:29] + '...'
      search_title2 = articles[2]['title']
      if len(search_title2) > 29:
        search_title2 = search_title2[:29] + '...'
      search_title3 = articles[3]['title']
      if len(search_title3) > 29:
        search_title3 = search_title3[:29] + '...'
      search_title4 = articles[4]['title']
      if len(search_title4) > 29:
        search_title4 = search_title4[:29] + '...'
      results = discord.Embed(
        title=f'Results For {question.capitalize()}',
        color=0xffffff
      )
      results.add_field(
        name=search_title,
        value=f"[{articles[0]['snippet'][:38] + '...'}]({articles[0]['link']})",
        inline=False
      )
      results.add_field(
        name=search_title1,
        value=f"[{articles[1]['snippet'][:38] + '...'}]({articles[1]['link']})",
        inline=False
      )
      results.add_field(
        name=search_title2,
        value=f"[{articles[2]['snippet'][:38] + '...'}]({articles[2]['link']})",
        inline=False
      )
      results.add_field(
        name=search_title3,
        value=f"[{articles[3]['snippet'][:38] + '...'}]({articles[3]['link']})",
        inline=False
      )
      results.add_field(
        name=search_title4,
        value=f"[{articles[4]['snippet'][:38] + '...'}]({articles[4]['link']})",
        inline=False
      )
      results.set_thumbnail(url='https://storage.googleapis.com/support-kms-prod/ZAl1gIwyUsvfwxoW9ns47iJFioHXODBbIkrK')
      results.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
      await ctx.send(embed=results)

@commands.has_permissions(embed_links=True)
@client.command()
async def weather(ctx, city):
  async with aiohttp.ClientSession() as session:
    async with session.get(f'http://api.weatherapi.com/v1/current.json?key={os.environ.get("WEATHER_API_KEY")}&q={city}&aqi=no&alerts=no') as resp:
      js = await resp.json()
      if js['current']['is_day'] == 1:
        js['current']['is_day'] = 'yes'
      else:
        js['current']['is_day'] = 'no'
      currentweather = discord.Embed(
        title=f"Current Weather For {city.capitalize()}",
        description=f"**-City:** {js['location']['name']}\n**-Country:** {js['location']['country']}\n**-Time:** {js['location']['localtime']}\n**-Temperature in Celsius(C):** {js['current']['temp_c']}°\n**-Temperature in Fahrenheit(F):** {js['current']['temp_f']}°\n**-Is day:** {js['current']['is_day']}\n**-Stat:** {js['current']['condition']['text']}\n**-Wind speed in kilometers per hour:** {js['current']['wind_kph']}\n**-Wind precipitation:** {js['current']['wind_degree']}°\n**-Humidity:** {js['current']['humidity']}%",
        color=0x00ffff
      )
      currentweather.set_thumbnail(url='https:' + js['current']['condition']['icon'])
      currentweather.set_footer(text='Last updated on the ' + js['current']['last_updated'].replace("-", "/").replace(" ", " | "))
      currentweather.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

      await ctx.send(embed=currentweather)

@weather.error
async def weather_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Make sure to provide a valid **city**.")

@commands.has_permissions(embed_links=True)
@client.command()
async def forecast(ctx, city, hour=None):
  async with aiohttp.ClientSession() as session:
    async with session.get(f'http://api.weatherapi.com/v1/forecast.json?key={os.environ.get("WEATHER_API_KEY")}&q={city}&days=1&aqi=no&alerts=yes') as resp:
      js = await resp.json()
      if hour is not None:
        for result in js['forecast']['forecastday'][0]['hour']:
          for key, value in result.items():
            if key == 'time' and hour in value[11:][:3]:
              forecast = discord.Embed(
                title=f"Forecast For {js['location']['name'].capitalize()} At {js['forecast']['forecastday'][0]['hour'][0]['time'][11:]}",
                description=f"**-City:** {js['location']['name']}\n**-Country:** {js['location']['country']}\n**-Local Time:** {js['location']['localtime']}\n**-Temperature in Celsius(C):** {js['forecast']['forecastday'][0]['hour'][0]['temp_c']}°\n**-Temperature in Fahrenheit(F):** {js['forecast']['forecastday'][0]['hour'][0]['temp_f']}°\n**-Stat:** {js['forecast']['forecastday'][0]['hour'][0]['condition']['text']}\n**-Wind speed in kilometers per hour:** {js['forecast']['forecastday'][0]['hour'][0]['wind_kph']}\n**-Wind precipitation:** {js['forecast']['forecastday'][0]['hour'][0]['wind_degree']}°\n**-Humidity:** {js['forecast']['forecastday'][0]['hour'][0]['humidity']}%",
                color=0x003994
              )
              forecast.set_thumbnail(url='https:' + js['forecast']['forecastday'][0]['hour'][0]['condition']['icon'])
              forecast.set_footer(text='Last updated on the ' + js['current']['last_updated'].replace("-", "/").replace(" ", " | "))
              await ctx.send(embed=forecast)
              break
      else:
        forecast = discord.Embed(
          title=f"Forecast For {js['location']['name'].capitalize()}",
          description=f"**-City:** {js['location']['name']}\n**-Country:** {js['location']['country']}\n**-Local Time:** {js['location']['localtime']}\n**-Max temperature in Celsius(C):** {js['forecast']['forecastday'][0]['day']['maxtemp_c']}°\n**-Max temperature in Farhenheit(F):** {js['forecast']['forecastday'][0]['day']['maxtemp_f']}°\n**-Max wind speed in kilometers per hour:** {js['forecast']['forecastday'][0]['day']['maxwind_kph']}\n**-Average relative humidity:** {js['forecast']['forecastday'][0]['day']['avghumidity']}%\n**-Chance of rain:** {js['forecast']['forecastday'][0]['day']['daily_chance_of_rain']}%\n**-Chance of snow:** {js['forecast']['forecastday'][0]['day']['daily_chance_of_snow']}%\n**-Total precipitation in Millimeters(mm):** {js['forecast']['forecastday'][0]['day']['totalprecip_mm']}\n**-Average relative visibility in Kilometers(km):** {js['forecast']['forecastday'][0]['day']['avgvis_km']}\n**-Stat:** {js['forecast']['forecastday'][0]['day']['condition']['text']}",
          color=0x003994
        )
        await ctx.send(embed=forecast)
        alerts = []
        for alerts_loop in js['alerts']['alert']:
          alerts.append(Translator().translate(alerts_loop, dest='en'))
          print(alerts_loop)
        print(alerts)
        if not alerts:
          forecast.add_field(
            name="Alerts",
            value='No alerts',
            inline=False
          )
        else:
          forecast.add_field(
            name="Alerts",
            value=alerts,
            inline=False
          )
        forecast.set_thumbnail(url='https:' + js['forecast']['forecastday'][0]['day']['condition']['icon'])
        forecast.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=forecast)

@forecast.error
async def weather_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Make sure to provide a valid **city** or **country** name and (optional) an hour with **24 format** containing two numbers.")

@commands.has_permissions(embed_links=True)
@client.command()
async def astro(ctx, city):
  async with aiohttp.ClientSession() as session:
    async with session.get(f'http://api.weatherapi.com/v1/forecast.json?key={os.environ.get("WEATHER_API_KEY")}&q={city}&days=1&aqi=no&alerts=no') as resp:
      js = await resp.json()
      astro = discord.Embed(
        title=f"Astro For {js['location']['name'].capitalize()}",
        description=f"**-Sunrise:** {js['forecast']['forecastday'][0]['astro']['sunrise']}\n**-Sunset:** {js['forecast']['forecastday'][0]['astro']['sunset']}\n**-Moonrise:** {js['forecast']['forecastday'][0]['astro']['moonrise']}\n**-Moonset:** {js['forecast']['forecastday'][0]['astro']['moonset']}\n**-Moon phase:** {js['forecast']['forecastday'][0]['astro']['moon_phase'].lower()}\n**-Moon illumination:** {js['forecast']['forecastday'][0]['astro']['moon_illumination']}",
        color=0xffc933
      )
      astro.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    async with session.get(f'https://api.pray.zone/v2/times/today.json?city={city}')as resp:
      js = await resp.json()
      astro.add_field(
        name="For Muslims",
        value=f"**-Imsak:** {js['results']['datetime'][0]['times']['Imsak']}\n**-Fajr:**{js['results']['datetime'][0]['times']['Fajr']}\n**-Sunrise:** {js['results']['datetime'][0]['times']['Sunrise']}\n**-Dhuhr:** {js['results']['datetime'][0]['times']['Dhuhr']}\n**-Asr:** {js['results']['datetime'][0]['times']['Asr']}\n**-Sunset:** {js['results']['datetime'][0]['times']['Sunset']}\n**-Maghrib:** {js['results']['datetime'][0]['times']['Maghrib']}\n**-Isha:** {js['results']['datetime'][0]['times']['Isha']}\n**-Midnight:** {js['results']['datetime'][0]['times']['Midnight']}"
      )

    await ctx.send(embed=astro)

@astro.error
async def astro_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Make sure to provide a valid **city**.")
client.run(os.environ["DISCORD_TOKEN"])
