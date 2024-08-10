import discord
import ping3
import ipaddress
from discord.ext import commands
import whois
import logging
import subprocess
import socket
import os
import time
import asyncio
from ping3 import ping, verbose_ping
import dns.resolver
import dns.zone
import dns.query
import dns.name

logging.basicConfig(level=logging.INFO, format='\033[94m%(asctime)s - %(levelname)s - %(message)s\033[0m', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('discord')

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f'App online - Name : {bot.user.name}')

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

        response_time = ping(ip)
        success = response_time is not None

        embed = discord.Embed(
            title="Résultat du Ping",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="Adresse IP", value=f"`{ip}`", inline=False)
        if domain_resolved:
            embed.add_field(name="Nom de domaine", value=f"`{domain_resolved}`", inline=False)
        embed.add_field(name="Statut", value="Réponse reçue" if success else "Pas de réponse", inline=False)
        if not success:
            embed.add_field(name="Erreur", value="Pas de réponse du serveur", inline=False)

        embed.set_footer(text="Résultat du ping effectué par le bot.")
        await ctx.respond(embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /ping_ip: {e}')
        await ctx.respond(f"Une erreur s'est produite lors du ping de `{target}`.")

@bot.slash_command(name="ping_me", description="Obtenir le ping du bot.")
async def ping_me(ctx):
    start_time = time.time()
    message = await ctx.respond("Calcul du ping...")
    end_time = time.time()
    latency = bot.latency * 1000  
    response_time = (end_time - start_time) * 1000  

    embed = discord.Embed(
        title="Ping du Bot",
        color=discord.Color.blue()
    )
    embed.add_field(name="Latence de l'API", value=f"{latency:.2f} ms", inline=False)
    embed.add_field(name="Temps de réponse", value=f"{response_time:.2f} ms", inline=False)
    embed.set_footer(text="Le temps de réponse peut varier en fonction de la charge du bot.")

    await message.edit(content=None, embed=embed)

@bot.slash_command(name="decompose_ip", description="Décompose une adresse IP en octets, binaire et hexadécimal.")
async def decompose_ip(ctx, ip: str):
    logger.info(f'Commande utilisée: /decompose_ip par {ctx.author.name} ({ctx.author.id}) pour l\'IP {ip}')
    try:
        ip_obj = ipaddress.ip_address(ip)
        octets = ip_obj.exploded.split(':') if ip_obj.version == 6 else ip_obj.exploded.split('.')
        
        if ip_obj.version == 4:
            binary_representation = '.'.join(f'{int(octet):08b}' for octet in octets)
            hex_representation = '.'.join(f'{int(octet):02X}' for octet in octets)
        else:
            binary_representation = ':'.join(f'{int(segment, 16):016b}' for segment in octets)
            hex_representation = ':'.join(f'{segment.upper()}' for segment in octets)

        embed = discord.Embed(
            title="Décomposition de l'adresse IP",
            color=discord.Color.blue()
        )
        embed.add_field(name="Adresse IP", value=f"`{ip}`", inline=False)
        embed.add_field(name="Nombre d'octets", value=f"`{len(octets)}`", inline=False)
        embed.add_field(name="Représentation binaire", value=f"`{binary_representation}`", inline=False)
        embed.add_field(name="Représentation hexadécimale", value=f"`{hex_representation}`", inline=False)
        embed.set_footer(text="Décomposition effectuée par le bot.")

        await ctx.respond(embed=embed)

    except ValueError as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /decompose_ip: {e}')
        await ctx.respond(f"Adresse IP invalide: `{ip}`.")
    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /decompose_ip: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la décomposition de `{ip}`.")

@bot.slash_command(name="convert", description="Convertir un nombre entre différents systèmes de numération.")
async def convert(ctx, number: str, target_type: str = discord.Option(
    choices=[
        discord.OptionChoice(name="Décimal", value="décimal"),
        discord.OptionChoice(name="Octal", value="octal"),
        discord.OptionChoice(name="Binaire", value="binaire"),
        discord.OptionChoice(name="Hexadécimal", value="hexadécimal")
    ]
)):
    logger.info(f'Commande utilisée: /convert par {ctx.author.name} ({ctx.author.id}) pour le nombre {number} et le type cible {target_type}')
    try:
        valid_target_types = {"décimal", "octal", "binaire", "hexadécimal"}
        
        if target_type not in valid_target_types:
            await ctx.respond("Type cible invalide. Utilisez `décimal`, `octal`, `binaire`, ou `hexadécimal`.")
            return

        try:
            if number.startswith("0b"):
                base = 2
                value = int(number, 2)
            elif number.startswith("0o"):
                base = 8
                value = int(number, 8)
            elif number.startswith("0x"):
                base = 16
                value = int(number, 16)
            else:
                value = int(number)
                base = 10
        except ValueError:
            await ctx.respond(f"Nombre invalide : `{number}`.")
            return

        if target_type == "décimal":
            result = str(value)
        elif target_type == "octal":
            result = oct(value)
        elif target_type == "binaire":
            result = bin(value)
        elif target_type == "hexadécimal":
            result = hex(value)

        embed = discord.Embed(
            title="Conversion de Nombre",
            color=discord.Color.blue()
        )
        embed.add_field(name="Nombre initial", value=f"`{number}`", inline=False)
        embed.add_field(name="Format cible", value=f"`{target_type}`", inline=False)
        embed.add_field(name="Résultat", value=f"`{result}`", inline=False)
        embed.set_footer(text="Conversion effectuée par le bot.")

        await ctx.respond(embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /convert: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la conversion de `{number}`.")

@bot.slash_command(name="decompose_dns", description="Afficher les enregistrements DNS d'un nom de domaine.")
async def decompose_dns(ctx, domain: str):
    logger.info(f'Commande utilisée: /decompose_dns par {ctx.author.name} ({ctx.author.id}) pour le domaine {domain}')
    
    try:
        records = []

        try:
            a_records = dns.resolver.resolve(domain, 'A')
            for record in a_records:
                records.append(f"{domain} A: {record.address}")
        except dns.resolver.NoAnswer:
            records.append(f"Aucun enregistrement A trouvé pour {domain}")
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des enregistrements A pour {domain}: {e}')

        try:
            cname_records = dns.resolver.resolve(domain, 'CNAME')
            for record in cname_records:
                records.append(f"{domain} CNAME: {record.target}")
        except dns.resolver.NoAnswer:
            records.append(f"Aucun enregistrement CNAME trouvé pour {domain}")
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des enregistrements CNAME pour {domain}: {e}')

        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            for record in mx_records:
                records.append(f"{domain} MX: {record.exchange} (Priorité: {record.preference})")
        except dns.resolver.NoAnswer:
            records.append(f"Aucun enregistrement MX trouvé pour {domain}")
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des enregistrements MX pour {domain}: {e}')

        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                records.append(f"{domain} TXT: {' '.join(record.strings)}")
        except dns.resolver.NoAnswer:
            records.append(f"Aucun enregistrement TXT trouvé pour {domain}")
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des enregistrements TXT pour {domain}: {e}')

        embed = discord.Embed(
            title=f"Enregistrements DNS pour `{domain}`",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Enregistrements DNS", value='\n'.join(records) if records else "Aucun enregistrement trouvé", inline=False)
        embed.set_footer(text="Certaines informations peuvent être incomplètes en raison des restrictions d'accès aux zones DNS.")

        await ctx.respond(embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /decompose_dns: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la récupération des enregistrements DNS pour `{domain}`.")

@bot.slash_command(name="tracert", description="Trace le chemin vers une IP ou un nom de domaine donné.")
async def tracert_command(ctx, target: str):
    logger.info(f'Commande utilisée: /tracert par {ctx.author.name} ({ctx.author.id}) pour la cible {target}')
    
    try:
        message = await ctx.respond(f"Exécution de la commande `tracert` vers `{target}`, cela peut prendre un moment...")

        process = await asyncio.create_subprocess_exec(
            'tracert', target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        try:
            output = stdout.decode('cp850')
        except UnicodeDecodeError:
            output = stdout.decode('utf-8', errors='replace')  
        if process.returncode != 0:
            output += f"\nUne erreur s'est produite lors de l'exécution de la commande tracert. Code de retour: {process.returncode}\n{stderr.decode('cp850')}"

        if len(output) > 2000:
            output = output[:1997] + "..."
        
        embed = discord.Embed(
            title=f"Résultat du Tracert vers `{target}`",
            description=f"```{output}```",
            color=discord.Color.blue()
        )

        await message.edit_original_response(content=None, embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande tracert: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de l'exécution de la commande tracert pour `{target}`.")

bot.run("")
