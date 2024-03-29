import discord ,  sandbox , aiosqlite , random ,  os , time , asyncio 
from typing import Final
from discord.ext import commands
from discord import app_commands , Embed
#from databaseMng import chose_random , list_challenges_for , enrollement , registering
from asyncDatabaseMng import DatabaseManager
from uuid import uuid4
import discord

PATH:Final = "C:\\Users\\sts\\Documents\\CODING\\python\\DiscordBot\\main.db"
dbmanager = DatabaseManager(PATH)



async def sendPost(bot , details , dbmanager):
    #details contain the server to send to + channel + time of posting
    while True : 

        print("not yet ")
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        posting_time = time.localtime(int(details[2]))
        posting_hour = posting_time.tm_hour
        posting_minute = posting_time.tm_min
        

        # Check if the current time matches the target time
        if (current_hour > posting_hour) or (current_hour == posting_hour  and current_minute > posting_minute) :
            
            for server in bot.guilds:
                print(f"server id : {server.id } matching with {details[4]}")
                if server.id == details[4] : 
                    for channel in server.channels :
                        if channel.type.name == 'text' and channel.id == details[5]:
                            
                            await channel.send(f"here's todays challenge : \nhttps://leetcode.com/problems/{details[1]}/description/  \nenjoy! " , suppress_embeds=True)
                            await dbmanager.mark_challenge_sent(details[3] , details[6])
        await asyncio.sleep(10)


async def fetch_today_challenges():

    ongoing_evts = await dbmanager.list_ongoing_evts()
    ongoing_evts_ids = [evt[0] for evt in ongoing_evts]
    print(ongoing_evts_ids)
    for evt in ongoing_evts_ids :
        challenges = await dbmanager.list_challenges_for(evt) 
        print(f"challenges : {challenges}")
        challenges_list = []
        for challenge in challenges :
            print(f" challenge[4]  : { challenge[4]}")  
            if (int(challenge[2])//86400 == int(time.time())//86400) :
                challenges_list.append((challenge[3] , evt , challenge[2]))
        return challenges_list
    return []
                

def run_discord_bot():
    TOKEN = os.getenv('reallycoolbot_token')
    print(TOKEN)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.guilds = True

    bot = commands.Bot(command_prefix='/'  , intents= intents)


    @bot.event
    async def on_ready():
        try : 
            today_challs =  []
            
            
            synced = await bot.tree.sync() 
            print(f"synced  : {len(synced)} commands")

            #EVERYDAY
            while True : 
        
                await dbmanager.populate_submissions() 
        
                today_challs = await fetch_today_challenges()
        
                print(f"todays challenge : {today_challs}")
        
                for chall in today_challs :     

                                    
                    challenge_details = await dbmanager.get_challenge_details( chall[0] , chall[1] )
            
                    print(f"challenge_details : {challenge_details}")
                    asyncio.ensure_future(sendPost(bot , challenge_details , dbmanager))
            
                await asyncio.sleep(60)
                print('refresh submissions')
            

        except Exception as e : 
            
            print(e.with_traceback())
            
            



        
        print(f"{bot.user} is running ")
   
   
    #################################### enroll ###################################################
    
    @bot.tree.command(name="enroll")
    @app_commands.describe(evt='enter event id')
    async def enroll( interaction: discord.Interaction , evt:str):
        try : 
            await dbmanager.enrollement(interaction.user.name , evt )
            await interaction.response.send_message(f"{interaction.user.mention } congrats you're in ")
        except Exception as e : 
            await interaction.response.send_message(f"{e.args[0]}")
    #################################### register ###################################################
            

    @bot.tree.command(name="register")
    @app_commands.describe(username='enter leetcode username')
    async def register( interaction: discord.Interaction , username:str):
        try : 

            await dbmanager.registering(interaction.user.name , username , interaction.user.nick )
            await interaction.response.send_message(f"{interaction.user.mention } you're now resigtered in the system !")
        except Exception as e : 
            await interaction.response.send_message(e)

#################################### my stats ###################################################
            

    @bot.tree.command(name="my_stats")
    async def my_stats(interaction: discord.Interaction):
        try:
            stats = await dbmanager.get_stats(interaction.user.name)
            active_enrollements = ""
            for enrollment in stats[0]:
                active_enrollements += f" {enrollment[0]}-->{enrollment[1]} \n"
            previous_enrollements = " " if not stats[1] else f"\n previous enrollements : {' -> '.join(stats[1])}"
            await interaction.response.send_message(f"your active enrollements  :\n {active_enrollements} {previous_enrollements} \nsince {stats[3]} , you've solved {stats[2]} challenges , with the longest streak being {stats[4]} days!")
        except Exception as e:
            await interaction.response.send_message(str(e))


    ####################################### start event ################################################
    @bot.tree.command(name="start_evt")
    @app_commands.describe(event='what is the event about ? ' , start_date = 'when is it starting' , end_date="when it ending " , notif_time="when to send the notification (HH)format")
    async def startevt(interaction: discord.Interaction , event:str , start_date:int , end_date:int , notif_time:int):
        if interaction.user.guild_permissions.administrator  :
        
            print(f"was sent from : {interaction.channel.name}")
            await interaction.response.send_message("enter search query ")
            while True:
                try:
                    query = await bot.wait_for("message", check=lambda msg: msg.author == interaction.user)
                    event_id = uuid4().int % 1000000
                    wherestmt = query.content 

                    message = await dbmanager.start_evt(event_id, event, start_date, end_date, wherestmt, interaction.guild_id, interaction.channel_id, notif_time)

                    # If start_evt completes without raising an exception, break out of the loop
                    break
                except Exception as e:
                    print(f"An error occurred: {e}")
                    await interaction.followup.send(f"An error occurred : {e} Please try again.")

        
            await interaction.followup.send(f" new event started by {interaction.user.nick} , {message}, code : {event_id} (you'll need this to enroll in the event)")

        
        else  :
            await interaction.response.send_message("https://tenor.com/view/mouse-gif-18572789")

            
    ####################################### delete event ################################################
    @bot.tree.command(name="delete_evt")
    @app_commands.describe(evt_id='enter the events id  ')
    async def startevt(interaction: discord.Interaction , evt_id:int ):
        if interaction.user.guild_permissions.administrator  :
            
            try :
                await dbmanager.delete_evt(evt_id)
                await interaction.response.send_message("event deleted")
            except Exception as e :
                await interaction.response.send_message(e)
            
        
        else  :
            await interaction.response.send_message("https://tenor.com/view/mouse-gif-18572789")

            
    
    
    ####################################### add challenge ################################################
    @bot.tree.command(name="add_challenge")
    @app_commands.describe(chal_id='challenge id' ,evt_id='to which event ?', start_time='when is it starting? (optional)')
    async def add_challenge(interaction: discord.Interaction , evt_id:str , chal_id:int , start_time:int = None):
        
        try :
            new_date = await dbmanager.add_challenge( evt_id ,  chal_id , start_time) 
        except Exception as e :
            await interaction.response.send_message(e)
        if new_date != None : 
            await interaction.response.send_message(f"new challenge was added \n {new_date}")
        else :
            await interaction.response.send_message("new challenge was added")
        

    ####################################### list_challenges_for ################################################
    @bot.tree.command(name="list_challenges_for")
    @app_commands.describe(evnt_id='get the list of challenges ')
    async def list_challenges(interaction: discord.Interaction , evnt_id:str):
        
        try : 
            rows = await dbmanager.list_challenges_for(evnt_id)
            rows_list = [t[0] for t in rows if int(time.time())>int(t[2])]

            rows_list =[' ']+rows_list
            rowsLines = "\n• ".join(rows_list)
            

            await interaction.response.send_message( f"past challenges :\n{rowsLines} \n------------------\n this event contains {len(rows)} challenges in total \n the rest will be revealed according to their respective starting time" )
        except Exception as e :
            await interaction.response.send_message(e) 
    ####################################### list_ongoing_events ################################################
    @bot.tree.command(name="list_ongoing")
    async def list_ongoing(interaction: discord.Interaction ):
        
        rows = await dbmanager.list_ongoing_evts()
        if len(rows) != 0 :
                
            rows_list = []
            for row in rows :
                rows_list.append(f"event : {row[1]} \nwith code: {row[0]} \n[ from {row[2]} to {row[3]}]\n")
            rowsLines = "\n".join(rows_list)
            await interaction.response.send_message( rowsLines )
        else  :
            await interaction.response.send_message( "there are no ongoin event currently " )
    
    ####################################### more details ################################################
    @bot.tree.command(name="get_details")
    @app_commands.describe(evnt_id='insert the events id')
    async def list_ongoing(interaction: discord.Interaction , evnt_id:int):
        
        try :
                    
            infos = await dbmanager.get_event_details(evnt_id)
            
            await interaction.response.send_message( infos )
        except Exception as e:
            await interaction.response.send_message( f"something went wrong {e}" )
     ####################################### leaderboard ################################################
    @bot.tree.command(name="leaderboard")
    @app_commands.describe(evnt_id='insert the events id')
    async def leaderboard(interaction: discord.Interaction , evnt_id:int) :
        
        participants = await dbmanager.get_leaderboard(evnt_id)
        text = "leaderboard : \n"
        for i , participant in enumerate(participants) :
            text += f"{i+1}. @{participant[0]} with {participant[1]} points \n"
            
        await interaction.response.send_message( text )
        
        
    
    bot.run(TOKEN)


