import discord
from discord.ext import commands
import whois
import logging
import subprocess
import socket
import os

logging.basicConfig(level=logging.INFO, format='\033[94m%(asctime)s - %(levelname)s - %(message)s\033[0m', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('discord')

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.slash_command(name="whois", description="Obtenir des informations WHOIS pour un domaine.")
async def whois_command(ctx, domain: str):
    logger.info(f'Commande utilisée: /whois par {ctx.author.name} ({ctx.author.id}) pour le domaine {domain}')
    try:
        w = whois.whois(domain)

        embed = discord.Embed(title=f"WHOIS Information pour `{domain}`", color=discord.Color.blue())
        
        embed.add_field(name="Domaine", value=f"`{w.domain_name}`" if w.domain_name else "`N/A`", inline=False)
        embed.add_field(name="Registrar", value=f"`{w.registrar}`" if w.registrar else "`N/A`", inline=False)
        embed.add_field(name="Date de création", value=f"`{w.creation_date}`" if w.creation_date else "`N/A`", inline=False)
        embed.add_field(name="Date d'expiration", value=f"`{w.expiration_date}`" if w.expiration_date else "`N/A`", inline=False)
        embed.add_field(name="Serveurs de noms", value=f"`{'`, `'.join(w.name_servers)}`" if w.name_servers else "`N/A`", inline=False)
        embed.set_footer(text="Ces informations sont fournies par notre prestataire, nous ne garantissons pas la véracité de celle ci.")

        contact_info = (
            f"**Email:** `{w.emails}`\n"
            f"**Organisation:** `{w.org}`\n"
            f"**Pays:** `{w.country}`\n"
            f"**Ville:** `{w.city}`\n"
            f"**Adresse:** `{w.address}`\n"
            f"**Numéro de téléphone:** `{w.phone}`"
        )
        embed.add_field(name="Informations de contact", value=contact_info if w.emails else "`N/A`", inline=False)

        await ctx.respond(embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande WHOIS: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la récupération des informations WHOIS pour `{domain}`.")

@bot.slash_command(name="userinfo", description="Obtenir des informations sur un utilisateur à l'aide de son identifiant.")
async def userinfo(ctx, user_id: str):
    try:
        user = await bot.fetch_user(user_id)
        embed = discord.Embed(title=f"Informations sur l'utilisateur `{user.name}`", color=discord.Color.blue())

        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        embed.add_field(name="Nom complet", value=f"`{user.name}#{user.discriminator}`", inline=False)
        embed.add_field(name="ID", value=f"`{user.id}`", inline=False)
        embed.add_field(name="Créé le", value=f"`{user.created_at.strftime('%d/%m/%Y à %H:%M:%S')}`", inline=False)
        embed.add_field(name="Bot", value=f"`{'Oui' if user.bot else 'Non'}`", inline=False)
        embed.set_footer(text="Ces informations sont fournies par l'API de Discord.")

        await ctx.respond(embed=embed)
        logger.info(f'Commande utilisée: /userinfo par {ctx.author.name} ({ctx.author.id}) pour l\'utilisateur {user_id}')

    except discord.NotFound:
        await ctx.respond(f"Aucun utilisateur trouvé avec l'ID `{user_id}`.")
        logger.error(f'Erreur: Utilisateur avec l\'ID {user_id} introuvable.')
    except Exception as e:
        await ctx.respond(f"Une erreur s'est produite lors de la récupération des informations pour l'utilisateur `{user_id}`.")
        logger.error(f'Erreur lors de l\'exécution de la commande userinfo: {e}')

@bot.slash_command(name="ping_ip", description="Ping une adresse IP ou un nom de domaine pour vérifier s'il répond.")
async def ping_ip(ctx, target: str):
    logger.info(f'Commande utilisée: /ping_ip par {ctx.author.name} ({ctx.author.id}) pour le target {target}')
    try:
        try:
            ip = socket.gethostbyname(target)
            domain_resolved = target
        except socket.gaierror:
            ip = target
            domain_resolved = None

        param = '-n' if os.name == 'nt' else '-c'
        command = ['ping', param, '1', ip]

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success = result.returncode == 0

        embed = discord.Embed(
            title="Résultat du Ping",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="Adresse IP", value=f"`{ip}`", inline=False)
        if domain_resolved:
            embed.add_field(name="Nom de domaine", value=f"`{domain_resolved}`", inline=False)
        embed.add_field(name="Statut", value="Réponse reçue" if success else "Pas de réponse", inline=False)
        embed.set_footer(text="Résultat du ping effectué par le bot.")

        await ctx.respond(embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /ping_ip: {e}')
        await ctx.respond(f"Une erreur s'est produite lors du ping de `{target}`.")

bot.run("")
