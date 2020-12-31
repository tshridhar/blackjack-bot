# blackjackbot.py

# Import statements
# must install discord, dotenv, json if not there
import os
import discord
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from random import shuffle

"""
    Threading not implemented, currently not locking access to the 'sessions' dictionary.
    Default Python serialization is in effect.
"""

#------------------------------------------------------------------#
# Load all environment variables from the .env file, which can be
#      created with setup.py
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DATA_PATH = os.getenv('DATA_PATH') + "\database.txt"
CREATOR = os.getenv('CREATOR')

#------------------------------------------------------------------#
# Global variable / Database setup
client = discord.Client()
data = {}

# Assumes there is a file in DATA_PATH called 'database.txt'
with open(DATA_PATH, 'r') as file:
    data = json.load(file)
print(data)

cards = {"A" : 1, "2" : 2, "3" : 3, "4" : 4, "5" : 5, "6" : 6, "7" : 7, "8" : 8, "9" : 9, "10" : 10, "J" : 10, "Q" : 10, "K" : 10}
sessions = {}
deck = []

#------------------------------------------------------------------#
@client.event
async def on_ready():
    guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)
    print(
        f'{client.user} is connected to the Discord!\n',
        f' server: {guild.name} \n  id: {guild.id}')

#------------------------------------------------------------------#
# *****This function can be streamlined more... TODO For future build
def genEmbed(type, title, desc, msg="", color=discord.Color.blurple(), player=None):
    global sessions
    embed = discord.Embed(
                        title = title,
                        description = desc,
                        color = color
                        )
    if type == "create":
        embed.add_field(name='\U0001F4B0 Balance \U0001F4B0', value="2000", inline=False)
        embed.set_footer(text='Type !help or !assist if you\'re lost!')
    elif type == 'play' or type == "win" or type == "lose":
        field_name = {'play' : 'Bet Amount', 'win' : 'Amount Won', 'lose' : 'Amount Lost'}
        footer = {'play' : '!hit or !stand', 'win' : 'Blackjack prodigy!', 'lose' : 'Better luck next time!'}
        embed.add_field(name=field_name[type], value=f":coin: {sessions[player]['bet']} :coin:", inline=False)
        embed.add_field(name='Balance', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Player Hand', value=f"{' - '.join([i for i in sessions[player]['player_hand']])}", inline=True)
        embed.add_field(name=' :black_large_square:', value=' :black_large_square:', inline=True)
        dealer_hand = f"{sessions[player]['dealer_hand'][0]} - \U0001F0CF" if type == 'play' else f"{' - '.join([i for i in sessions[player]['dealer_hand']])}"
        embed.add_field(name='Dealer Hand', value=dealer_hand, inline=True)
        embed.set_footer(text=footer[type])
    elif type == "tie":
        embed.add_field(name='Balance', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Player Hand', value=f"{' - '.join([i for i in sessions[player]['player_hand']])}", inline=True)
        embed.add_field(name=' :black_large_square:', value=' :black_large_square:', inline=True)
        embed.add_field(name='Dealer Hand', value=f"{' - '.join([i for i in sessions[player]['dealer_hand']])}", inline=True)
        embed.set_footer(text='Bet again!')
    elif type == "stats":
        embed.add_field(name='Balance', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.add_field(name='Wins', value=f"{data[player]['wins']}", inline=True)
        embed.add_field(name='Losses', value=f"{data[player]['losses']}", inline=True)
        embed.add_field(name='Ties', value=f"{data[player]['ties']}", inline=True)
        embed.add_field(name='Rank', value=f"Not yet implemented", inline=False)
        embed.set_footer(text='!help or !assist if you\'re lost')
    elif type == "leaderboard":
        leaderboard = sorted([(k, v['balance'], v['wins']) for k,v in data.items()], key=(lambda x: (x[1],x[2])), reverse=True)
        if len(leaderboard) > 4:
            leaderboard = leaderboard[0:4]
        for i, v in enumerate(leaderboard):
            emoji = {0 : ':first_place:', 1 : ':second_place:', 2: ':third_place:'}
            i = emoji[i] if i in emoji else f"#{i+1}"
            embed.add_field(name=f"{i} :  {v[0][:-5]}", value=f"{v[1]}", inline=False)
        embed.set_footer(text='!help or !assist if you\'re lost')
    elif type == 'job':
        embed.add_field(name='New Balance', value=f"\U0001F4B0 {data[player]['balance']} \U0001F4B0", inline=False)
        embed.set_footer(text='!help or !assist if you\'re lost')
    return embed

#------------------------------------------------------------------#
# Generates a standard blackjack deck. Consists of 6 packs of 52 ct cards, shuffled.
def genDeck():
    deck = []
    # Generate a deck of 6 packs
    for _ in range(6):
        pack = []
        # Generate each pack
        for i in range(4):
            pack += cards.keys()
            shuffle(pack)
        deck += pack
        shuffle(deck)
    return deck

#------------------------------------------------------------------#\
# Calculates the value of a hand according to Blackjack rules
def sumHand(hand):
    hand_sum = 0
    aces = 0
    for i in hand:
        if i != 'A':
            hand_sum += cards[i]
        else:
            aces += 1
    # Handle aces
    for i in range(aces):
        if hand_sum + 11 <= 21:
            hand_sum += 11
        else:
            hand_sum += 1
    return hand_sum

#------------------------------------------------------------------#
@client.event
async def on_message(message):
    #------------------------------------------------------------------#
    global sessions
    global deck
    channel = message.channel
    player = message.author
    
    #------------------------------------------------------------------#
    # Check if message was sent in the "blackjack" channel, or if the sender
    #    is the bot
    if "blackjack" not in channel.name or player == client.user:
        return
    #------------------------------------------------------------------#
    # Player name and message parsing setup
    name = f'{player}'
    msg = message.content if message.content.startswith('!gift') or message.content.startswith('!give') else message.content.lower()
    
    #------------------------------------------------------------------#
    if msg == '!help':
        embed = discord.Embed(title='List of Commands', desc='-', color=discord.Color.gold())
        embed.add_field(name='!play | !bet', value='!play <token amount>', inline=False)
        embed.add_field(name='!hit | !stand', value='!hit - be dealt another card\n!stand - lock in your hand', inline=False)

        # Separate !bal and !stats eventually
        embed.add_field(name='!bal | !stats | !balance', value='Shows player profile with current balance, W/L/T, and rank', inline=False)
        
        embed.add_field(name='!top | !leaderboard', value='Displays the top 4 players', inline=False)
        embed.add_field(name='!job | !collect', value='Adds 200 tokens to your account. Can only be claimed once per hour', inline=False)
        await channel.send(f"{player.mention}", embed=embed)
        return
    #------------------------------------------------------------------#
    elif msg.startswith('!') and name not in data and msg != '!create':
        await channel.send('Please create a blackjack account with "!create"')

    #------------------------------------------------------------------#
    elif msg == '!hit':
        if name in sessions:
            sessions[name]['player_hand'].append(deck.pop())
            dealer_hand = sumHand(sessions[name]['dealer_hand'])
            player_hand = sumHand(sessions[name]['player_hand'])
            if player_hand > 21:
                data[name]['balance'] -= sessions[name]['bet']
                data[name]['losses'] += 1
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("lose", 'LOSS', 'You lost!!!', color=discord.Color.red(), player=name))
                del sessions[name]

            elif player_hand == 21:
                while sumHand(sessions[name]['dealer_hand']) < 17:
                    sessions[name]['dealer_hand'].append(deck.pop())
                if sumHand(sessions[name]['dealer_hand']) == 21:
                    data[name]['ties'] += 1
                    await channel.send(f"{player.mention}", embed=genEmbed("tie", 'TIE!', 'Nobody wins. All bets returned.', player=name))
                else:
                    data[name]['wins'] += 1
                    data[name]['balance'] += sessions[name]['bet']
                    json.dump(data, open(DATA_PATH, 'w'))
                    await channel.send(f"{player.mention}", embed=genEmbed("win", ':tada: WIN!!! :tada:', 'You win!', color=discord.Color.green(), player=name))
                del sessions[name]
            
            else:
                await channel.send(f"{player.mention}", embed=genEmbed("play", 'Blackjack', 'Round Continued!', color=discord.Color.blue(), player=name))
        else:
            await channel.send(f"{player.mention} not currently in a game!")

    #------------------------------------------------------------------#
    elif msg == '!stand':
        if name in sessions:
            player_hand = sumHand(sessions[name]['player_hand'])
            while sumHand(sessions[name]['dealer_hand']) < 17:
                sessions[name]['dealer_hand'].append(deck.pop())
            dealer_hand = sumHand(sessions[name]['dealer_hand'])
            if (player_hand > dealer_hand and player_hand <= 21) or dealer_hand > 21:
                data[name]['wins'] += 1
                data[name]['balance'] += sessions[name]['bet']
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("win", ':tada: WIN!!! :tada:', 'You win!', color=discord.Color.green(), player=name))
            elif player_hand < dealer_hand and dealer_hand <= 21:
                data[name]['losses'] += 1
                data[name]['balance'] -= sessions[name]['bet']
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("lose", 'LOSS', 'You lost!!!', color=discord.Color.red(), player=name))
            else:
                data[name]['ties'] += 1
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("tie", 'TIE!', 'Nobody wins. All bets returned.', player=name))
            del sessions[name]
        else:
            await channel.send(f"{player.mention} not currently in a game!")

    elif msg in ('!bal', '!balance', '!stats'):
        await channel.send(f"{player.mention}", embed=genEmbed("stats", 'Your Profile', 'All stats.', player=name))
    
    #------------------------------------------------------------------#
    elif msg.startswith('!bet') or msg.startswith('!play'):
        # Verify session does not already exist
        if name not in sessions:
            # Verify proper command format: !bet <integer amount>
            if len(msg.split(' ')) == 2 and msg.split(' ')[1].isdigit():
                bet = int(msg.split(' ')[1])
                # Verify bet amount is legal: bet <= player balance and > 0
                if bet <= data[name]['balance'] and bet > 0:
                    sessions[name] = {"bet": bet, "player_hand": [], "dealer_hand": []}
                    if len(deck) < 75:
                        deck = genDeck()
                        print("Deck was shuffled.")
                    for _ in range(2):
                        sessions[name]['player_hand'].append(deck.pop())
                        sessions[name]['dealer_hand'].append(deck.pop())
                    dealer_hand = sumHand(sessions[name]['dealer_hand'])
                    player_hand = sumHand(sessions[name]['player_hand'])
                    
                    if player_hand == 21 and dealer_hand != 21:
                        # Payout player bet * 1.5 and add to balance. Increment Player win, Increment dealer loss.
                        data[name]['balance'] += int(sessions[name]['bet'] * 1.5)
                        sessions[name]['bet'] = int(sessions[name]['bet'] * 1.5)
                        data[name]['wins'] += 1
                        json.dump(data, open(DATA_PATH, 'w'))
                        await channel.send(f"{player.mention}", embed=genEmbed("win", ':tada: :tada: WIN!!! :tada: :tada:', 'Natural! You win!', color=discord.Color.green(), player=name))
                        del sessions[name]

                    # Return player bet and do not change balance. Increment Player tie, Increment Dealer tie.
                    elif dealer_hand == 21 and dealer_hand == player_hand:
                        data[name]['ties'] += 1
                        json.dump(data, open(DATA_PATH, 'w'))
                        await channel.send(f"{player.mention}", embed=genEmbed("tie", 'TIE!', 'Nobody wins. All bets returned.', player=name))
                        del sessions[name]

                    else:
                        await channel.send(f"{player.mention}", embed=genEmbed("play", 'Blackjack', 'Round Started!', color=discord.Color.blue(), player=name))
                else:
                    await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', f"You don't have {bet} tokens to bet!", color=discord.Color.orange()))
            else:
                await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', 'Correct use is\n!bet <tokens>  OR !play <tokens>', color=discord.Color.orange()))
        else:
            await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', 'Currently in a game!', color=discord.Color.orange()))
    
    #------------------------------------------------------------------#
    elif msg.startswith('!job') or msg.startswith('!collect'):
        lastjob = datetime.strptime(data[name]['lastjob'], "%Y-%m-%d %H:%M:%S")
        if lastjob <= datetime.utcnow()-timedelta(hours=1):
            # modify user
            data[name]['lastjob'] = f'{datetime.utcnow()}'.split('.')[0]
            data[name]['balance'] += 200
            json.dump(data, open(DATA_PATH, 'w'))
            await channel.send(f"{player.mention}", embed=genEmbed("job", 'Paycheck Time!', 'You received 200 tokens', color=discord.Color.green(), player=name))
        else:
            # error
            time_to_next_job = str((lastjob+timedelta(hours=1))-datetime.strptime(f'{datetime.utcnow()}'.split('.')[0], "%Y-%m-%d %H:%M:%S")).split(':')
            await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', f'Can only !job once every hour!\nNext paycheck in:\n{time_to_next_job[-2]} min {time_to_next_job[-1]} sec', color=discord.Color.orange()))
    
    #------------------------------------------------------------------#
    elif msg == '!leaderboard' or msg == '!top':
        if len(data.keys()) == 0:
            await channel.send(f"{player.mention}\nLeaderboard is currently empty.")
        line = '----------------------------------'
        await channel.send(f"{player.mention}", embed=genEmbed("leaderboard", ":chart_with_upwards_trend: :medal: Leaderboard :medal: :chart_with_upwards_trend:", f'{line}', color=discord.Color.purple()))
    
    #------------------------------------------------------------------#
    elif msg.startswith('!give') or msg.startswith('!gift'):
        """ 
        Gift/Give command. Usage: !give <player> <token amount> or !gift <player> <token amount>
            Constraints:
                Cannot gift more than current balance
                Cannot gift if currently in a game
                Must gift to someone currently in the database
        """
        if name in sessions.keys():
            await channel.send(f"{player.mention}", embed=genEmbed('error', 'Error!', "Can't gift while you are in a game!", color=discord.Color.orange()))
            return
        split_msg = msg.split(' ')
        amount = int(split_msg[2]) if len(split_msg) == 3 and split_msg[2].isdigit() else 0
        if len(split_msg) == 3 and split_msg[1] in data.keys() and (amount > 0 and data[name]['balance']-amount >= 0):
            data[name]['balance'] -= amount
            data[split_msg[1]]['balance'] += amount
            embed = discord.Embed(title=':confetti_ball::gift: Gift! :gift::confetti_ball:', description=f"{name[:-5]} gave {split_msg[1][:-5]} {amount} tokens!", color=discord.Color.dark_grey())
            await channel.send(f"{player.mention} gifts {split_msg[1][:-5]}", embed=embed)
        else:
            await channel.send(f"{player.mention}", embed=genEmbed('error', 'Error!', 'Correct command is !gift <user#tag> <valid amount>', color=discord.Color.orange()))

    elif msg == '!create':
        if name in data:
            await channel.send(f"{player.mention}", embed=genEmbed("error", 'Error!', 'Account already created!', color=discord.Color.orange()))
        else:
            data[name] = {'balance' : 2000, 'lastjob': f'{datetime.utcnow()}'.split('.')[0], 'wins' : 0, 'losses' : 0, 'ties' : 0}
            json.dump(data, open(DATA_PATH, 'w'))
            await channel.send(f"{player.mention}", embed=genEmbed("create", '\U00002660 Blackjack \U00002660', 'Account creation success!'))
    
    elif msg.startswith('!rigged'):
        await channel.send('Sue me.')

    # ==== DEBUGGING / CREATOR CONTROLS ==== #
    elif (msg == '!cheats' or msg == '!hacks') and name == CREATOR:
        if len(msg.split(' ')) == 2 and msg.split(' ')[1].isdigit():
            bet = int(msg.split(' ')[1])
            if bet <= 100000:
                data[name]['balance'] += bet
                json.dump(data, open(DATA_PATH, 'w'))
                await channel.send(f"{player.mention}", embed=genEmbed("job", 'Here you go creator!', f'You received {bet} tokens', color=discord.Color.green(), player=name))

    elif msg == '!quit' and name == CREATOR:
        del sessions[name]

    elif msg == '!next' and name == CREATOR:
        await channel.send(f"{player.mention} The next 2 cards are {deck[-1]} and {deck[-2]}")

    elif msg.startswith('!disconnect') and name == CREATOR:
        sessions.clear()
        json.dump(data, open(DATA_PATH, 'w'))
        await client.close()
    
    elif msg.startswith('!deleteacc') and name == CREATOR:
        await channel.send('f"{player.mention}, your account has been deleted."')
        data.pop(name)
    return

client.run(TOKEN)

