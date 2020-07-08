import discord, asyncio, typing, datetime, humanize
from discord.ext import commands

from utils import butils

class InfoCommands(commands.Cog, name="Info"):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['av', 'pfp'])
    async def avatar(self, ctx, *, user : typing.Union[discord.Member, discord.User, int] = None):
        """Grabs a user's avatar, even if they aren't in the server (which is pretty pog)"""
        if user is None:
            user = ctx.author

        elif isinstance(user, int):
            user = await self.client.fetch_user(user)
            
            if user is None:
                return await ctx.send(
                    "<a:tried:623018822076727307> That isn't a valid user ID poo poo brain"
                )

        return await ctx.send(
            embed = butils.Embed(
                description = f"Steal this: [WEBP]({user.avatar_url_as(format='webp')}) **⋮** [PNG]({user.avatar_url_as(format='png')}) **⋮** [JEPG]({user.avatar_url_as(format='jpeg')})" + (f" **⋮** [GIF]({user.avatar_url_as(format='gif')})" if user.is_avatar_animated() else '')
            ).set_author(
                name = f"{user.display_name}'s Avatar", icon_url = user.avatar_url
            ).set_image(
                url = user.avatar_url
            )
        )

    @commands.guild_only()
    @commands.command(aliases=['user', 'u', 'ui', 'whois'])
    async def userinfo(self, ctx, *, user : typing.Union[discord.Member, discord.User, int] = None):
        """Gives information about a user, if no user is provided, shows your information"""
        if user is None: user = ctx.author

        if isinstance(user, int): # Provided an ID
            user = await self.client.fetch_user(user)

        em = butils.Embed(
            timestamp = discord.Embed.Empty
            #,colour = user.colour
        ).set_thumbnail(
            url = user.avatar_url
        ).set_author(
            name = f"{user}" + (f" ❱ {user.display_name}" if user.display_name != user.name else ""),
            icon_url = user.avatar_url
        )
        if user.colour is not None: em.colour = user.colour
        alt_date = butils.strfdelta(datetime.datetime.utcnow() - user.created_at, fmt="%D")
        em.description = f"""
        {user.mention} `{user.id}`
        Joined Discord : `{user.created_at.strftime('%A, %B %d %Y')}`
        Account Age: `{humanize.naturaldelta(datetime.datetime.utcnow() - user.created_at, months=False)}` {'`(' + alt_date + ' days)`' if int(alt_date) > 365 else ''}
        """

        if isinstance(user, discord.Member):
            em.add_field(
                name = "🛡️ | Guild Specific Information",
                value = f"""
                Joined Guild : `{user.joined_at.strftime('%A, %B %d %Y')}` `({humanize.naturaldelta(datetime.datetime.utcnow() - user.joined_at, months=False)})`
                Join Position : `#{sorted(ctx.guild.members, key=lambda m: m.joined_at).index(user) + 1:,}`"""
            )

            if len(user.roles) > 1: # need to compensate for @everyone role
                em.add_field(
                    name = f"🎖️ | Guild Roles ❱ {len(user.roles) - 1} Roles",
                    value = " ".join([r.mention for r in sorted(user.roles, key=lambda o: o.position, reverse=True)[:15] if r.name != "@everyone"]) + ('' if len(user.roles)-1 <= 15 else f' ... {len(user.roles)-16} more'),
                    inline=False
                )

        if hasattr(user, 'activity'):
            if isinstance(user.activity, discord.activity.Spotify):
                em.add_field(
                    name = "🎵 | Spotify Song",
                    value = f"""
                    **{user.activity.title}** from {user.activity.album}
                    `Artist{'s' if len(user.activity.artists) > 1 else ''}:` {', '.join(user.activity.artists)}
                    [<:spotify:652326837283979327> Listen to this](https://open.spotify.com/track/{user.activity.track_id})
                    """,
                    inline=False
                )

        return await ctx.send(
            embed = em
        )
    
    @commands.guild_only() # guild guildinfo command retar
    @commands.group(aliases=['guild', 'g', 's', 'server', 'serverinfo'])
    async def guildinfo(self, ctx):
        """Shows information about the guild you run it in"""
        e = []
        _e = sorted([str(vc) for vc in ctx.guild.emojis], key = lambda n: len(n))
        
        for i in _e:
            if len(''.join(e)) + len(i) <= 1024:
                e.append(i)
            else:
                break

        return await ctx.send(
            embed = butils.Embed(
                description = f"""Server ID: `{ctx.guild.id}`
                Region : `{str(ctx.guild.region).upper()}`
                Owner : {ctx.guild.owner.mention} (`{ctx.guild.owner.id}`)
                Verification Level: `{str(ctx.guild.verification_level).upper()}`
                Guild Age: `{ctx.guild.created_at.strftime('%A, %B %d %Y')}` `({humanize.naturaldelta(datetime.datetime.utcnow() - ctx.guild.created_at, months=False)})`
                Members: `{len(ctx.guild.members)}`, (`{len([i for i in ctx.guild.members if i.bot])}` Bots, `{round((len([i for i in ctx.guild.members if i.bot]) / len(ctx.guild.members))*100, 2)}%`)
                """
            )
            .set_thumbnail(
                url = ctx.guild.icon_url
            )
            .set_image(
                url = ctx.guild.banner_url if ctx.guild.banner_url is not None else discord.Embed.Empty
            )
            .set_author(
                name = ctx.guild.name, icon_url = ctx.guild.icon_url
            )
            .add_field(
                name = "<:NitroBoost:658026856905179142> | Boost Info",
                value = f"""Boost Level: `{ctx.guild.premium_tier}` (`{ctx.guild.premium_subscription_count}` Total Boosts)
                """,
                inline = False
            )
            .add_field(
                name = "📝 | Channels",
                value = f"""`{len(ctx.guild.text_channels)}` Text Channels
                `{len(ctx.guild.voice_channels)}` Voice Channels
                `{len(ctx.guild.categories)}` Categories
                `{len(ctx.guild.channels)}` Total Channels
                """,
                inline = False
            ).add_field(
                name = f"😎 | Emojis ({len(ctx.guild.emojis)} Total, {len(e)} Shown)",
                value = ''.join(e) if len(e) > 0 else "No Emojis",
                inline = False
            )
            
        )

def setup(client):
    client.add_cog(
        InfoCommands(client)
    )