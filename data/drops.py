import discord, asyncio, string, random, yaml
from discord.ext import commands

import enum

with open('./data/config.yml', 'r') as f:
    _config = yaml.load(f)

### Config Bullshit ###
dropRewards = (
    _config['drop-reward-min'],
    _config['drop-reward-max']
)
#######################


class dropDifficulty(enum.Enum):
    easy = 0
    medium = 1
    hard = 2

class dropResponse():
    def __init__(self, typethis, reward, *, embed_desc : str = None, embed_image : str = None, hide_answer : bool = False):
        self.typethis = typethis
        self.reward = reward
        self.embed_desc = embed_desc if not None else "Solve the following"
        self.embed_image = embed_image

        self.hide_answer = hide_answer

    def solves(self, msg : discord.Message):
        return self.typethis.lower() in msg.content.lower()

def _util_get_difficulty():
    d = random.choice(
        population=[
            dropDifficulty.easy,
            dropDifficulty.medium,
            dropDifficulty.hard
        ],
        weights=[
            0.6, # 60% Chance for Easy 
            0.25, # 25% Chance for Medium
            0.15 # 15% Chance for Hard
        ]
    )
    return d

async def type_drop(channel : discord.TextChannel, strength : dropDifficulty = None, *args, **kwargs):
    if strength is None: strength = _util_get_difficulty()
    if strength.value == 0: # Easy
        dR = dropResponse(
            "".join(random.choice(string.ascii_lowercase) for i in range(random.randint(4, 8))), # 4->8 Random Letters
            reward = random.randint(**dropRewards),
            embed_desc="Type the following phrase"
        )
    elif strength.value == 1: # Medium
        dR = dropResponse(
            "".join(random.choice(string.ascii_lowercase + string.digits) for i in range(random.randint(6, 10))), # 4->8 Random Letters
            reward = random.randint(**dropRewards) * 1.5,
            embed_desc="Type the following phrase"
        )
    elif strength.value == 2: # Hard
        dR = dropResponse(
            "".join(random.choice(string.ascii_lowercase + string.digits) for i in range(random.randint(10, 14))), # 4->8 Random Letters
            reward = random.randint(**dropRewards) * 2,
            embed_desc="Type the following phrase"
        )
    return dR