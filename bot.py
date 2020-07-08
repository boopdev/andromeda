import asyncio, discord, asyncpg, datetime, logging, pyfiglet, yaml
from discord.ext import commands

# Pretty things
from rich.logging import RichHandler
from rich.traceback import install

# Logging Information
logging.basicConfig(
    level=logging.WARN,
    handlers=[RichHandler()], # Disable this if console lags
    format = "%(message)s",
    datefmt="[%X] "
)

# Better Traceback Handler
install()

__config__ = {
    'c' : "config.yml", # Config.yml
    'm' : 'modranks.yml' # Modranks.yml
    }

async def start_andromeda():

    # Uses a postgres server
    credentials = {
        "user" : "user", # PGsql Username
        "password" : "password", # PGsql Password
        "database" : "andromeda", # PGsql Database name
        "host" : "0.0.0.0" # Server IP
    }
    db = await asyncpg.create_pool(**credentials)
    del credentials # Delete these because we dont want people to be able to get their hands on them

    data = open('andromeda-1.0.sql', 'r').read()

    if data is not None and len(data) >= 1:
        await db.execute(data)

    client = Andromeda(db=db)

    for cog in client.autoload_cogs:
        try:
            client.load_extension(f'cogs.{cog}')
        except Exception as error:
            client.logger.critical(f'Failed to load cog "{cog}" due to: {error}')
            raise error
        else:
            client.logger.warn(f'Loaded cog {cog}')

    try:
        await client.start("da bot token") # You should know what goes here
    except KeyboardInterrupt:
        await client.clean_kill()
    except Exception as err:
        raise Exception

class Andromeda(commands.Bot):
    def __init__(self, **kwargs):

        self._read_yamls() # Sets key attributes to the bot object, dont move this retard

        super().__init__(
            command_prefix=self._config['bot-prefix'],
            owner_ids=[
                104660856658210816 # boop id, replace with your own fuckhead
            ],
            case_insensitive=True,
            activity=discord.Streaming(
                name = "Andromeda 💜",
                url="https://twitch.tv/wendys"
            )
            #,status=discord.Status.invisible
        )

        self.db = kwargs.pop('db')
        self.logger = logging

        # these are autoloaded
        self.autoload_cogs = [
            'dev',
            'error',
            'help',
            'settings'
        ]

        self.modranks = self.get_modranks()


        @self.event
        async def on_ready():
            self.logger.warn("Andromeda is running!")

    def _read_yamls(self):
        with open(f"./data/{__config__['c']}", 'r') as f:
            self._config = yaml.load(f)

        with open('./data/colours.yml', 'r') as f:
            self._colours = yaml.load(f)


    class ModRankObj():
        def __init__(self, cli, name, stuff):
            self.__client = cli
            self.name = name
            self.__stuff = stuff

            self.id = self.__stuff['id']
            self.inherit_tags = self.__stuff.get('inherit', [])

        def __str__(self): return self.name.title()

        @property
        def inherits(self):
            return [self.__client.get_modrank(x) for x in self.inherit_tags if x != '*']

    def get_modranks(self):
        with open(f"./data/{__config__['m']}", 'rb') as f:
            _raw_data = yaml.load(f)
        return [
            self.ModRankObj(self, list(i.keys())[0], i) for i in _raw_data
        ]

    def get_modrank(self, query):
        qu = list(filter(lambda z: z.name.lower() == query.lower(), self.modranks))
        if len(qu) >= 1: return qu[0]
        else: return None

    @property
    def scarlyst(self):
        return self.get_guild(self._config['scarlyst-id']) # Scarlyst ID: 448571905524498432

    # Closes database n shit
    async def clean_kill(self):
        await self.db.close()
        await self.logout()

    def reload_cog(self, cogname : str, *, context : commands.Context = None):
        try:
            self.reload_extension(f'cogs.{cogname}')
        except Exception as error:
            if context is None and not hasattr(context, 'author'):
                self.logger.critical(f'Failed to reload "{cogname}" : {error}')
            else:
                self.logger.critical(f'{context.author} tried to reload "{cogname}" but it errored: {error}')
            raise error
        else:
            if context is None and not hasattr(context, 'author'):
                self.logger.warn(f'Successfully reloaded "{cogname}"!')
            else:
                self.logger.warn(f'{context.author} reloaded "{cogname}"!')

    def load_cog(self, cogname : str, *, context : commands.Context = None):
        try:
            self.load_extension(f'cogs.{cogname}')
        except Exception as error:
            if context is None and not hasattr(context, 'author'):
                self.logger.critical(f'Failed to load "{cogname}" : {error}')
            else:
                self.logger.critical(f'{context.author} tried to load "{cogname}" but it errored: {error}')
            raise error
        else:
            if context is None and not hasattr(context, 'author'):
                self.logger.warn(f'Successfully loaded "{cogname}"!')
            else:
                self.logger.warn(f'{context.author} loaded "{cogname}"!')
 
    def unload_cog(self, cogname : str, *, context : commands.Context = None):
        try:
            self.unload_extension(f'cogs.{cogname}')
        except Exception as error:
            if context is None and not hasattr(context, 'author'):
                self.logger.critical(f'Failed to unload "{cogname}" : {error}')
            else:
                self.logger.critical(f'{context.author} tried to unload "{cogname}" but it errored: {error}')
            raise error
        else:
            if context is None and not hasattr(context, 'author'):
                self.logger.warn(f'Successfully unloaded "{cogname}"!')
            else:
                self.logger.warn(f'{context.author} unloaded "{cogname}"!')


print(pyfiglet.figlet_format("Andromeda", font='doom'))

loop = asyncio.get_event_loop()
loop.run_until_complete(start_andromeda())