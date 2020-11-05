import firebase_admin
from firebase_admin import credentials, firestore

import discord  
from discord.ext import commands

import datetime
import random

cred = credentials.Certificate("./botprivatekey.json")
firebase_admin.initialize_app(cred)

db = firestore.client() 

client = commands.Bot(command_prefix = '!')

@client.event
async def on_ready():
    print("Bot Is Ready")
        



@client.command()
async def start(ctx):
    '''
        Starts Event
    '''
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    
    doc_ref = db.collection('events').document(f'{guild_id}')
    if doc_ref.get().exists: 
       await ctx.send('Server already has an ongoing event')
       await ctx.send('If you would like to participate, use the !join command') 
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

    user = client.get_user(author_id)
    #check if user exist in users collection
    if not user_ref.get().exists:
        user_ref.set({
            'name' : f'{user.name}',
            'wishlist': [], 
        })
    
    #add user to list of users in the server
    event_ref.update({'users': firestore.ArrayUnion([user_ref])})

   
    await ctx.send(f'{ctx.message.author} has been added to the event! :partying_face:')
    await user.send("Use this channel to add/remove items to your wishlist")
    
    


@client.command()
async def add(ctx, *, wish):
    '''
        Add item into wishlist
    '''
   
    author_id = ctx.message.author.id
   
   
    user_ref = db.collection('users').document(f'{author_id}')
    

    user_ref.update({'wishlist': firestore.ArrayUnion([f'{wish}'])})
    user = client.get_user(author_id) 
    await user.send(f'I added {wish} to your wishlist :upside_down:')


#FIX-ME  
@client.command(aliases=['list'])
async def _list(ctx):
    '''
        Retrieve recipeint wishlist 
    '''

    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection('events').document(f'{guild_id}')
    event = event_ref.get().to_dict()
    
    rec_ref = event[f'{author_id}']
    wishlist = rec_ref.get().to_dict()['wishlist']

    user = client.get_user(int(author_id))
    
    await user.send(f'Here is the wishlist: {wishlist}')
    

 

#Fix-Me     
@client.command()
async def randomize(ctx): 
    pairs = {}
    guild_id = ctx.message.guild.id
    author_id = ctx.message.author.id

   
    event_ref = db.collection('events').document(f'{guild_id}')
    event = event_ref.get().to_dict()
    users = event['users']
    host = event['host']

    #host permission
    if author_id != int(host): 
        await ctx.send('Only the host can start random pairings :(')
        return

    #randomize list of users
    random.shuffle(users)

    #pairs users via Hamiltonian Cycle
    for i in range(len(users)): 
        pairs[users[i].id] = users[(i+1)%len(users)]


    event_ref.update(pairs)
    await ctx.send('Everyone has been randomly matched run !recipient in the server to get your recipient:)')


@client.command()
async def recipient(ctx): 
    guild_id = ctx.message.guild.id
    author_id = ctx.message.author.id

    event_ref = db.collection('events').document(f'{guild_id}')
    event = event_ref.get().to_dict()

    rec_ref = event[f'{author_id}']
    rec_name = rec_ref.get().to_dict()['name']

    user = client.get_user(author_id)

    await user.send(f'Your recipient is {rec_name}!!! :santa: ')

client.run('')