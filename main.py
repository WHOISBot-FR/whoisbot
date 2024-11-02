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
import psutil
import requests
import ssl
from ping3 import ping, verbose_ping
import dns.resolver
import dns.zone
import dns.query
import dns.name
from scapy.layers.inet import traceroute
from scapy.all import conf
from datetime import datetime

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
    
    await ctx.respond(f"Recherche des informations WHOIS pour `{domain}`... Cela peut prendre un moment.")
    
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

        await ctx.edit(content=None, embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande WHOIS: {e}')
        await ctx.edit(content=f"Une erreur s'est produite lors de la récupération des informations WHOIS pour `{domain}`.")

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
    
    await ctx.respond(f"Ping de `{target}` en cours...")

    try:
        try:
            ip = socket.gethostbyname(target)
            domain_resolved = target
        except socket.gaierror:
            await ctx.edit(content=f"Erreur: Le nom de domaine ou l'adresse IP `{target}` est invalide ou introuvable.")
            return

        response_time = ping(ip)
        success = response_time is not None

        geo_url = f"http://ip-api.com/json/{ip}"
        geo_response = requests.get(geo_url).json()
        
        location_info = (
            f"**Pays:** {geo_response.get('country', 'N/A')}\n"
            f"**Région:** {geo_response.get('regionName', 'N/A')}\n"
            f"**Ville:** {geo_response.get('city', 'N/A')}\n"
            f"**ISP:** {geo_response.get('isp', 'N/A')}"
        )

        embed = discord.Embed(
            title="Résultat du Ping",
            color=discord.Color.green() if success else discord.Color.red()
        )
        embed.add_field(name="Adresse IP", value=f"`{ip}`", inline=False)
        if domain_resolved:
            embed.add_field(name="Nom de domaine", value=f"`{domain_resolved}`", inline=False)
        embed.add_field(name="Statut", value="Réponse reçue" if success else "Pas de réponse", inline=False)
        
        if success:
            embed.add_field(name="Temps de réponse", value=f"`{response_time}` ms", inline=False)
        else:
            embed.add_field(name="Erreur", value="Le ping a échoué. Le serveur pourrait refuser les requêtes ICMP.", inline=False)

        embed.add_field(name="Localisation", value=location_info, inline=False)

        embed.set_footer(text="Résultat du ping effectué par le bot.")
        await ctx.edit(content=None, embed=embed)

    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /ping_ip: {e}')
        await ctx.edit(content=f"Une erreur s'est produite lors du ping de `{target}`.")

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

@bot.slash_command(name="server_stats", description="Affiche l'utilisation actuelle de la CPU et de la RAM du serveur.")
async def server_stats(ctx):
    logger.info(f'Commande utilisée: /server_stats par {ctx.author.name} ({ctx.author.id})')
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent

        embed = discord.Embed(title="Statistiques du serveur", color=discord.Color.blue())
        embed.add_field(name="Utilisation CPU", value=f"{cpu_usage}%", inline=False)
        embed.add_field(name="Utilisation RAM", value=f"{ram_usage}%", inline=False)
        embed.set_footer(text="Ces informations sont mises à jour en temps réel.")

        await ctx.respond(embed=embed)
    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /server_stats: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la récupération des statistiques du serveur.")

@bot.slash_command(name="reverse_dns", description="Effectue un reverse DNS lookup pour une adresse IP.")
async def reverse_dns(ctx, ip: str):
    logger.info(f'Commande utilisée: /reverse_dns par {ctx.author.name} ({ctx.author.id}) pour l\'IP {ip}')
    try:
        domain = socket.gethostbyaddr(ip)
        await ctx.respond(f"L'adresse IP `{ip}` est associée au domaine `{domain[0]}`.")
    except socket.herror:
        await ctx.respond(f"Aucun domaine trouvé pour l'adresse IP `{ip}`.")
    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /reverse_dns: {e}')
        await ctx.respond(f"Une erreur s'est produite lors du reverse DNS lookup pour `{ip}`.")

async def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        result = sock.connect_ex((ip, port))
        return port if result == 0 else None

@bot.slash_command(name="scan_ports", description="Scanne les ports ouverts sur une adresse IP.")
async def scan_ports(ctx, ip: str):
    logger.info(f'Commande utilisée: /scan_ports par {ctx.author.name} ({ctx.author.id}) pour l\'IP {ip}')
    await ctx.defer()  
    
    try:
        response_time = ping(ip)
        if response_time is None:
            await ctx.followup.send(f"L'adresse IP `{ip}` est injoignable. Le scan des ports ne peut pas être effectué.")
            return
        
        open_ports = []
        tasks = [check_port(ip, port) for port in range(1, 1025)]
        results = await asyncio.gather(*tasks)
        
        open_ports = [port for port in results if port is not None]

        if open_ports:
            await ctx.followup.send(f"Les ports ouverts sur `{ip}` sont : `{', '.join(map(str, open_ports))}`.")
        else:
            await ctx.followup.send(f"Aucun port ouvert détecté sur `{ip}`.")
    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /scan_ports: {e}')
        await ctx.followup.send(f"Une erreur s'est produite lors du scan des ports sur `{ip}`.")

@bot.slash_command(name="reverse_lookup", description="Trouver tous les domaines liés à une adresse IP.")
async def reverse_lookup(ctx, ip: str):
    logger.info(f'Commande utilisée: /reverse_lookup par {ctx.author.name} ({ctx.author.id}) pour l\'IP {ip}')
    try:
        domains = dns.resolver.resolve_reverse(ip)
        embed = discord.Embed(title=f"Domaines associés à {ip}", description=f"Domaines : {', '.join(domains)}", color=discord.Color.blue())
        await ctx.respond(embed=embed)
    except Exception as e:
        logger.error(f'Erreur lors de la commande /reverse_lookup: {e}')
        embed = discord.Embed(title="Erreur", description=f"Erreur lors de la recherche DNS inverse pour `{ip}`.", color=discord.Color.red())
        await ctx.respond(embed=embed)


@bot.slash_command(name="http_version", description="Obtenir la version du serveur HTTP d'une URL.")
async def http_version(ctx, url: str):
    logger.info(f'Commande utilisée: /http_version par {ctx.author.name} ({ctx.author.id}) pour l\'URL {url}')
    try:
        response = requests.head(url)
        server_version = response.headers.get('Server', 'Non disponible')
        embed = discord.Embed(title=f"Version HTTP de {url}", description=f"Serveur : {server_version}", color=discord.Color.blue())
        await ctx.respond(embed=embed)
    except Exception as e:
        logger.error(f'Erreur lors de la commande /http_version: {e}')
        embed = discord.Embed(title="Erreur", description=f"Erreur lors de la récupération de la version HTTP pour `{url}`.", color=discord.Color.red())
        await ctx.respond(embed=embed)

@bot.slash_command(name="network_latency", description="Tester la latence réseau vers plusieurs serveurs cibles.")
async def network_latency(ctx):
    targets = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
    results = []
    for target in targets:
        try:
            result = ping(target)
            results.append(f"{target} : {result} ms" if result else f"{target} : Aucun résultat")
        except Exception as e:
            results.append(f"{target} : Erreur")
    
    embed = discord.Embed(title="Résultats des tests de latence", description="\n".join(results), color=discord.Color.blue())
    await ctx.respond(embed=embed)

@bot.slash_command(name="tracert", description="Déterminer la route vers une IP ou URL.")
async def tracert(ctx, target: str):
    logger.info(f'Commande utilisée: /tracert par {ctx.author.name} ({ctx.author.id}) pour le target {target}')
    
    try:
        conf.verb = 0
        res, unans = traceroute(target, maxttl=30)

        result = ""
        for snd, rcv in res:
            result += f"{snd.ttl} {rcv.src}\n"
        
        embed = discord.Embed(title=f"Traceroute vers {target}", description=f"```\n{result}\n```", color=discord.Color.blue())
        await ctx.respond(embed=embed)
    
    except Exception as e:
        logger.error(f'Erreur lors de l\'exécution de la commande /tracert: {e}')
        await ctx.respond(f"Une erreur s'est produite lors de la tentative de traceroute vers `{target}`.")

@bot.slash_command(name="ssl_check", description="Vérifie les informations SSL d'un domaine")
async def ssl_check(ctx, domain: str):
    logger.info(f'Commande utilisée: /ssl_check par {ctx.author.name} ({ctx.author.id})')
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

        issuer = dict(x[0] for x in cert['issuer'])
        issuer_name = issuer.get('organizationName', 'Inconnu')
        valid_from = datetime.strptime(cert['notBefore'], "%b %d %H:%M:%S %Y %Z")
        valid_until = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        days_left = (valid_until - datetime.utcnow()).days
        status = "Valide" if days_left > 0 else "Expiré"

        embed = discord.Embed(
            title=f"Vérification SSL pour {domain}",
            color=0x00ff00 if status == "Valide" else 0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Émetteur", value=issuer_name, inline=False)
        embed.add_field(name="Valide depuis", value=valid_from.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Expire le", value=valid_until.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Jours restants", value=str(days_left), inline=True)
        embed.add_field(name="Statut", value=status, inline=False)
        embed.set_thumbnail(url="https://ssl.gstatic.com/ui/v1/icons/mail/rfr/gmail_security_checkup_dark_24dp.png")
        embed.set_footer(text="Vérification SSL")

        await ctx.respond(embed=embed)

    except Exception as e:
        await ctx.respond(f"Erreur lors de la vérification SSL pour {domain}: {str(e)}", ephemeral=True)        

bot.run("")
