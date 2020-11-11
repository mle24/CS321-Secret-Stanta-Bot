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
bot = commands.Bot(command_prefix="!", help_command=None)


@bot.event
async def on_command_error(ctx, error):
    """
    Error command handler for commands that are not found
    """
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            colour=discord.Colour.red(),
            description="Command not recognized. Use the !help to list the available commands :smile:",
        )
        await ctx.send(embed=embed)


@bot.command()
async def start(ctx):
    """
    The host starts the event
    """
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection("events").document(f"{guild_id}")
    msg = ""
    # Check if event exists in the events collection
    if not event_ref.get().exists:
        # If the event does not exist, create the event
        event_ref.set({"host": f"{author_id}", "users": [], "pairs": {}})
        msg = "Event has started! :christmas_tree:\n"
    else:
        # Send message if the event is already started
        msg = "Server already has an ongoing event! :christmas_tree:\n"
    # Send message on how the user can join the event
    embed = discord.Embed(
        colour=discord.Colour.red(),
        description=f"{msg} If you would like to participate, use the !join command",
    )
    await ctx.send(embed=embed)

def get_help_message():
    """
        Return an embedded help message that will list the available commands
    """
    # Create am embeded message that contains help commands and how each command works
    description = "Secret Santa is the most convient way to celebrate the holidays with friends and family in your Discord Server."
    embed = discord.Embed(
        title="Commands Menu", colour=discord.Colour.red(), description=f"{description}"
    )
    embed.set_author(
        name="Secret Santa",
        icon_url="https://httpsimage.com/v2/410ead26-e041-499f-8b4d-ddbfce568350.png",
    )
    embed.add_field(name="!start", value="Start an Event", inline=False)
    embed.add_field(name="!join", value="Join the event", inline=False)
    embed.add_field(name="!pair", value="Randomly pair participants", inline=False)
    embed.add_field(name="!add ITEM_NAME", value="Add item to your wishlist", inline=False)
    embed.add_field(name="!remove ITEM_NUMBER", value="Remove item from your wishlist", inline=False)
    embed.add_field(name="!my_wishlist", value="Get your wishlist", inline=False)
    embed.add_field(name="!wishlist", value="Get your recipient's wishlist", inline=False)
    return embed

@bot.command()
async def help(ctx):
    """
    Custom Commands Menu by calling get_help_message
    """
    # Get help message and send to user
    embed = get_help_message()
    await ctx.send(embed=embed)


@bot.command()
async def join(ctx):
    """
    User joins the even if not already participating
    """
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection("events").document(f"{guild_id}")
    user_ref = db.collection("users").document(f"{author_id}")
    # Make sure an event is in progress
    if not event_ref.get().exists:
        await ctx.send("No event in progress, ask the event host to start one! :smile:")
        return
    # Get the user who is joining the event
    user = bot.get_user(author_id)
    # Check if user exists in our database of users
    if not user_ref.get().exists:
        # If they don't exist, set their information in the database
        user_ref.set(
            {
                "name": f"{user.name}#{user.discriminator}",
                "wishlist": [],
                "events": [],
            }
        )
    # If the event we are joining already exists in the users event list, send them a message
    if event_ref in user_ref.get().to_dict()["events"]:
        await ctx.send("You have already joined the event! :smile:")
    # If the user is not part of the event we are joining, add it to their event list and
    # add the user to the servers event list.
    else:
        event_ref.update({"users": firestore.ArrayUnion([user_ref])})
        user_ref.update({"events": firestore.ArrayUnion([event_ref])})
        embed = discord.Embed(
            colour=discord.Colour.red(),
            description=f"{ctx.message.author} has been added to the event! :partying_face:",
        )
        await ctx.send(embed=embed)
        await user.send(embed=get_help_message())
        await user.send("Use this channel to add/remove items from your wishlist\nUse this channel to also get items from your with the !my_wishlist :smile:")


@bot.command()
async def add(ctx, *args):
    """
    Add item into wishlist
    """
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection("users").document(f"{author_id}")
    # Create item to be added into wishlist
    item = " ".join(args)
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send("You are not part of an event! Join one before adding items to your wishlist :smile:")
        return
    # User is not part of any event throughout Discord
    if len(user_ref.get().to_dict()["events"]) == 0:
        await ctx.send("You are not part of an event! Join one before adding items to your wishlist :smile:")
        return
    # Alert user that their item can be seen in public
    user = bot.get_user(author_id)
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await user.send("Others can see the items you add to your wishlist in a public channel! Be careful! :smile:")
    # Update user refernece with the new array of items
    user_ref.update({"wishlist": firestore.ArrayUnion([f"{item}"])})
    user = bot.get_user(author_id)
    embed = discord.Embed(
        colour=discord.Colour.red(),
        description=f"I have added {item} to your wishlist :upside_down:",
    )
    await user.send(embed=embed)


@bot.command()
async def remove(ctx, index_to_remove):
    """
    Remove item from wishlist
    """
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection("users").document(f"{author_id}")
    # Store the index after parsing argument
    index = 0
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send("You are not part of an event! Join one before removing items from your wishlist :smile:")
        return
    # User is not part of any event throughout Discord
    if len(user_ref.get().to_dict()["events"]) == 0:
        await ctx.send("You are not part of an event! Join one before removing items from your wishlist :smile:")
        return
    # Get user's wishlist
    user_wishlist = user_ref.get().to_dict()["wishlist"]
    # Try to parse the index passed in as an integer
    try:
        index = int(index_to_remove)
    # If an error occurs when parsing, send an error message
    except ValueError:
        await ctx.send("To remove: !remove <item number>\nItem number can be found above each item using !my_wishlist :smile:")
        return
    # Send an error if the integer is out of bounds
    if index > len(user_wishlist):
        await ctx.send("Invalid Item Number\nItem number can be found above each item using !my_wishlist :smile:")
        return
    # Alert user that their item can be seen in public
    user = bot.get_user(author_id)
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await user.send("Others can see the items you remove from your wishlist in a public channel! Be careful! :smile:")
    # Update user refernece and delete specified item
    item = user_wishlist[index - 1]
    del user_wishlist[index - 1]
    user_ref.update({"wishlist": user_wishlist})
    embed = discord.Embed(
        colour=discord.Colour.red(),
        description=f"I have deleted {item} from your wishlist :upside_down:",
    )
    await user.send(embed=embed)


@bot.command()
async def my_wishlist(ctx):
    """
    Retrieve your wishlist
    """
    # Get references to the user
    author_id = ctx.message.author.id
    user_ref = db.collection("users").document(f"{author_id}")
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send("You are not part of an event! Join one before viewing items in your wishlist :smile:")
        return
    # User is not part of any event throughout Discord
    user_dict = user_ref.get().to_dict()
    if len(user_dict["events"]) == 0:
        await ctx.send("You are not part of an event! Join one before viewing items in your wishlist :smile:")
        return
    # Retrieve the user's wishlist
    user = bot.get_user(int(author_id))
    wishlist = user_dict["wishlist"]
    embed = discord.Embed(title="Your Wishlist", colour=discord.Colour.red())
    for i in range(len(wishlist)):
        embed.add_field(name=f"Item {i+1}", value=f"{wishlist[i]}", inline=False)
    await user.send(embed=embed)


@bot.command()
async def wishlist(ctx):
    """
    Retrieve Recipient Wishlist
    """
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    user_ref = db.collection("users").document(f"{author_id}")
    event_ref = db.collection("events").document(f"{guild_id}")
    # Make sure an event is in progress
    if not event_ref.get().exists:
        await ctx.send("No event in progress, ask the event host to start one! :smile:")
        return
    event_dict = event_ref.get().to_dict()
    # Make sure the user exists
    if not user_ref.get().exists:
        await ctx.send("You are not part of an event! Join one before viewing items in your wishlist :smile:")
        return
    # User is not part of any event throughout Discord
    user_dict = user_ref.get().to_dict()
    if len(user_dict["events"]) == 0:
        await ctx.send("You are not part of an event! Join one before viewing items in your wishlist :smile:")
        return
    # Check if the user has already been paired
    if len(event_dict["pairs"]) == 0:
        await ctx.send("You have not been paired yet! Ask the host to start the pairing :smile:")
        return
    # Retrieve the user's recipient wishlist
    user = bot.get_user(int(author_id))
    recipient = event_dict[f"pairs"][f"{author_id}"].get().to_dict()
    recipient_wishlist = recipient["wishlist"]
    embed = discord.Embed(title=f"{recipient['name']}'s Wishlist", colour=discord.Colour.red())
    for i in range(len(recipient_wishlist)):
        embed.add_field(name=f"Item {i+1}", value=f"{recipient_wishlist[i]}", inline=False)
    await user.send(embed=embed)


@bot.command()
async def pair(ctx):
    """
    Randomly pair users with each other
    """
    # Make sure this command is run on a server
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("This command can only be run in a server! :smile:")
        return
    # Get references to the user and the server they are on
    author_id = ctx.message.author.id
    guild_id = ctx.message.guild.id
    event_ref = db.collection("events").document(f"{guild_id}")
    pairs = {}
    # Make sure an event is in progress
    if not event_ref.get().exists:
        await ctx.send("No event in progress, ask the event host to start one! :smile:")
        return
    event = event_ref.get().to_dict()
    users = event["users"]
    # Make sure host is the only one calling this command
    if author_id != int(event["host"]):
        host = bot.get_user(int(event["host"]))
        await ctx.send(f"Only the event host can run this command. Ask {host.name}#{host.discriminator}! :smile:")
        return
    # Make sure there are users present in the event
    if len(users) == 0:
        await ctx.send("No users have joined the event! Ask them to join with the !join command :smile:")
        return
    # Randomize list of users
    random.shuffle(users)
    # Pairs users via Hamiltonian Cycle
    for i in range(len(users)):
        pairs[users[i].id] = users[(i + 1) % len(users)]
    # Update database
    event_ref.update({"pairs": pairs})
    # Loop through all the pairs and send them a message with who their pair is
    for key, value in pairs.items():
        user = bot.get_user(int(key))
        recipient = value.get().to_dict()["name"]
        wishlist = value.get().to_dict()["wishlist"]
        embed = discord.Embed(
            title=f"{recipient}'s Wishlist", colour=discord.Colour.red()
        )
        for i in range(len(wishlist)):
            embed.add_field(name=f"Item {i+1}", value=f"{wishlist[i]}", inline=False)
        await user.send(f"Your recipient is {recipient}!!! :santa:")
        await user.send(embed=embed)
    # Send a message to the guild stating that everyone has been paired
    embed = discord.Embed(
        colour=discord.Colour.red(),
        description="Everyone who joined the event has been randomly paired! Check your direct messages to see who you are paired with. :smile:",
    )
    await ctx.send(embed=embed)


bot.run("NzY1MzgxOTA3MTM5MTMzNTIw.X4T_cg.M6zHSd6aDLa0MU79Px8Zmp8VZ58")
