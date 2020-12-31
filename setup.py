import os
from dotenv import load_dotenv

DISCORD_TOKEN = input('Enter bot\'s discord token:')
print(f"token entered was '{DISCORD_TOKEN}'")
DISCORD_GUILD = input('Enter your server\'s name here:')
print(f"Server name entered was '{DISCORD_GUILD}'")
CREATOR = input('Enter the creator\'s name and tag (e.g name#1234):')
print(f"Creator name entered was '{CREATOR}'")
DATA_PATH= input('Enter path to the directory the bot files will be:')
print(f"Path entered was {DATA_PATH}")

if os.path.exists(DATA_PATH + "\.env"):
  os.remove(DATA_PATH + "\.env")
env = open(DATA_PATH + "\.env", 'w')

env.write('# .env\n')
env.write(f"DISCORD_TOKEN='{DISCORD_TOKEN}'\n")
env.write(f"DISCORD_GUILD={DISCORD_GUILD}\n")
env.write(f"CREATOR='{CREATOR}'")
env.write(f"DATA_PATH={DATA_PATH}\n")
env.close()
