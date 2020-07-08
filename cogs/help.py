import discord, asyncio
from discord.ext import commands, menus

def _cmd_get_full_posix_sig(c : commands.Command):
    _cmd_aliases = c.aliases
    return "{} {}".format(
        c.name,
        c.signature
    )

class HelpDialog(commands.Cog, name="Help"):
    def __init__(self, client):
        self.client = client
        self.client.remove_command('help')

        # Testing this shit
        self.__cog_settings__['hidden']=True

    class CommandHelp():
        def __init__(self, cmd : commands.Command):
            self.cmd = cmd
            self.cog_obj = cmd.cog
            self.cog = cmd.cog.qualified_name # Key
            self.name = cmd.name # Value i think
            self.qualified_name = cmd.qualified_name
            self.sig = _cmd_get_full_posix_sig(cmd)

        @property
        def proper_short_doc(self):
            if len(self.cmd.short_doc) > 0: return self.cmd.short_doc
            return "No description, ping boop to fix this lmao"


    class HelpMenu(menus.GroupByPageSource):
        async def format_page(self, menu, entry):
            x='\n'.join(f"> **{menu.ctx.prefix}{v.sig}**\n`{v.proper_short_doc}`\n" for v in entry.items)
            return discord.Embed(
                title=entry.key.upper(),
                description=x
            ).set_footer(
                text=f"Page {menu.current_page+1} of {self.get_max_pages()}", icon_url=menu.ctx.bot.user.avatar_url
            ).set_thumbnail(
                url=menu.ctx.bot.scarlyst.icon_url
            )
            #return f"**{entry.key.upper()}**\n{x}\n```\n{menu.current_page+1} / {self.get_max_pages()}```"

    @commands.command(name='help')
    async def _help(self, ctx):
        """Help Command"""
        cmds = [self.CommandHelp(x) for x in self.client.commands]
        if not ctx.author.id in self.client.owner_ids:
            cmds = list(filter(lambda q: not q.cog_obj.__cog_settings__.get('hidden', False), cmds)) # Filters out hidden cogs if the user isnt an owner
            cmds = list(filter(lambda q: not q.cmd.hidden, cmds)) # Filters out hidden commands
        pgs = menus.MenuPages(source=self.HelpMenu(cmds, key=lambda t: t.cog, per_page=5), clear_reactions_after=True, delete_message_after=True)
        await pgs.start(ctx)

def setup(client):
    client.add_cog(HelpDialog(client))