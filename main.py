import discord
import json
import time
import datetime
from datetime import timezone
from discord.ext import commands
from web3 import Web3

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Web3 setup
RPC_URL = "https://testnet-rpc.monad.xyz/"  # Update with the correct Monad RPC URL
web3 = Web3(Web3.HTTPProvider(RPC_URL))

MAIN_ADD = "0xeda2077037706d98624E976B6bDf2512d01898f4"  # Replace with your faucet wallet address
MAIN_PK = "12f4a660e1dc74fa1074321c987c781fd9b2141500f7f139f3e95b0c395258d6"  # Replace with your private key (KEEP THIS SAFE!)
EXPLORER = "https://testnet.monadexplorer.com/"

# Function to send transaction
def transfer_eth(from_address, private_key, to_address, amount):
    nonce = web3.eth.get_transaction_count(from_address)
    gas_price = web3.eth.gas_price
    value = web3.to_wei(amount, "ether")

    tx = {
        "nonce": nonce,
        "to": to_address,
        "value": value,
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": 10143,  # Update according to Monad Testnet
    }

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)  # ✅ Fixed AttributeError
    return tx_hash.hex()

@bot.event
async def on_ready():
    print(f"✅ Bot is online! Logged in as {bot.user}")

@bot.tree.command(name="faucet", description="Claim test tokens from the faucet.")
async def faucet(interaction: discord.Interaction, address: str):
    user = interaction.user

    # ✅ Restrict to a specific channel (Update channel ID)
    allowed_channel_id = 1350274580949762189
    if interaction.channel.id != allowed_channel_id:
        await interaction.response.send_message(f"❌ Use this command in <#{allowed_channel_id}>.", ephemeral=True)
        return

    # ✅ Validate address
    if not Web3.is_address(address):
        await interaction.response.send_message("❌ Invalid wallet address.", ephemeral=True)
        return

    # ✅ Role check (Update role name)
    role_name = "Trench Warriors"
    has_role = discord.utils.get(user.roles, name=role_name)
    if not has_role:
        await interaction.response.send_message("❌ You need the 'Trench Warriors' role.", ephemeral=True)
        return

    # ✅ Defer response to prevent timeout
    await interaction.response.defer(ephemeral=True)

    # ✅ Read faucet log
    file_path = "faucet_logs.json"
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    # ✅ Cooldown check (24 hours = 86400 seconds)
    user_id = user.id
    now = int(datetime.datetime.now(timezone.utc).timestamp())  # ✅ Fixed deprecated utcnow()
    user_record = next((entry for entry in data if entry["userId"] == user_id), None)

    if user_record:
        last_faucet_time = user_record["timeFaucet"]
        elapsed_time = now - last_faucet_time

        if elapsed_time < 86400:  # 24-hour cooldown
            remaining_time = 86400 - elapsed_time
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60
            seconds = remaining_time % 60

            if hours > 0:
                time_str = f"{hours} hours"
            elif minutes > 0:
                time_str = f"{minutes} minutes"
            else:
                time_str = f"{seconds} seconds"

            await interaction.followup.send(f"⏳ Try again in {time_str}.", ephemeral=True)
            return

    # ✅ Update logs
    if user_record:
        user_record["timeFaucet"] = now
    else:
        data.append({"userId": user_id, "timeFaucet": now})

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    # ✅ Send transaction
    address = web3.to_checksum_address(address)
    tx_transfer = transfer_eth(MAIN_ADD, MAIN_PK, address, 0.01)

    # ✅ Send success or failure message
    if tx_transfer:
        await interaction.followup.send(f"✅ Faucet success!\n Try again in 24 hours \n Transaction Hash: {EXPLORER}tx/{tx_transfer}")
    else:
        await interaction.followup.send("❌ Transaction failed. Try again later.", ephemeral=True)

# Run bot
TOKEN = "MTM1MjYzNDg4ODk2NDI4MDQzMQ.GEAb9E.n0NJFKyUFVki6-0RPMB2z3FN_R8c3fOqOfmn8E"  # Replace with your bot token
bot.run(TOKEN)
