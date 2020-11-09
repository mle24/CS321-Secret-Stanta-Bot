import firebase_admin
from firebase_admin import credentials, firestore
import discord
from discord.ext import commands
import datetime
import random

# Initialize credentials for bot to access database
cred = credentials.Certificate("./botprivatekey.json")
firebase_admin.initialize_app(cred)
# Initialize database client and discord bot
db = firestore.client()
bot = commands.Bot(command_prefix='!')


@bot.command()
async def start(ctx):
    '''
        The host starts the event
    '''
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection('events').document(f'{guild_id}')
    # Check if event exists in the events collection
    if not event_ref.get().exists:
        # If the event does not exist, create the event
        event_ref.set({
            'host': f'{author_id}',
            'users': []
        })
        await ctx.send('Event has started! :christmas_tree:')
    else:
        # Send message if the event is already started
        await ctx.send('Server already has an ongoing event! :christmas_tree:')
    # Send message on how the user can join the event
    await ctx.send('If you would like to participate, use the !join command')


@bot.command()
async def join(ctx):
    '''
        User joins the even if not already participating
    '''
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection('events').document(f'{guild_id}')
    user_ref = db.collection('users').document(f'{author_id}')
    # Make sure an event is in progress
    if not event_ref.get().exists:
        await ctx.send('No event in progress, ask the event host to start one! :smile:')
        return
    # Get the user who is joining the event
    user = bot.get_user(author_id)
    # Check if user exists in our database of users
    if not user_ref.get().exists:
        # If they don't exist, set their information in the database
        user_ref.set({
            'name': f'{user.name}#{user.discriminator}',
            'wishlist': [],
            'events': [],
        })
    # If the event we are joining already exists in the users event list, send them a message
    if event_ref in user_ref.get().to_dict()['events']:
        await ctx.send('You have already joined the event! :smile:')
    # If the user is not part of the event we are joining, add it to their event list and
    # add the user to the servers event list.
    else:
        event_ref.update({'users': firestore.ArrayUnion([user_ref])})
        user_ref.update({'events': firestore.ArrayUnion([event_ref])})
        await ctx.send(f'{ctx.message.author} has been added to the event! :partying_face:')
        await user.send("Use this channel to add and remove items from your wishlist")


@bot.command()
async def add(ctx, *args):
    '''
        Add item into wishlist
    '''
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection('users').document(f'{author_id}')
    # Create item to be added into wishlist
    item = " ".join(args)
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send('You are not part of an event! Join one before adding items to your wishlist :smile:')
        return
    # User is not part of any event throughout Discord
    if len(user_ref.get().to_dict()['events']) == 0:
        await ctx.send('You are not part of an event! Join one before adding items to your wishlist :smile:')
        return
    # Alert user that their item can be seen in public
    user = bot.get_user(author_id)
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await user.send("Others can see the items you add to your wishlist in a public channel! Be careful! :smile:")
    # Update user refernece with the new array of items
    user_ref.update({'wishlist': firestore.ArrayUnion([f'{item}'])})
    user = bot.get_user(author_id)
    await user.send(f"I have added {item} to your wishlist :upside_down:")


@bot.command()
async def remove(ctx, *args):
    '''
        Remove item from wishlist
    '''
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection('users').document(f'{author_id}')
    # Create item to be added into wishlist
    item = " ".join(args)
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send('You are not part of an event! Join one before removing items from your wishlist :smile:')
        return
    # User is not part of any event throughout Discord
    if len(user_ref.get().to_dict()['events']) == 0:
        await ctx.send('You are not part of an event! Join one before removing items from your wishlist :smile:')
        return
    # Alert user that their item can be seen in public
    user = bot.get_user(author_id)
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await user.send("Others can see the items you remove from your wishlist in a public channel! Be careful! :smile:")
    # Update user refernece and delete specified item
    user_ref.update({'wishlist': firestore.ArrayRemove([f'{item}'])})
    user = bot.get_user(author_id)
    await user.send(f"I have deleted {item} from your wishlist :upside_down:")


@bot.command()
async def wishlist(ctx):
    '''
        Retrieve your wishlist
    '''
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection('users').document(f'{author_id}')
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send('You are not part of an event! Join one before viewing items in your wishlist :smile:')
        return
    # User is not part of any event throughout Discord
    if len(user_ref.get().to_dict()['events']) == 0:
        await ctx.send('You are not part of an event! Join one before viewing items in your wishlist :smile:')
        return
    user = bot.get_user(int(author_id))
    wishlist = user_ref.get().to_dict()['wishlist']
    await user.send(f'Here is your wishlist: {wishlist}')


@bot.command()
async def pair(ctx):
    '''
        Randomly pair users with each other
    '''
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Create empty dictionary for pairs
    pairs = {}
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection('events').document(f'{guild_id}')
    # Make sure an event is in progress
    if not event_ref.get().exists:
        await ctx.send('No event in progress, ask the event host to start one! :smile:')
        return
    event = event_ref.get().to_dict()
    users = event['users']
    # Make sure host is the only one calling this command
    if author_id != int(event['host']):
        host = bot.get_user(int(event['host']))
        await ctx.send(f'Only the event host can run this command. Ask {host.name}#{host.discriminator}! :smile:')
        return
    # Make sure there are users present in the event
    if len(users) == 0:
        await ctx.send('No users have joined the event! Ask them to join with the !join command :smile:')
        return
    # Randomize list of users
    random.shuffle(users)
    # Pairs users via Hamiltonian Cycle
    for i in range(len(users)):
        pairs[users[i].id] = users[(i+1) % len(users)]
    # Update database
    event_ref.update({"pairs": pairs})
    # Loop through all the pairs and send them a message with who their pair is
    for key, value in pairs.items():
        user = bot.get_user(int(key))
        recipient = value.get().to_dict()['name']
        recipient_wishlist = value.get().to_dict()['wishlist']
        await user.send(f'Your recipient is {recipient}!!! :santa:\nHere is their wishlist: {recipient_wishlist} :smile:')
    # Send a message to the guild stating that everyone has been paired
    await ctx.send('Everyone who joined the event has been randomly paired! Check your direct messages to see who you are paired with. :smile:')


bot.run('')
