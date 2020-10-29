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
        
event_id = ''
event_in_progress_flag = False

@client.command()
async def start(ctx):

    global event_in_progress_flag
    global event_id

    if event_in_progress_flag:
        await ctx.send('Event already in progress, use the join command')
        return

    collection = db.collection('events')
    event_id = datetime.datetime.now()
    res = collection.document(f'{event_id}').set({'id': f'{event_id}'})
    
    collection = db.collection('event_participants')
    res = collection.document(f'{event_id}').set({'event_id': f'{event_id}'})
    res = collection.document(f'{event_id}').update({'participants': {}})

    await ctx.send('Event has started')
    await ctx.send('If you would like to participate, use the join command')
    event_in_progress_flag = True

@client.command()
async def join(ctx):

    global event_id
    global event_in_progress_flag

    if not event_in_progress_flag:
        await ctx.send('No event in progress, use the start command to begin an event')
        return

    msg_auth = ctx.message.author.id

    user_dicts = [ item.to_dict() for item in db.collection('users').get() ]
    for user in user_dicts:
        if msg_auth in user.values():
            break
        else:
            collection = db.collection('users')
            res = collection.document(f'{msg_auth}').set({'id': msg_auth})

    event_participants_dicts = [ item.to_dict() for item in db.collection('event_participants').get() ]
    for event_participant in event_participants_dicts:
        if (str(event_id) == event_participant['event_id']):
            
            if (str(msg_auth) in event_participant['participants']):
                await ctx.send(f'{ctx.message.author}, you have already been added to the event! :rage:')
                return
            else:
                collection = db.collection('event_participants')
                res = collection.document(f'{event_id}').update({f'participants.{msg_auth}': []} )

    await ctx.send(f'{ctx.message.author} has been added to the event! :partying_face:')

    user = client.get_user(msg_auth)
    await user.send("Please use this channel to construct your wishlist using the add command")

@client.command()
async def add(ctx, *, wish):

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

@client.command(aliases=['list'])
async def _list(ctx):
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
            


client.run('NzY1MzgxOTA3MTM5MTMzNTIw.X4T_cg.mE8yghJf8AS8sjiPnDvG7xDPM1M')