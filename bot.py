import firebase_admin
from firebase_admin import credentials, firestore
import discord 
from discord.ext import commands
import datetime

cred = credentials.Certificate("./botprivatekey.json")
firebase_admin.initialize_app(cred)

db = firestore.client() 

client = commands.Bot(command_prefix = '!')

@client.event
async def on_ready():
    print("Bot Is Ready")
        



@client.command()
async def start(ctx):
    #Starts Event

    global event_in_progress_flag
    global event_id

   
    
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    
    doc_ref = db.collection('events').document(f'{guild_id}')
    if doc_ref.get().exists: 
       await ctx.send('Server already has an ongoing event')
    else:
        doc_ref.set({
            'host': f'{author_id}',
            'users': []
        })
        await ctx.send('Event has started')
        await ctx.send('If you would like to participate, use the join command') 
        
 
    #event_in_progress_flag = True

@client.command()
async def join(ctx):
    '''
        User Join Event if not already participating
    '''
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection('events').document(f'{guild_id}')
    user_ref = db.collection('users').document(f'{author_id}')
    
    #check if event exist
    if not event_ref.get().exists: 
        await ctx.send('No event in progress, use the start command to begin an event')
        return

    
    #check if user exist in users collection
    if not user_ref.get().exists:
        user_ref.set({
            'wishlist': [], 
        })
    
    #add user to list of users in the server
    event_ref.update({'users': firestore.ArrayUnion([user_ref])})

    await ctx.send(f'{ctx.message.author} has been added to the event! :partying_face:')
    

#FIX-ME
@client.command()
async def add(ctx, *, wish):
    '''
        Add item into wishlist
    '''
    global event_id
    global event_in_progress_flag

    if not event_in_progress_flag:
        await ctx.send('No event in progress, use the start command to begin an event')
        return

    msg_auth = ctx.message.author.id

    collection = db.collection('event_participants')
    res = collection.document(f'{event_id}').update({f'participants.{msg_auth}': firestore.ArrayUnion([f'{wish}'])})

    user = client.get_user(msg_auth)
    await user.send(f'I added {wish} to your wishlist :upside_down:')


#FIX-ME
@client.command(aliases=['list'])
async def _list(ctx):
    '''
        Retrieve recipeint wishlist 
    '''
    global event_id
    global event_in_progress_flag

    if not event_in_progress_flag:
        await ctx.send('No event in progress, use the start command to begin an event')
        return

    msg_auth = ctx.message.author.id

    event_participants_dict = db.collection('event_participants').document(f'{event_id}').get().to_dict()

    user = client.get_user(msg_auth)
    ulist = event_participants_dict['participants'].get(f'{msg_auth}')

    await user.send(f'Here is your wishlist: {ulist}')

#Test          
@client.command()
async def randomize(ctx): 
    user_dicts = [ item.to_dict() for item in db.collection('users').get() ]
    
    for user in user_dicts:
        print(user['id'])
        if user['id']  != 0: 
            user = client.get_user(user['id'])
            if user != None:
                await user.send('Hello')
            else: 
                await ctx.send('failed:(')
        print('--------------')


client.run('')