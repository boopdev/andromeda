import asyncio, discord, os, traceback, sys, yaml
from discord.ext import commands
from utils import checks, butils, bconv
from utils import smartCD as cd

# .eval imports
import textwrap, psutil, io
from contextlib import redirect_stdout

# Checksum Command Imports
import glob, hashlib

# Checksum Function
def md5_checksum(fpath):
    _h = hashlib.md5()
    with open(fpath, mode='rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            _h.update(chunk)
    return _h.hexdigest()

class DevCog(commands.Cog, name='Developer'):
    def __init__(self, client):
        self.client = client

        self._last_result = None
        self.sessions = set()

        self.__cog_settings__['hidden']=True

        @self.client.check
        async def developer_mode(ctx):
            if not ctx.bot._config['developer-mode']: return True
            org=checks.require_rank(ctx.bot._config['developer-mode-mod-rank']).predicate
            return await org(ctx, noerror=True)

    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def checksum(self, ctx):
        """Checksum all scarlo bot files"""
        async with ctx.channel.typing():

            _glob = glob.glob("./**/*.py") # Grabs all the .py files
            checksums = {p : md5_checksum(p) for p in _glob} # Generate Hashes

            p = commands.Paginator(prefix="",suffix="") # Paginator
            for s in checksums.keys():
                _fn = os.path.split(s)[1] # Get file name
                p.add_line(f"\📜 **{_fn}** `{checksums[s]}`")
            for a in p.pages: await ctx.send(a) # Send pages

    @commands.is_owner()
    @checksum.command(name='compare')
    async def checksum_compare(self, ctx, *, csum):
        "Compare a checksum to all the other files' checksums, the bot will return any that match"

        _glob = glob.glob("./**/*.py") # Grabs all the .py files
        checksums = {p : md5_checksum(p) for p in _glob} # Generate Hashes

        if not csum in checksums.values():
            return await ctx.send(
                f'> ❌ | `No files match "{csum}"`'
            )
        else:
            x = list(filter(lambda k: csum == checksums[k], checksums))
            return await ctx.send(
                "> ✅ " + ",".join([os.path.split(i)[1] for i in x])
            )

    @commands.is_owner()
    @commands.command(name='reload', aliases=['rl', 'rlc'])
    async def _reloadcog(self, ctx, cog : str):
        try:
            self.client.reload_cog(cog, context=ctx)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            return await ctx.send("> ❌ | `Encountered an Error!`\n```py\n" + ''.join(traceback.format_exception(exc_type, exc_value,exc_traceback)) + "```")
        else:
            return await ctx.send(
                f"> ✅ | **{cog.upper()}** `was reloaded!`"
            )

    @commands.is_owner()
    @commands.command(name='load', aliases=['lc',])
    async def _loadcog(self, ctx, cog : str):
        try:
            self.client.load_cog(cog, context=ctx)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            return await ctx.send("> ❌ | `Encountered an Error!`\n```py\n" + ''.join(traceback.format_exception(exc_type, exc_value,exc_traceback)) + "```")
        else:
            return await ctx.send(
                f"> ✅ | **{cog.upper()}** `was loaded!`"
            )

    @commands.is_owner()
    @commands.command(name='unload', aliases=['ul', 'ulc'])
    async def _unloadcog(self, ctx, cog : str):
        try:
            self.client.unload_cog(cog, context=ctx)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            return await ctx.send("> ❌ | `Encountered an Error!`\n```py\n" + ''.join(traceback.format_exception(exc_type, exc_value,exc_traceback)) + "```")
        else:
            return await ctx.send(
                f"> ✅ | **{cog.upper()}** `was unloaded`"
            )

    @commands.is_owner()
    @commands.group(invoke_without_command=True, aliases=['sql', 'postgres'])
    async def psql(self, ctx):
        async with self.client.db.acquire() as con:
            _dbinf = con.get_server_version()

        return await ctx.send(
            "```diff\n- Postgres Version: {0.major}.{0.minor}.{0.micro} {0.releaselevel}````=psql execute (query)`\n`=psql fetch (query)`\n`=psql fetchrow (query)`".format(_dbinf)
        )

    @commands.is_owner()
    @psql.command(name="execute", aliases=['exec', 'e'])
    async def psql_execute(self, ctx, *, query : str):
        try:
            x = await self.client.db.execute(query)
        except Exception as err:
            x = err
        return await ctx.send(
            embed = butils.Embed(
                description = f"```\n{str(x)}```"
            ).set_author(
                name = "Query Results", icon_url = ctx.author.avatar_url
            )
        )

    @commands.is_owner()
    @psql.command(name="fetch", aliases=['fet', 'f'])
    async def psql_fetch(self, ctx, *, query : str):
        """Fetches data from the database"""
        try:
            x = await self.client.db.fetch(query)
        except Exception as err:
            x = err
            
        p = ""
        if isinstance(x, Exception):
            p = str(x)
        else:
            o = x[:32]
            p = "\n".join([",".join(list(i.values())) for i in o])

        return await ctx.send(
            embed = butils.Embed(
                description = p
            ).set_author(
                name = "Query Results", icon_url = ctx.author.avatar_url
            ).set_footer(
                text = f"Showing results {len(o)} / {len(x)}"
            )
        )

    @commands.is_owner()
    @psql.command(name="fetchrow", aliases=['fr', 'fetr', 'fetrow'])
    async def psql_fetchrow(self, ctx, *, query : str):
        """Fetches data from the database"""
        try:
            x = await self.client.db.fetchrow(query)
        except Exception as err:
            x = err
        return await ctx.send(
            embed = butils.Embed(
                description = f"```\n{str(x)}```" if isinstance(x, Exception) else f"```\n{list(x.values())}```"
            ).set_author(
                name = "Query Results", icon_url = ctx.author.avatar_url
            )
        )        

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')


    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True, name='eval', aliases=['ev'])
    @commands.is_owner()
    async def _eval(self, ctx, *, body: str):
        """Evaluates code"""

        env = {
            'self': self,
            'client': self.client,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'os': os,
            'ps': psutil,
            'discord': discord,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.is_owner()
    @commands.command(name='sudo')
    async def _sudo(self, ctx, user : discord.Member, *, brr : str):
        "Run a command as another user"
        nctx=await butils.copy_context_with(ctx, author=user, content=ctx.prefix + brr)
        if nctx.command is None:
            if nctx.invoked_with is None:
                return await ctx.send("tf happened")
            return await ctx.send("no command found dumbass lmao")
        return await nctx.command.invoke(nctx)
        

    @commands.command()
    async def ping(self, ctx):
        "pong!"
        return await ctx.send(f'> 🏓 `{round(self.client.latency*500, 2):,}ms`')

    @checks.require_rank("developer")
    @commands.command(name="test")
    async def _test(self, ctx):
        """Test Command"""
        return await ctx.send(str(self.client.get_cog('Economy').pickaxes))

    @commands.is_owner()
    @commands.command()
    async def die(self, ctx):
        "Kills the bot"
        await ctx.send("<:fmlS:587015100355969025> Adios nigga")
        await self.client.clean_kill()

def setup(client):
    client.add_cog(DevCog(client))