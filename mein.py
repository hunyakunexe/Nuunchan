


import asyncio
import difflib
import functools
from collections import defaultdict, deque
import base64
import hashlib
import io
import json
import math
import shutil
import os
import random
import sys
import re
import threading
import time
from pathlib import Path
from typing import Literal, Optional, Union

try:
    import numpy as np
except ImportError:  
    np = None

import discord
from discord import app_commands
from discord.ext import commands

                                                                    
                                               
                                                               
                                                                                               
ANGOUMAGIC = b"NUUNENC1"

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
except ImportError:
    _AESGCM = None

if _AESGCM is None:
    raise SystemExit(
        "保存データの暗号化には cryptography が必要です: pip install cryptography"
    )


def kagiseisei(raw):
    raw = str(raw or "").strip()
    try:
        b = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    except Exception:
        b = b""
    if len(b) == 32:
        return b
    return hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), b"nuun-data-key-v1", 200000, 32)


deetaoya = Path(os.environ.get("BOT_DATA_DIR") or os.environ.get("NUUNDATADIR") or "/data")


def deetamkdir(path):
    """読み取り専用マウント上の既存フォルダでも落ちないように作成する"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
    except OSError:
        if not Path(path).is_dir():
            raise


def kagiyomu():
    raw = os.environ.get("NUUNDATAKEY", "").strip() or os.environ.get("NUUN_DATA_KEY", "").strip()
    if raw:
        return kagiseisei(raw), "env"
    kagifile = deetaoya / ".nuundatakey"
    oldkagifile = kagifile.with_name(".nuun_data_key")
    deetamkdir(kagifile.parent)
    if kagifile.is_file():
        raw = kagifile.read_text("utf-8").strip()
        if raw:
            return kagiseisei(raw), "file"
    if oldkagifile.is_file():
        raw = oldkagifile.read_text("utf-8").strip()
        if raw:
            kagifile.write_text(raw, "utf-8")
            try:
                os.chmod(kagifile, 0o600)
            except OSError:
                pass
            return kagiseisei(raw), "file"
    raw = base64.urlsafe_b64encode(os.urandom(32)).decode()
    kagifile.write_text(raw, "utf-8")
    try:
        os.chmod(kagifile, 0o600)
    except OSError:
        pass
    print("NUUNDATAKEY が未設定のため data/.nuundatakey を新しく作りました。")
    print("本番では NUUNDATAKEY にこの値を設定し、鍵ファイルは別の場所へ退避してください。")
    return kagiseisei(raw), "file"


KAGI, KAGIMOTO = kagiyomu()
if KAGIMOTO == "file":
    print("警告: 暗号鍵をデータと同じフォルダに置いています。環境変数 NUUNDATAKEY の利用を推奨します。")
AESGCMKAGI = _AESGCM(KAGI)


def angoukabare(path):
    try:
        with open(path, "rb") as f:
            head = f.read(len(ANGOUMAGIC))
    except OSError:
        return False
    return head == ANGOUMAGIC


def angou(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    nonce = os.urandom(12)
    return ANGOUMAGIC + nonce + AESGCMKAGI.encrypt(nonce, data, ANGOUMAGIC)


def fukugou(data):
    if data[: len(ANGOUMAGIC)] != ANGOUMAGIC:
        return data                        
    nonce = data[len(ANGOUMAGIC): len(ANGOUMAGIC) + 12]
    try:
        return AESGCMKAGI.decrypt(nonce, data[len(ANGOUMAGIC) + 12:], ANGOUMAGIC)
    except Exception as error:
        raise RuntimeError(
            "保存データを復号できません。NUUNDATAKEY が保存時と違う値になっていないか確認してください。"
        ) from error


def yomubytes(path):
    return fukugou(Path(path).read_bytes())


def yomutext(path):
    return yomubytes(path).decode("utf-8")


def kakubytes(path, data):
    Path(path).write_bytes(angou(data))


def kakutext(path, text):
    kakubytes(path, text.encode("utf-8"))


class AngouWriter:
    """平文でファイルに書いていた箇所を、暗号化して書き出すための小さなラッパー"""

    def __init__(self, path):
        self.path = Path(path)
        self.buf = io.StringIO()

    def __enter__(self):
        return self.buf

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                kakutext(self.path, self.buf.getvalue())
        finally:
            self.buf.close()
        return False


def angoumigrate(path, text):
    """平文のまま残っているファイルを暗号化して置き換える"""
    try:
        if Path(path).is_file() and not angoukabare(path):
            kakutext(path, text)
            return True
    except OSError:
        pass
    return False


                                                    


basho = Path(__file__).parent
deeta = deetaoya
deetamkdir(deeta)
print(f"[mein.py] データ保存先: {deeta}")

failemei = (
    "settei.json", "kotoba.json", "model.json", "train.json",
    "nuunchan.json", "learning_exclude.json", "memory.json",
    "memory_vec.npz", "memory_vec.npy", "model_vec.npz",
    "model_vec.npy", "consent.json",
)
for namae in failemei:
    moto = basho / namae
    saki = deeta / namae
    if moto.is_file() and not saki.exists():
        try:
            moto.replace(saki)
        except OSError:
            pass

for moto in basho.iterdir():
    if moto.is_file() and moto.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        saki = deeta / moto.name
        if not saki.exists():
            try:
                moto.replace(saki)
            except OSError:
                pass

setteifile = deeta / "settei.json"
kotobafile = deeta / "kotoba.json"
modelfile = deeta / "model.json"
trainingfile = deeta / "train.json"
nuunchanfile = deeta / "nuunchan.json"
learningexcludefile = deeta / "learning_exclude.json"
learningowner = 1539822756831690776
data_purged = False
banpuid = 302050872383242240

tokun = os.environ.get("DISCORD_BOT_TOKEN") or "ここにBotトークンを入れてください"
gachago = "ぬーんガチャ"
koteiritsu = 1 / 5                              
renpo_window = 5.0
renpo_limit = 7
renpo = defaultdict(deque)
recent_human_messages = {}
tokenre = re.compile(r"[一-龥々]+|[ァ-ヴー]{2,}|[A-Za-z0-9]{2,}")
tomeru = {"今日", "明日", "昨日", "今", "何", "私", "自分", "人", "時", "事", "日", "本当", "最近"}

                                                                                       
owarire = re.compile(r"(?:[ぬヌ][ーｰ〜~ぅぉおぁっゥォオァッ]*[んン]|[。！？!?…])[。！？!?…~〜]*")


nuunre = re.compile(r"[ぬNヌ][^\s]{0,6}?[んNン]")

Kiri = Literal["オン", "オフ"]


_UP = r"A-ZＡ-Ｚ"
_nuun_voice = re.compile(r"[ぬヌ][^\s]{0,6}?[んン]")
_joshi_ok = {"と", "の", "が", "は", "を", "に", "で", "も", "や", "から", "まで", "って", "より", "など", "とか", "とは", "では", "には", "でも", "ですが", "です", "だ", "な"}


def is_gibberish(text):

    t = re.sub(r"\s+", "", str(text or ""))
    t = re.sub(r"<[^>\n]*>|:[A-Za-z0-9_]+:", "", t)        
    t = _nuun_voice.sub("", t)                                  
    if len(t) < 8:
        return False
    score = 0
    ups = sum(1 for c in t if re.match(f"[{_UP}]", c))
    
    
    segs = re.findall(f"(?<=[{_UP}])([^{_UP}]{{1,6}})(?=[{_UP}])", t)
    odd_segs = [x for x in segs if x not in _joshi_ok and re.fullmatch(r"[ぁ-んァ-ヴ一-龥ー]+", x)]
    if len(odd_segs) >= 3:
        score += 2
    elif len(odd_segs) >= 2:
        score += 1
    if ups / len(t) >= 0.2 and odd_segs:
        score += 1
    
    collapsed = re.sub(r"(.)\1+", r"\1", t)
    odd = len(re.findall(r"(?<![あぁ])ぁ|(?<![いぃ])ぃ|(?<![えぇ])ぇ|(?<![おぉ])ぉ|[ゎゐゑ]", collapsed))   
    if odd >= 3:
        score += 1
    if odd >= 2 and ups >= 3:
        score += 2
    
    if ups >= 3 and re.search(r"[あいうえお]{4,}", collapsed):
        score += 2
    if score >= 3:
        return True
    
    for run in re.findall(r"[A-Za-zＡ-Ｚａ-ｚ]{8,}", t):
        r = run.translate(str.maketrans("ＡＥＩＯＵａｅｉｏｕ", "AEIOUaeiou")).lower()
        if len(set(r)) >= 5 and sum(ch in "aeiou" for ch in r) / len(r) < 0.2:
            return True
    return False


mangled_re = re.compile(
    r"[一-龥ァ-ヴ]しる|ことにしる|までにしる|ておきる|ていきる|ありる|ありた(?![いかくけ])|やりる|なりる|終わりる"
)

stray_mark_re = re.compile(r"[゛゜゙゚]|\[(?:SYSTEM|INFO|WARN|ERROR|BOT)\]", re.I)


def is_broken_text(text):

    t = str(text or "")
    return bool(is_gibberish(t) or mangled_re.search(t) or stray_mark_re.search(t))


chishiki_tomeru = {
    "です", "ます", "から", "まで", "ので", "のに", "けど", "でも", "だけ", "より", "など", "って", "とは", "では", "には",
    "して", "した", "する", "ない", "ある", "いる", "こと", "もの", "よう", "これ", "それ", "あれ", "どれ", "なに", "なん",
    "だれ", "どこ", "いつ", "どう", "ここ", "そこ", "でした", "ました", "ません", "いい", "うん", "はい", "あの", "その",
    "この", "どの", "だよ", "よね", "かな", "ですか", "ますか", "について", "どんな", "教えて", "ください", "知って", "知ってる",
    "お願い", "なる", "なっ", "いて", "って何", "とは何", "という", "ている", "てる", "でき", "ちゃん", "さん", "くん",
    "何", "誰", "人", "事", "時", "日", "今", "私", "俺", "僕", "自分", "今日", "明日", "昨日", "最近", "本当", "皆",
    "よく", "もう", "まだ", "すぐ", "ため", "ところ", "みたい", "らしい", "だった", "だろう", "でしょ", "じゃ", "たい", "れる",
    "られ", "せる", "ている", "でる", "なら", "ので", "から", "ます", "ませ", "った", "って", "ない", "なく", "より", "ほど",
}

chishiki_kinou = re.compile("|".join(
    re.escape(w) for w in sorted((w for w in chishiki_tomeru if re.fullmatch(r"[ぁ-ん]+", w)), key=len, reverse=True)
))
chishiki_crawling = set()


vec_model_name = "cl-nagoya/ruri-v3-130m"
vec_seed_min = 0.65     
vec_prefix = ""         
vec_max_len = 128       
vec_fact_min = 0.55     
vec_turn_min = 0.65     
vec_margin = 0.06       
vec_max_hints = 3       
vec_dl_retries = 5      
vec_dl_wait = 30        


def yomu(file, hajime):
    if not file.is_file():
        kakutext(file, json.dumps(hajime, ensure_ascii=False, indent=2))
        return hajime
    try:
        moji = yomutext(file)
        data = json.loads(moji)
        angoumigrate(file, moji)
        return data
    except json.JSONDecodeError as error:
        backup = file.with_suffix(file.suffix + ".broken")
        if not backup.exists():
            shutil.copy2(file, backup)
        raise RuntimeError(
            f"{file} のJSONが壊れています。{error.lineno}行{error.colno}列を確認してください。"
            f"元ファイルは {backup} に保全しました。"
        ) from error


settei = yomu(setteifile, {})
if not settei.get("hanv2"):
    for cfg in settei.values():
        if isinstance(cfg, dict) and isinstance(cfg.get("hannou"), dict):
            for cid in list(cfg["hannou"]):
                cfg["hannou"][cid] = False
    settei["hanv2"] = True
    kakutext(setteifile, json.dumps(settei, ensure_ascii=False, indent=2))
kotoba = yomu(kotobafile, {
    "banpu": {"bun": "Bumpを検知したぬーん", "gazou": None},
    "gacha": {
        "例": {"ritsu": 100, "bun": "ぬーんガチャの例ぬーん", "gazou": None},
    },
    "hannou": [
        {"kiwado": ["こんにちは"], "ritsu": 0, "bun": "こんにちはぬーん", "gazou": None}
    ],
})


                    
for _g in settei.values():
    if isinstance(_g, dict) and "hansou" in _g:
        _g.setdefault("hannou", _g.pop("hansou"))
if "hansou" in kotoba:
    kotoba.setdefault("hannou", kotoba.pop("hansou"))


def nuunchanyomu():
    if not nuunchanfile.is_file():
        data = {"users": {}, "ranking": {}}
        kakutext(nuunchanfile, json.dumps(data, ensure_ascii=False, indent=2))
        return data
    try:
        moji = yomutext(nuunchanfile)
        data = json.loads(moji)
        angoumigrate(nuunchanfile, moji)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("users", {})
    data.setdefault("ranking", {})
    for user in data["users"].values():
        if isinstance(user, dict):
            user.pop("kioku", None)
    return data


nuunchan = nuunchanyomu()

def learningexcludeyomu():
    if not learningexcludefile.is_file():
        return []
    try:
        data = json.loads(yomutext(learningexcludefile))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []

def learningexcludekaku(data):
    tmp = learningexcludefile.with_suffix(".tmp")
    kakutext(tmp, json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(learningexcludefile)

learningexclude = learningexcludeyomu()

def learningexcluded(gid, cid=None, tid=None):
    gid, cid, tid = str(gid), str(cid or 0), str(tid or 0)
    for item in learningexclude:
        if str(item.get("g", "")) != gid:
            continue
        xcid = str(item.get("c", "0"))
        xtid = str(item.get("t", "0"))
        if xtid != "0":
            if tid == xtid:
                return True
        elif xcid != "0":
            if cid == xcid:
                return True
        else:
            return True
    return False

def learningtarget(gid, cid, tid):
    return {"g": str(gid), "c": str(cid or 0), "t": str(tid or 0)}


_nuunchan_io = threading.Lock()
_nuunchan_timer = None


def nuunchankaku():
    with _nuunchan_io:
        tmp = nuunchanfile.with_suffix(".tmp")
        kakutext(tmp, json.dumps(nuunchan, ensure_ascii=False, indent=2))
        tmp.replace(nuunchanfile)


def nuunchankaku_later(delay=5.0):

    global _nuunchan_timer
    with _nuunchan_io:
        if _nuunchan_timer is not None:
            return

        def run():
            global _nuunchan_timer
            with _nuunchan_io:
                _nuunchan_timer = None
            try:
                nuunchankaku()
            except Exception as error:
                print(f"nuunchan.json を保存できません: {error}")

        _nuunchan_timer = threading.Timer(delay, run)
        _nuunchan_timer.daemon = True
        _nuunchan_timer.start()


def nuunchanuser(uid):
    uid = str(uid)
    u = nuunchan["users"].setdefault(uid, {})
    u.setdefault("yobikata", "ぬーんちゃん")
    return u


def nuunchanyobikata(uid):
    return nuunchanuser(uid)["yobikata"]


def nuunchanmatch(text, uid):
    name = nuunchanyobikata(uid)
    return name if name and name in text else None


def nuunchanrank(uid, guild_id, amount):
    uid = str(uid)
    guild_id = str(guild_id)
    ranking = nuunchan.setdefault("ranking", {})
    if "global" not in ranking and all(not isinstance(v, dict) for v in ranking.values()):
        ranking = {"global": ranking, "servers": {}}
        nuunchan["ranking"] = ranking
    ranking.setdefault("global", {})
    ranking.setdefault("servers", {})
    ranking["global"][uid] = int(ranking["global"].get(uid, 0)) + int(amount)
    server = ranking["servers"].setdefault(guild_id, {})
    server[uid] = int(server.get(uid, 0)) + int(amount)


def nuunchanrankpos(ranking, uid):
    uid = str(uid)
    rows = sorted(((str(k), int(v)) for k, v in ranking.items()), key=lambda x: (-x[1], x[0]))
    for i, (rid, count) in enumerate(rows, 1):
        if rid == uid:
            return i, count
    return None, 0


async def nuunchanrankname(guild, uid):
    uid = int(uid)
    if guild:
        member = guild.get_member(uid)
        if member:
            return member.display_name
    user = bot.get_user(uid)
    if user:
        return user.display_name
    try:
        user = await bot.fetch_user(uid)
        return user.display_name
    except (discord.NotFound, discord.HTTPException, discord.Forbidden):
        return f"ユーザー{uid}"


async def nuunchanranktext(uid, guild):
    ranking = nuunchan.get("ranking", {})
    if "global" not in ranking and all(not isinstance(v, dict) for v in ranking.values()):
        ranking = {"global": ranking, "servers": {}}
    global_ranking = ranking.get("global", {})
    server_ranking = ranking.get("servers", {}).get(str(guild.id), {}) if guild else {}
    out = []
    for title, data in (("グローバルランキング", global_ranking), ("サーバー内ランキング", server_ranking)):
        out.append(title)
        if not data:
            out.append("まだランキングは始まっていないぬーん")
        else:
            rows = sorted(((str(k), int(v)) for k, v in data.items()), key=lambda x: (-x[1], x[0]))[:10]
            for i, (rid, count) in enumerate(rows, 1):
                out.append(f"{i}位　{await nuunchanrankname(guild, rid)}　{count}ぬーん")
        pos, count = nuunchanrankpos(data, uid)
        if pos is not None:
            out.append(f"あなた　{pos}位　{count}ぬーん")
        else:
            out.append("あなた　ランキング外　0ぬーん")
        out.append("")
    return "\n".join(out).rstrip()


HAIKU = [
    "ぬんぬんぬ、ぬぬぬぬぬぬぬ、ぬーんぬん",
    "ぬーん咲く、今日も元気に、ぬーんする",
    "春のぬーん、夏もぬーんして、秋ぬーん",
    "ぬーんかな、ぬーんじゃないかな、やっぱぬーん",
    "朝ぬーん、昼もぬーんで、夜ぬーん",
]


def nuunchanart(text, uid):
    name = nuunchanmatch(text, uid)
    if not name:
        return None
    body = text.replace(name, "", 1).strip(" 、,，。！？!?　")
    if "俳句" in body:
        return random.choice(HAIKU)
    if body in ("", "呼んだ", "おい", "ねえ", "ねぇ"):
        return "呼んだぬーん？"
    return random.choice([
        "ぬーん！呼んだぬーん？",
        "ぬーんちゃんはここにいるぬーん！",
        "どうしたぬーん？",
    ])


def kaku():
    kakutext(setteifile, json.dumps(settei, ensure_ascii=False, indent=2))


def globalchat_channels():
    data = settei.setdefault("globalchat", {})
    channels = data.setdefault("channels", [])
    if not isinstance(channels, list):
        channels = []
        data["channels"] = channels
    return channels


def globalchat_enabled(channel_id):
    return str(channel_id) in {str(x) for x in globalchat_channels()}


def globalchat_add(channel_id):
    channels = globalchat_channels()
    cid = str(channel_id)
    if cid not in {str(x) for x in channels}:
        channels.append(cid)
        kaku()


def globalchat_remove(channel_id):
    channels = globalchat_channels()
    cid = str(channel_id)
    before = len(channels)
    channels[:] = [x for x in channels if str(x) != cid]
    if len(channels) != before:
        kaku()
        return True
    return False


globalchat_links = {}
globalchat_roots = {}
globalchat_message_channels = {}
globalchat_reaction_lock = set()


def globalchat_root_id(message_id):
    return globalchat_roots.get(message_id, message_id)


def globalchat_clean_mentions(text):
    text = str(text or "")
    text = text.replace("@everyone", "＠everyone").replace("@here", "＠here")
    text = re.sub(r"<@&(\d+)>", lambda m: "＠<@&" + m.group(1) + ">", text)
    return text


async def globalchat_get_message(channel, message_id):
    if not channel:
        return None
    try:
        return await channel.fetch_message(message_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


async def globalchat_build_embeds(message, edited=False, destination=None):
    if not message.content and not message.attachments:
        return []
    name = getattr(message.author, "display_name", message.author.name)
    icon = message.author.display_avatar.url
    body = globalchat_clean_mentions(message.content)
    embed = discord.Embed(description=body[:4096] if body else None)
    embed.set_author(name=name, icon_url=icon)
    if edited:
        embed.set_footer(text="編集済み")

    if message.reference and message.reference.message_id:
        reply = message.reference.resolved
        if not isinstance(reply, discord.Message):
            reply = await globalchat_get_message(message.channel, message.reference.message_id)
        reply_link = None
        reply_name = None
        reply_text = None
        if isinstance(reply, discord.Message):
            reply_name = getattr(reply.author, "display_name", reply.author.name)
            reply_text = globalchat_clean_mentions(reply.content or "添付ファイル")
            reply_root = globalchat_root_id(reply.id)
            if reply.id != reply_root and reply.embeds:
                source_embed = reply.embeds[0]
                if source_embed.author and source_embed.author.name:
                    reply_name = source_embed.author.name
                if source_embed.description:
                    reply_text = globalchat_clean_mentions(source_embed.description)
            reply_text = reply_text.replace("\n", " ").replace("\r", " ").strip()
            if len(reply_text) > 300:
                reply_text = reply_text[:297] + "..."
            if destination is not None:
                if reply.id == reply_root and reply.channel.id == destination.id:
                    reply_link = reply.jump_url
                else:
                    for mapped_id in globalchat_links.get(reply_root, []):
                        if globalchat_message_channels.get(mapped_id) == destination.id:
                            mapped_message = await globalchat_get_message(destination, mapped_id)
                            if mapped_message:
                                reply_link = mapped_message.jump_url
                                break
            if reply_link is None and destination is None:
                reply_link = reply.jump_url
        if reply_link and reply_name is not None and reply_text is not None:
            embed.add_field(
                name="返信先",
                value=f"[{globalchat_clean_mentions(reply_name)}]({reply_link})\n{reply_text}",
                inline=False,
            )

    image_attachments = [
        a for a in message.attachments
        if (a.content_type or "").startswith("image/")
    ]
    if not body and not image_attachments:
        embed.description = "添付ファイル"

    embeds = [embed]
    for attachment in image_attachments[:9]:
        image_embed = discord.Embed()
        image_embed.set_image(url=f"attachment://{attachment.filename}")
        embeds.append(image_embed)
    return embeds


async def globalchat_send(message, destination):
    embeds = await globalchat_build_embeds(message, destination=destination)
    if not embeds:
        return None
    files = []
    for attachment in message.attachments:
        try:
            files.append(await attachment.to_file(use_cached=True))
        except Exception:
            continue
    try:
        sent = await destination.send(
            embeds=embeds,
            files=files,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=False),
        )
    except (discord.HTTPException, discord.Forbidden):
        return None
    globalchat_copy_ids.append(sent.id)
    return sent


globalchat_copy_ids = deque(maxlen=5000)


def globalchat_is_copy(message):


    if message.id in globalchat_copy_ids:
        return True
    if globalchat_roots.get(message.id, message.id) != message.id:
        return True
    if message.author.bot:
        for e in message.embeds:
            if getattr(e, "type", None) == "rich" and e.author and e.author.name:
                return True
    return False


async def globalchat_relay(message):
    if not message.guild or not globalchat_enabled(message.channel.id):
        return
    if message.author.bot and message.author.id != bot.user.id:
        return
    if globalchat_is_copy(message):
        return
    if message.id in globalchat_links:
        return
    targets = []
    for cid in globalchat_channels():
        channel = bot.get_channel(int(cid))
        if isinstance(channel, (discord.TextChannel, discord.Thread)) and channel.id != message.channel.id:
            targets.append(channel)
    if not targets:
        return
    sent_messages = []
    for channel in targets:
        sent = await globalchat_send(message, channel)
        if sent:
            sent_messages.append(sent)
    if sent_messages:
        ids = [message.id] + [m.id for m in sent_messages]
        globalchat_roots[message.id] = message.id
        globalchat_message_channels[message.id] = message.channel.id
        for mid in ids:
            globalchat_roots[mid] = message.id
            globalchat_links[mid] = ids
        for sent in sent_messages:
            globalchat_message_channels[sent.id] = sent.channel.id


async def globalchat_fetch_copy(mid):

    cid = globalchat_message_channels.get(mid)
    if not cid:
        return None
    ch = bot.get_channel(int(cid))
    if not isinstance(ch, (discord.TextChannel, discord.Thread)):
        return None
    return await globalchat_get_message(ch, mid)


async def globalchat_reaction(payload, add=True):
    if not bot.user or payload.user_id == bot.user.id:
        return
    ids = globalchat_links.get(payload.message_id)
    if not ids or payload.message_id in globalchat_reaction_lock:
        return
    key = (payload.message_id, payload.user_id, str(payload.emoji), add)
    if key in globalchat_reaction_lock:
        return
    globalchat_reaction_lock.add(key)
    try:
        for mid in ids:
            if mid == payload.message_id:
                continue
            root = globalchat_root_id(mid)
            if root != globalchat_root_id(payload.message_id):
                continue
            target = await globalchat_fetch_copy(mid)
            if not target:
                continue
            try:
                if add:
                    await target.add_reaction(payload.emoji)
                else:
                    await target.remove_reaction(payload.emoji, bot.user)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass
    finally:
        globalchat_reaction_lock.discard(key)


async def globalchat_edit(message):
    root = globalchat_root_id(message.id)
    ids = globalchat_links.get(root)
    if not ids or message.id != root:
        return
    if not message.guild:
        return
    embeds_by_channel = {}
    if not globalchat_links.get(root):
        return
    files = []
    for attachment in message.attachments:
        try:
            files.append(await attachment.to_file(use_cached=True))
        except Exception:
            continue
    for mid in ids:
        if mid == root:
            continue
        target = await globalchat_fetch_copy(mid)
        if not target:
            continue
        try:
            embeds = await globalchat_build_embeds(message, edited=True, destination=target.channel)
            if not embeds:
                continue
            await target.edit(embeds=embeds, attachments=files, allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=False))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


async def globalchat_delete(message):
    root = globalchat_root_id(message.id)
    ids = globalchat_links.get(root)
    if not ids or message.id != root:
        return
    for mid in ids:
        if mid == root:
            continue
        target = await globalchat_fetch_copy(mid)
        if not target:
            continue
        try:
            await target.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass
    for mid in ids:
        globalchat_links.pop(mid, None)
        globalchat_roots.pop(mid, None)
        globalchat_message_channels.pop(mid, None)


def saba(x):
    d = settei.setdefault(str(x.guild.id), {"banpu": True, "hannou": {}})
    d.setdefault("banpu", True)
    if not isinstance(d.get("hannou"), dict):
        d["hannou"] = {}
    return d


def han(x):
    d = saba(x)["hannou"]
    ch = x.channel
    if str(ch.id) in d:
        return d[str(ch.id)]
    if isinstance(ch, discord.Thread) and isinstance(ch.parent, discord.ForumChannel):
        return d.get(str(ch.parent_id), False)
    return False


def onofu(b):
    return "オン" if b else "オフ"


def pasento(v):
    try:
        return None if v is None else max(0, min(100, int(v)))
    except (TypeError, ValueError):
        return None


def ritsukojin(x):

    hito = getattr(x, "user", None) or x.author
    return pasento(saba(x).get("ritsu_kojin", {}).get(str(hito.id)))


def ritsumoji(x):

    v = ritsukojin(x)
    return 30 if v is None else v


def ritsusetsu(x):
    v = ritsukojin(x)
    if v is None:
        return "個人返信確率は30パーセント（未設定時の標準値）"
    return f"個人返信確率は{v}パーセント"


def dashi(r):
    k = {}
    if r.get("bun"):
        k["content"] = r["bun"]
    path = deeta / r["gazou"] if r.get("gazou") else None
    if path and path.is_file():
        k["file"] = discord.File(path)
    return k


async def okuru(heya, r):
    k = dashi(r)
    if k:
        await heya.send(**k)


def hiku():
    if not kotoba.get("gacha"):
        return {"content": "ガチャが設定されていないぬーん"}
    entries = [(name, item) for name, item in kotoba["gacha"].items() if isinstance(item, dict)]
    if not entries:
        return {"content": "ガチャの設定が正しくないぬーん"}
    names = [name for name, _ in entries]
    weights = []
    for _, item in entries:
        try:
            weights.append(max(0.0, float(item.get("ritsu", 1))))
        except (TypeError, ValueError):
            weights.append(0.0)
    if not any(weights):
        weights = [1.0] * len(entries)
    na = random.choices(names, weights=weights, k=1)[0]
    return dashi(dict(kotoba["gacha"][na])) or {"content": f"{na}ぬーん"}


nuun_voice_pat = r"[ぬヌ][ーｰ〜~ぅぉおぁぃぇっゥォオァィェッ]*[んン]|[Nn][Uu]+[Nn]"
nuun_teikei_pat = (
    r"(?:おはよう(?:ございます|ございました)|おはよう|おはよ[ーｰ〜~ぉぅ]*|こんにちは|こんにちわ|こんばんは|こんばんわ|"
    r"ありがとうございます|ありがとうございました|ありがとう|ありがと|おやすみなさい|おやすみ|さようなら|"
    r"ただいま|おかえりなさい|おかえり|いただきます|ごちそうさまでした|ごちそうさま|はじめまして|"
    r"よろしくお願いします|よろしくおねがいします|よろしく|お疲れ様でした|お疲れ様です|お疲れ様|"
    r"おつかれさまでした|おつかれさまです|おつかれさま|おつかれ|すみません|ごめんなさい|ごめん|"
    r"いってきます|いってらっしゃい)[ーｰ〜~]*"
)
nuun_special_re = re.compile(rf"(?P<n>{nuun_voice_pat})|(?P<f>{nuun_teikei_pat})")
nuunrank_re = re.compile(nuun_voice_pat)
nuun_kuten = "、。！？!?…~〜"
nuun_kinou_dousi = {"する", "いる", "ある", "なる", "できる", "れる", "られる", "くる", "おる", "しまう"}
_nuun_joshi_re = re.compile(r"から|まで|より|だけ|しか|ほど|など|では|には|とは|でも|のに|ので|って|は|が|を|に|で|と|も|の|へ|や")
_nuun_shujoshi_re = re.compile(r"(?:だよね|だよ|だね|よね|かな|よ|ね|な|わ|ぞ|ぜ|さ|か)$")
_nuun_run_re = re.compile(r"[一-龥々〆ヵヶ]+|[ぁ-ん]+|[ァ-ヴー]+|[A-Za-z0-9Ａ-Ｚａ-ｚ０-９]+|[、。！？!?…~〜]+|.", re.S)


def nuun_keitaiso(chunk):
    tok = get_tokenizer()
    if tok is None:
        return None
    try:
        out = []
        for t in tok.tokenize(chunk):
            pos = str(t.part_of_speech).split(",")
            out.append((t.surface, pos[0], pos[1] if len(pos) > 1 else "*",
                        str(getattr(t, "base_form", "") or ""), str(getattr(t, "node_type", "")) == "UNKNOWN"))
    except Exception:
        return None
    if sum(len(m[0]) for m in out) != len(chunk):
        return None
    return out


def _nuun_ketsugou(ms):
    groups = []
    for surf, p1, p2, base, _unk in ms:
        g = groups[-1] if groups else None
        join = False
        if g is not None:
            q1, q2 = g["p"][-1][0], g["p"][-1][1]
            has_yogen = any(x[0] in ("動詞", "形容詞") for x in g["p"])
            if q1 == "接頭詞":
                join = p1 not in ("記号", "助詞")
            elif p1 == "記号":
                join = all(c in nuun_kuten for c in surf) and all(c in nuun_kuten for c in g["s"])
            elif p1 == "助詞" and p2 == "接続助詞":
                join = has_yogen and q1 in ("動詞", "形容詞", "助動詞")
            elif p1 == "助動詞":
                join = q1 in ("動詞", "形容詞", "助動詞")
            elif p1 in ("動詞", "形容詞") and p2 in ("非自立", "接尾"):
                join = has_yogen and q1 in ("動詞", "形容詞", "助動詞", "助詞")
            elif p1 == "動詞" and base == "する" and q1 == "名詞" and q2 == "サ変接続":
                join = True
            elif p1 == "名詞" and q1 == "名詞":
                join = p2 != "代名詞" and q2 not in ("代名詞", "副詞可")
        if join:
            g["s"] += surf
            g["p"].append((p1, p2, base))
        else:
            groups.append({"s": surf, "p": [(p1, p2, base)]})
    return groups


def _nuun_shurui(g):
    ps = g["p"]
    if all(p[0] == "記号" for p in ps):
        return "sym"
    for p1, p2, base in ps:
        if p1 == "名詞" and p2 not in ("代名詞", "非自立", "数", "接尾", "特殊"):
            return "word"
        if p1 in ("動詞", "形容詞") and p2 == "自立" and base not in nuun_kinou_dousi:
            return "word"
        if p1 in ("副詞", "感動詞", "連体詞"):
            return "word"
    return "func"


def _nuun_hira_naiyou(u):
    return any(len(p) >= 2 for p in chishiki_kinou.sub(" ", u).split())


def _nuun_hira_unit(u, pos, toks):
    for part in re.split(r"(を)", u):
        if not part:
            continue
        if part == "を":
            toks.append((part, "func", pos))
        else:
            ms = _nuun_shujoshi_re.search(part)
            core, tail = (part[:ms.start()], part[ms.start():]) if ms and ms.start() >= 2 else (part, "")
            if core:
                toks.append((core, "word" if _nuun_hira_naiyou(core) else "func", pos))
            if tail:
                toks.append((tail, "func", pos + len(core)))
        pos += len(part)


def _nuun_hiragana(r, s, toks):
    prev = toks[-1] if toks else None
    adj = prev is not None and prev[2] + len(prev[0]) == s
    rest, pos = r, s
    if adj and prev[1] == "word":
        m = _nuun_joshi_re.match(rest)
        if m:
            while rest:
                m = _nuun_joshi_re.match(rest)
                if not m:
                    break
                toks.append((m.group(), "func", pos))
                pos += len(m.group())
                rest = rest[len(m.group()):]
        elif _moji_kind(prev[0][-1]) == "k":
            ms = _nuun_shujoshi_re.search(rest)
            okuri, tail = (rest[:ms.start()], rest[ms.start():]) if ms and (ms.start() > 0 or rest != "な") else (rest, "")
            toks[-1] = (prev[0] + okuri, "word", prev[2])
            pos += len(okuri)
            if tail:
                toks.append((tail, "func", pos))
            return
    if rest:
        _nuun_hira_unit(rest, pos, toks)


def _nuun_fallback(seg, off, toks, spans):
    for m in _nuun_run_re.finditer(seg):
        r, s = m.group(), off + m.start()
        c = r[0]
        if c in "ーｰ":
            if toks and toks[-1][2] + len(toks[-1][0]) == s:
                toks[-1] = (toks[-1][0] + r, toks[-1][1], toks[-1][2])
            else:
                toks.append((r, "sym", s))
            continue
        k = _moji_kind(c)
        if k in ("k", "a", "l"):
            toks.append((r, "word", s))
            if len(r) >= 2:
                spans.append((s, s + len(r)))
        elif k == "o":
            toks.append((r, "sym", s))
        else:
            _nuun_hiragana(r, s, toks)


def _nuun_seg(seg, off, toks, spans):
    ms = nuun_keitaiso(seg)
    if ms is None:
        _nuun_fallback(seg, off, toks, spans)
        return
    p = off
    for surf, p1, p2, base, unk in ms:
        if not unk and len(surf) >= 2 and p1 not in ("記号", "助詞", "助動詞"):
            spans.append((p, p + len(surf)))     
        p += len(surf)
    pos = off
    for g in _nuun_ketsugou(ms):
        toks.append((g["s"], _nuun_shurui(g), pos))
        pos += len(g["s"])


@functools.lru_cache(maxsize=20000)
def _nuun_wakachi_full(text, use_morph):
    toks, spans = [], []
    for cm in re.finditer(r"\S+", text):
        chunk, off, last = cm.group(), cm.start(), 0
        for m in nuun_special_re.finditer(chunk):
            if m.start() > last:
                _nuun_seg(chunk[last:m.start()], off + last, toks, spans)
            if m.group("n"):
                toks.append((m.group(), "nuun", off + m.start()))
            else:
                toks.append((m.group(), "fixed", off + m.start()))
                spans.append((off + m.start(), off + m.end()))
            last = m.end()
        if last < len(chunk):
            _nuun_seg(chunk[last:], off + last, toks, spans)
    return tuple(toks), tuple(spans)


def nuun_wakachi(text):
    return list(_nuun_wakachi_full(str(text or ""), get_tokenizer() is not None)[0])


def nuun_goi(text, whole=True):
    raw = re.sub(r"<a?:\w+:\d+>|<@!?\d+>|<#\d+>|<@&\d+>|https?://\S+", " ", str(text or ""))
    toks = nuun_wakachi(raw)
    morph = get_tokenizer() is not None
    out = []

    def add(w):
        n = SharedMemory.normalize(w)
        if not n or re.fullmatch(r"[0-9０-９]+|[wｗ]+", n):
            return
        if len(n) < 2 and not re.fullmatch(r"[一-龥々〆]", n):
            return
        if w not in out:
            out.append(w)

    for w, kind, _ in toks:
        if kind == "fixed":
            add(w)
        elif kind == "word":
            if not morph and re.fullmatch(r"[ぁ-んー]+", w):
                core = w
                while True:     
                    m = chishiki_kinou.match(core)
                    if m and len(core) - m.end() >= 2:
                        core = core[m.end():]
                    else:
                        break
                if len(core) >= 3:
                    core = re.sub(r"[はがをにでともへやの]$", "", core)
                if core not in chishiki_tomeru:
                    add(core)
            else:
                add(w)
    if whole:
        plain = re.sub(r"[\s、。！？!?…~〜]+", "", raw)
        n_tok = sum(1 for _, k, _s in toks if k in ("word", "func", "fixed"))
        if 2 <= len(plain) <= 10 and n_tok >= 2 and plain not in out and re.fullmatch(r"[ぁ-んァ-ヴー一-龥々〆A-Za-z0-9]+", plain):
            out.append(plain)
    return out[:40]


def nuun_kyokai_ok(text, pos):
    try:
        spans = _nuun_wakachi_full(str(text or ""), get_tokenizer() is not None)[1]
    except Exception:
        return True
    return not any(s < pos < e for s, e in spans)


class SharedMemory:

    
    def __init__(self):
        self.path = deeta / "memory.json"
        self.sentences = []
        self.counts = {}
        self.relations = {}
        self.vocab = {}
        self.source_relations = {}
        self.source_vocab = {}
        has_source_tracking = False
        self.turns = []
        self.facts = []
        self.facts_removed = 0      
        self.alias_groups = []
        self.alias_by = {}                                                 
        self.alias_base = None                                     
        self.vocab_ver = 2          
        self.dirty = 0
        self.save_lock = threading.Lock()
        self.save_state = threading.Lock()
        self.save_busy = False
        self.save_again = False
        try:
            data = json.loads(yomutext(self.path)) if self.path.is_file() else {}
            if isinstance(data, dict):
                self.sentences = data.get("sentences", [])
                self.counts = data.get("counts", {})
                self.relations = data.get("relations", {})
                self.vocab = data.get("vocab", {})
                self.source_relations = data.get("source_relations", {})
                self.source_vocab = data.get("source_vocab", {})
                has_source_tracking = "source_relations" in data and "source_vocab" in data
                self.turns = data.get("turns", [])
                self.facts = data.get("facts", [])
                self.alias_groups = data.get("alias_groups", [])
                self.alias_by = data.get("alias_by", {})
                self.alias_base = data.get("alias_base")
                _vv = data.get("vocab_ver", 1)
                self.vocab_ver = _vv if isinstance(_vv, int) else 1
                if "vocab" not in data:
                    self.vocab_ver = 2
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
        if not isinstance(self.sentences, list):
            self.sentences = []
        if not isinstance(self.counts, dict):
            self.counts = {}
        if not isinstance(self.relations, dict):
            self.relations = {}
        if not isinstance(self.vocab, dict):
            self.vocab = {}
        self.vocab = {str(k): max(0, int(v)) for k, v in self.vocab.items() if isinstance(k, str)}
        if not isinstance(self.source_relations, dict):
            self.source_relations = {}
        if not isinstance(self.source_vocab, dict):
            self.source_vocab = {}
        cleaned_source_relations = {}
        for location, rows in self.source_relations.items():
            if not isinstance(location, str) or not isinstance(rows, dict):
                continue
            clean_rows = {}
            for left, rights in rows.items():
                if not isinstance(left, str) or not isinstance(rights, dict):
                    continue
                clean_rows[left] = {str(right): max(0, int(count)) for right, count in rights.items() if isinstance(right, str)}
            if clean_rows:
                cleaned_source_relations[location] = clean_rows
        self.source_relations = cleaned_source_relations
        self.source_vocab = {
            str(location): {str(word): max(0, int(count)) for word, count in words.items() if isinstance(word, str)}
            for location, words in self.source_vocab.items()
            if isinstance(location, str) and isinstance(words, dict)
        }
        legacy_untracked = self.path.is_file() and not has_source_tracking
        if legacy_untracked:
            self.relations = {}
            self.vocab = {}
            self.source_relations = {}
            self.source_vocab = {}
            self.vocab_ver = 2
        if not isinstance(self.turns, list):
            self.turns = []
        if not isinstance(self.facts, list):
            self.facts = []
        if not isinstance(self.alias_groups, list):
            self.alias_groups = []
        self.alias_groups = self._clean_alias_groups(self.alias_groups)
        if not isinstance(self.alias_by, dict):
            self.alias_by = {}
        self.alias_by = {
            str(u): [[str(x) for x in parts] for parts in rows if isinstance(parts, list)]
            for u, rows in self.alias_by.items()
            if isinstance(rows, list)
        }
        if isinstance(self.alias_base, list):
            self.alias_base = self._clean_alias_groups(self.alias_base)
        else:
            self.alias_base = [list(g) for g in self.alias_groups]
        self.facts = [
            {
                "s": x["s"] if isinstance(x.get("s"), str) else "",
                "t": x["t"],
                "g": x["g"] if isinstance(x.get("g"), int) else 0,
                "by": [u for u in x.get("by", []) if isinstance(u, int)][-5:],
                "x": 1 if x.get("x") else 0,
            }
            for x in self.facts
            if isinstance(x, dict) and isinstance(x.get("t"), str) and x["t"].strip()
        ]
        for f in self.facts:
            f.setdefault("c", 0)
            f.setdefault("d", 0)
        self.sentences = [str(x) for x in self.sentences if isinstance(x, str)]
        self.turns = [x for x in self.turns if isinstance(x, dict) and isinstance(x.get("q"), str) and isinstance(x.get("a"), str)]
        
        self.sentences = [x for x in self.sentences if not is_gibberish(x)]
        self.counts = {k: v for k, v in self.counts.items() if not is_gibberish(k)}
        self.turns = [x for x in self.turns if not (is_gibberish(x["q"]) or is_gibberish(x["a"]))]
        self.facts = [x for x in self.facts if not is_gibberish(x["t"])]
        auto_facts = [x for x in self.facts if not x.get("x")]
        migrated = bool(self.sentences or self.counts or self.turns or auto_facts or legacy_untracked)
        self.sentences = []
        self.counts = {}
        self.turns = []
        self.facts = [x for x in self.facts if x.get("x")]
        self.facts_removed += len(auto_facts)
        self.chishiki_kouchiku()
        if migrated:
            self.dirty = 1
            self.save()

    
    @staticmethod
    def normalize(text):
        text = str(text or "").casefold()
        text = re.sub(r"<@!?\d+>|<#\d+>|<@&\d+>", "", text)
        text = re.sub(r"[\s　、。,.，．!！?？…~〜:：;；]+", "", text)
        return text.strip("『』「」\"'()（）")

    
    @staticmethod
    def terms(text):
        text = SharedMemory.normalize(text)
        found = re.findall(r"[一-龥々〆ヵヶ]+|[ぁ-ん]+|[ァ-ヴー]+|[a-z0-9]+", text)
        terms = []
        for term in found:
            if len(term) >= 2 and term not in terms:
                terms.append(term)
            if len(term) >= 4:
                for i in range(len(term) - 1):
                    part = term[i:i + 2]
                    if part not in terms:
                        terms.append(part)
        for i in range(len(text) - 1):
            part = text[i:i + 2]
            if part not in terms and not part.isspace():
                terms.append(part)
        return terms[:30]

    
    @staticmethod
    def grams(text):
        text = SharedMemory.normalize(text)
        if len(text) < 2:
            return {text} if text else set()
        return {text[i:i + 2] for i in range(len(text) - 1)}

    
    @staticmethod
    def source_key(source):
        if source is None:
            return None
        if isinstance(source, str):
            return source
        try:
            gid, cid, tid, *rest = source
            key = f"{int(gid)}:{int(cid or 0)}:{int(tid or 0)}"
            if rest and rest[0]:
                owners = rest[0] if isinstance(rest[0], (list, tuple, set)) else [rest[0]]
                owners = sorted({int(x) for x in owners if x})
                if owners:
                    key += ":" + "+".join(str(x) for x in owners)
            return key
        except (TypeError, ValueError):
            return None

    
    @staticmethod
    def source_matches(location, gid, cid=0, tid=0):
        try:
            parts = str(location).split(":")
            if len(parts) not in (3, 4):
                return False
            lg, lc, lt = (int(x) for x in parts[:3])
        except (TypeError, ValueError):
            return False
        if lg != int(gid):
            return False
        if tid:
            return lt == int(tid)
        if cid:
            return lc == int(cid)
        return True

    
    @staticmethod
    def with_owner(source, *uids):

        if not isinstance(source, (tuple, list)):
            return source
        try:
            gid, cid, tid, *_ = source
        except ValueError:
            return source
        owners = sorted({int(u) for u in uids if u})
        return (gid, cid, tid, owners) if owners else (gid, cid, tid)

    @staticmethod
    def source_owners(location):
        parts = str(location).split(":")
        if len(parts) != 4:
            return set()
        try:
            return {int(x) for x in parts[3].split("+") if x}
        except ValueError:
            return set()

    @staticmethod
    def source_has_owner(location, uid):
        try:
            return int(uid) in SharedMemory.source_owners(location)
        except (TypeError, ValueError):
            return False

    def add_relation(self, left, right, source_key=None, count=1):
        row = self.relations.setdefault(left, {})
        row[right] = min(100000, int(row.get(right, 0)) + int(count))
        if source_key:
            source_rows = self.source_relations.setdefault(source_key, {})
            source_row = source_rows.setdefault(left, {})
            source_row[right] = min(100000, int(source_row.get(right, 0)) + int(count))

    
    def learn(self, text, store_sentence=False, source=None):
        cleaned = str(text or "").strip()
        normalized = self.normalize(cleaned)
        if len(normalized) < 2:
            return
        if not store_sentence and self.source_key(source) is None:
            return
        if is_gibberish(cleaned):
            return
        if store_sentence:
            if cleaned in self.counts:
                self.counts[cleaned] = int(self.counts.get(cleaned, 0)) + 1
            else:
                self.counts[cleaned] = 1
                self.sentences.append(cleaned)
        terms = self.terms(cleaned)
        source_key = self.source_key(source)
        for i, left in enumerate(terms):
            for right in terms[i + 1:]:
                if left != right:
                    self.add_relation(left, right, source_key)
                    self.add_relation(right, left, source_key)
        if store_sentence and len(self.sentences) > 12000:
            self.sentences = self.sentences[-12000:]
            keep = set(self.sentences)
            self.counts = {k: v for k, v in self.counts.items() if k in keep}
        if len(self.relations) > 20000:
            self.relations = dict(sorted(self.relations.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:16000])
        self.dirty += 1
        if self.dirty >= 20:
            self.save_async()

    
    def learn_turn(self, question, answer, source=None, q_uid=None, a_uid=None):
        if self.source_key(source) is None:
            return
        q = str(question or "").strip()
        a = str(answer or "").strip()
        if len(self.normalize(q)) < 2 or len(self.normalize(a)) < 2:
            return
        if self.normalize(q) == self.normalize(a) or is_gibberish(q) or is_gibberish(a):
            return
        self.learn(q, store_sentence=False, source=self.with_owner(source, q_uid))
        self.learn(a, store_sentence=False, source=self.with_owner(source, a_uid))
        source_key = self.source_key(self.with_owner(source, q_uid, a_uid))                     
        left_terms = self.terms(q)
        right_terms = self.terms(a)
        for left in left_terms:
            for right in right_terms:
                if left == right:
                    continue
                self.add_relation(left, right, source_key)
                self.add_relation(right, left, source_key)
        self.dirty += 1

    
    def related_terms(self, text, limit=8):
        scores = {}
        query_terms = set(self.terms(text))
        for term in query_terms:
            for related, count in self.relations.get(term, {}).items():
                if related not in query_terms:
                    scores[related] = scores.get(related, 0) + int(count)
        ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return [term for term, _ in ordered[:max(1, min(int(limit), 20))]]

    
    def similarity(self, query, candidate):
        qn, cn = self.normalize(query), self.normalize(candidate)
        if not qn or not cn:
            return 0.0
        if qn == cn:
            return 1.0
        if cn.startswith(qn):
            return 0.92 + min(0.07, (len(cn) - len(qn)) / 1000)
        if qn in cn:
            return 0.82
        qt, ct = set(self.terms(query)), set(self.terms(candidate))
        overlap = len(qt & ct) / max(1, len(qt | ct))
        qg, cg = self.grams(query), self.grams(candidate)
        gram = len(qg & cg) / max(1, len(qg | cg))
        related = 0.0
        if qt and ct:
            best = 0.0
            for token in qt:
                row = self.relations.get(token, {})
                total = sum(int(v) for v in row.values())
                if not total:
                    continue
                for other in ct:
                    count = int(row.get(other, 0))
                    if count:
                        best = max(best, min(1.0, count / max(3, total * 0.25)))
            related = best
        return overlap * 0.45 + gram * 0.45 + related * 0.10

    
    def query_variants(self, question):
        normalized = self.normalize(question)
        variants = [normalized]
        endings = (
            r"ってどんな(?:感じ|もの|人|やつ)?$", r"とはどんな(?:感じ|もの|人|やつ)?$",
            r"って何(?:者|ですか|なの|なのか)?$", r"とは何(?:者|ですか|なの|なのか)?$",
            r"ってなに(?:者|ですか|なの)?$", r"とはなに(?:者|ですか|なの)?$",
            r"はどんな(?:感じ|もの|人|やつ)?$", r"は誰(?:ですか|なの)?$",
            r"は何(?:者|ですか|なの|なのか)?$", r"について教えて$",
            r"について$", r"とは$", r"って$", r"ってどういうこと$",
            r"どんな感じ$", r"教えて$", r"知ってる$", r"なに$", r"何$", r"誰$",
        )
        for pattern in endings:
            shortened = re.sub(pattern, "", normalized)
            if len(shortened) >= 2 and shortened not in variants:
                variants.append(shortened)
        return variants

    
    def query_similarity(self, question, candidate):
        return max(self.similarity(q, candidate) for q in self.query_variants(question))

    
    def recall(self, question, context=None):
        return None

    
    def retrieve_evidence(self, question, context=None, limit=5):

        query = str(question or "").strip()
        query_norm = self.normalize(query)
        if len(query_norm) < 2:
            return []

        found = []
        seen = set()

        
        for item in self.turns[-3000:]:
            source_question = str(item.get("q", "")).strip()
            qscore = self.query_similarity(query, source_question)
            cscore = self.query_similarity(context, source_question) if context else 0.0
            
            score = qscore * 0.90 + cscore * 0.04
            answer = str(item.get("a", "")).strip()
            key = self.normalize(answer)
            if answer and key not in seen and qscore >= 0.52 and score >= 0.50:
                found.append({"score": score, "text": answer, "source": source_question, "kind": "turn"})
                seen.add(key)

        
        for sentence in self.sentences[-6000:]:
            sentence = str(sentence).strip()
            key = self.normalize(sentence)
            if not key or key == query_norm or key in seen or len(key) < 3:
                continue
            score = self.query_similarity(query, sentence)
            if context:
                score = score * 0.96 + self.query_similarity(context, sentence) * 0.04
            
            if score >= 0.48:
                found.append({"score": score, "text": sentence, "source": "", "kind": "sentence"})
                seen.add(key)

        
        found.sort(key=lambda x: x["score"], reverse=True)
        selected = []
        selected_grams = []
        for item in found:
            grams = self.grams(item["text"])
            if any(len(grams & old) / max(1, len(grams | old)) > 0.78 for old in selected_grams):
                continue
            selected.append(item)
            selected_grams.append(grams)
            if len(selected) >= max(1, min(int(limit), 5)):
                break
        return selected

    
    
    @staticmethod
    def _clean_alias_groups(groups):
        out = []
        seen = set()
        if not isinstance(groups, list):
            return out
        for group in groups:
            if not isinstance(group, list):
                continue
            vals = []
            for x in group:
                x = SharedMemory.normalize(x)
                if len(x) < 2 or x in chishiki_tomeru or x in vals:
                    continue
                vals.append(x)
            vals.sort(key=lambda x: (-len(x), x))
            key = tuple(vals)
            if len(vals) >= 2 and key not in seen:
                seen.add(key)
                out.append(vals[:20])
        return out[:50000]

    @staticmethod
    def _alias_parts(text):
        t = re.sub(r"[。！？!?…~〜]+", " ", str(text or "").strip())
        t = re.sub(r"(?:というのは|っていうのは|ってのは|とは|って|と呼ぶ|と呼ばれる|と呼んで|のことを|のことは|のこと)", " ", t)
        raw = re.split(r"[\s、,，:：]+|\s*と\s*", t)
        vals = []
        for x in raw:
            x = SharedMemory.normalize(x)
            if len(x) >= 2 and x not in chishiki_tomeru and x not in vals and len(x) <= 30:
                vals.append(x)
        return vals[:10]

    @staticmethod
    def _alias_union(groups, parts):

        hit = [g for g in groups if any(x in g for x in parts)]
        merged = []
        for g in hit:
            for x in g:
                if x not in merged:
                    merged.append(x)
        for x in parts:
            if x not in merged:
                merged.append(x)
        if len(merged) < 2:
            return groups, False
        rest = [g for g in groups if not any(x in g for x in merged)]
        rest.append(sorted(set(merged), key=lambda x: (-len(x), x))[:20])
        return rest, True

    def _alias_record(self, owner, parts):
        rows = self.alias_by.setdefault(owner, [])
        if parts not in rows:
            rows.append(list(parts))
            if len(rows) > 5000:
                                                                   
                self.alias_base, _ = self._alias_union(self.alias_base, rows.pop(0))

    def alias_rebuild(self):

        groups = [list(g) for g in self.alias_base]
        for rows in self.alias_by.values():
            for parts in rows:
                groups, _ = self._alias_union(groups, parts)
        self.alias_groups = self._clean_alias_groups(groups)

    def chishiki_alias_manabu(self, text, uid=None):
        t = re.sub(r"\s+", " ", str(text or "")).strip()
        if not t:
            return 0
        patterns = (
            r"^(.{2,30}?)(?:というのは|っていうのは|ってのは|とは)(.{2,30})$",
            r"^(.{2,30}?)(?:という|って)(.{2,30})$",
            r"^(.{2,30}?)(?:と呼ぶ|と呼ばれる|と呼んで)(.{2,30})$",
            r"^(.{2,30}?)(?:のことを|のことは)(.{2,30})$",
            r"^(.{2,30}?)[はが](.{2,30})$",
        )
        pairs = []
        for pat in patterns:
            m = re.match(pat, t)
            if m:
                a, b = m.group(1).strip(), m.group(2).strip()
                parts = []
                for x in re.split(r"\s*(?:、|,|，|\s+と\s+)\s*", b):
                    x = re.sub(r"^[、,，:：\s]+|[。！？!?…~〜\s]+$", "", x).strip()
                    if len(x) >= 2:
                        parts.append(x)
                parts = [a] + parts
                parts = [SharedMemory.normalize(x) for x in parts]
                parts = [x for x in parts if len(x) >= 2 and x not in chishiki_tomeru]
                if len(parts) >= 2:
                    pairs.append(parts)
                break
        if not pairs:
            parts = self._alias_parts(t)
            if len(parts) >= 2 and len(parts) <= 6:
                pairs.append(parts)
        changed = False
        owner = str(int(uid)) if uid else None
        for parts in pairs:
            groups, ok = self._alias_union(self.alias_groups, parts)
            if not ok:
                continue
            self.alias_groups = groups
            changed = True
            if owner:
                self._alias_record(owner, parts)
            else:
                self.alias_base, _ = self._alias_union(self.alias_base, parts)                 
        if changed:
            self.alias_groups = self._clean_alias_groups(self.alias_groups)
            self.dirty += 1
        return 1 if changed else 0

    def chishiki_alias_hitto(self, text):
        q = self.normalize(text)
        if not q:
            return []
        hits = []
        for group in self.alias_groups:
            matched = [x for x in group if x and x in q]
            if matched:
                hits.append(group)
        hits.sort(key=lambda g: max(len(x) for x in g if x in q), reverse=True)
        return hits[:8]

    chishiki_gimon = (
        r"(?:何者|なにもの|何|なに|なん|誰|だれ|どこ|いつ|どんな(?:もの|人|感じ|やつ|の)?|どういう(?:もの|人|こと|意味|やつ)?|どう|意味|"
        r"について(?:教えて(?:くれ|ください|ほしい)?)?|教えて(?:くれ|ください|ほしい)?|知ってる|しってる|知ってますか|わかる|分かる|"
        r"ですか|ますか|でしょうか|のか|なのか|かな|だっけ|っけ)"
    )
    chishiki_gimon_end = r"(?:なの|なん|なんだ|だ|です|の|ん|よ|ね|さ|ぞ|や|か)*"
    chishiki_joshi_re = r"(?:というのは|っていうのは|ってのは|とは|って|のこと|こと|について|は|が|を|も|の)+"

    
    @staticmethod
    def chishiki_wadai(text):

        t = SharedMemory.normalize(text)
        t2 = re.sub(SharedMemory.chishiki_gimon + SharedMemory.chishiki_gimon_end + "$", "", t)
        asked = t2 != t
        t3 = re.sub(SharedMemory.chishiki_joshi_re + "$", "", t2)
        
        return (t3 if (len(t3) >= 2 or re.fullmatch(r"[一-龥々〆]", t3)) else t2), asked

    chishiki_sep_re = re.compile(r"っていうのは|というのは|ってのは|とは|って|は|が|＝|=|：|:")

    
    @staticmethod
    def chishiki_bunkai(t):

        t = str(t or "")
        for i in range(1, min(len(t), 20) + 1):
            m = SharedMemory.chishiki_sep_re.match(t, i)
            if not m:
                continue
            tail = t[m.end():]
            if not tail:
                continue
            if re.fullmatch(r"[ぁ-ん]+", t[:i]) and not nuun_kyokai_ok(t, i):
                continue        
            subject = SharedMemory.normalize(t[:i])
            if len(subject) < 2 and not re.fullmatch(r"[一-龥々〆]", subject):
                continue        
            if subject in chishiki_tomeru:
                return "", t
            rest = tail.lstrip(" \t　、,，") or tail[-1:]
            return subject, rest.strip()
        return "", t

    
    @staticmethod
    def chishiki_shudai(text):

        return SharedMemory.chishiki_bunkai(str(text or "").strip())

    def chishiki_renkei(self, text):
        t = re.sub(r"\s+", " ", str(text or "")).strip()
        if not t:
            return []
        a, rest = self.chishiki_bunkai(t)
        if not a:
            return []
        parts = [a]
        for x in re.split(r"\s*(?:=|＝)\s*", rest):
            x = re.sub(r"^[、,，:：\s]+|[。！？!?…~〜\s]+$", "", x).strip()
            x = self.normalize(x)
            if len(x) >= 1 and x not in parts and x not in chishiki_tomeru:
                parts.append(x)
        return parts if len(parts) >= 2 else []

    def chishiki_hitto(self, text):
        q = self.normalize(text)
        if not q:
            return []
        hits = []
        seen = set()
        for group in self.chishiki_alias_hitto(q):
            for f in self.facts:
                chain = self.chishiki_renkei(f.get("t", ""))
                if not chain:
                    continue
                if any(any(alias in self.normalize(part) for alias in group) for part in chain):
                    key = id(f)
                    if key in seen:
                        continue
                    seen.add(key)
                    hits.append(chain)
        for f in self.facts:
            chain = self.chishiki_renkei(f.get("t", ""))
            if len(chain) < 2:
                continue
            if chain[0] in q and id(f) not in seen:
                seen.add(id(f))
                hits.append(chain)
        return hits[:20]

    
    @staticmethod
    def chishiki_shitsumon(text):
        t = str(text or "").strip()
        if re.search(r"[?？]", t):
            return True
        return SharedMemory.chishiki_wadai(t)[1]

    
    @staticmethod
    def chishiki_goi(text):

        t = str(text or "").casefold()
        t = re.sub(r"<@!?\d+>|<#\d+>|<@&\d+>|https?://\S+", " ", t)
        t = re.sub(r"[wｗ]{2,}", " ", t)
        out = []

        
        def add(x):
            if x not in out:
                out.append(x)

        for run in re.findall(r"[一-龥々〆ヵヶ]+|[ぁ-ん][ぁ-んー]*|[ァ-ヴ][ァ-ヴー]*|[a-z0-9]+", t):
            if run in chishiki_tomeru:
                continue
            if re.fullmatch(r"[ぁ-ん][ぁ-んー]*", run):
                for piece in chishiki_kinou.sub(" ", run).split():
                    if len(piece) >= 3:
                        piece = re.sub(r"[はがをにでともへやの]$", "", piece)
                    if len(piece) >= 2 and piece not in chishiki_tomeru:
                        add(piece)
                continue
            add(run)
            if len(run) >= 3 and re.fullmatch(r"[一-龥々〆ヵヶ]+", run):
                for i in range(len(run) - 1):
                    add(run[i:i + 2])
        return out[:60]

    
    def chishiki_kouchiku(self):

        self.chishiki_idx = {}
        self.chishiki_keys = {}
        self.chishiki_terms = {}
        self.chishiki_shu = {}
        for f in self.facts:
            self._chishiki_toroku(f)

    
    def _chishiki_toroku(self, f):
        terms = set(self.chishiki_goi(f["t"]))
        if f.get("s"):
            terms.update(self.chishiki_goi(f["s"]))
        self.chishiki_terms[id(f)] = frozenset(terms)
        derived, rest = self.chishiki_shudai(f["t"])
        self.chishiki_shu[id(f)] = (self.normalize(f.get("s", "")), derived, rest)
        self.chishiki_keys[self.normalize(f["t"])] = f
        for t in terms:
            self.chishiki_idx.setdefault(t, []).append(f)

    
    def chishiki_oboeru(self, text, uid, gid, subject="", explicit=False, cid=0, tid=0):

        text = re.sub(r"\s+", " ", str(text or "")).strip()
        subject = str(subject or "").strip()
        key = self.normalize(text)
        if not key or is_gibberish(text) or is_gibberish(subject):
            return None
        f = self.chishiki_keys.get(key)
        if f is not None:
            if uid not in f["by"]:
                f["by"] = (f["by"] + [uid])[-5:]
            if explicit:
                f["x"] = 1
                if subject and not f.get("s"):
                    f["s"] = subject
                    self.chishiki_kouchiku()
            self.dirty += 1
            return "更新"
        f = {"s": subject, "t": text, "g": gid, "c": cid, "d": tid, "by": [uid], "x": 1 if explicit else 0}
        self.facts.append(f)
        self._chishiki_toroku(f)
        vec_index.add("f", text)
        self.dirty += 1
        if self.dirty >= 20:
            self.save_async()
        return "新規"

    
    def chishiki_kotoba_manabu(self, text, source=None):
        learned = []
        source_key = self.source_key(source)
        source_words = self.source_vocab.setdefault(source_key, {}) if source_key else None
        for word in nuun_goi(text, whole=False):
            self.vocab[word] = min(1000000, int(self.vocab.get(word, 0)) + 1)
            if source_words is not None:
                source_words[word] = min(1000000, int(source_words.get(word, 0)) + 1)
            learned.append(word)
        if learned:
            self.dirty += 1
        return learned

    
    def chishiki_kotoba_saisei(self):
        if self.vocab_ver >= 2:
            return 0
        new = {}
        for s in list(self.sentences):
            c = max(1, int(self.counts.get(s, 1)))
            for w in nuun_goi(s):
                new[w] = min(1000000, new.get(w, 0) + c)
        for f in list(self.facts):
            if f["t"] in self.counts:
                continue
            for w in nuun_goi(f["t"]):
                new[w] = min(1000000, new.get(w, 0) + 1)
        self.vocab = new
        self.vocab_ver = 2
        self.dirty += 1
        return len(new)

    
    def chishiki_kotoba_hit(self, text, limit=8):
        words = self.chishiki_kotoba(text)
        known = [(self.vocab.get(word, 0), word) for word in words if word in self.vocab]
        known.sort(key=lambda x: x[0], reverse=True)
        return [word for _, word in known[:max(1, min(int(limit), 20))]]

    
    @staticmethod
    def chishiki_kotoba(text):
        return nuun_goi(text)

    
    def chishiki_manabu(self, text, uid, gid, cid=0, tid=0):
        source = (gid, cid, tid, uid)                                   
        self.chishiki_alias_manabu(text, uid)
        words = self.chishiki_kotoba_manabu(text, source=source)
        cleaned = nuun.clean(text)
        self.learn(cleaned, store_sentence=False, source=source)
        return len(words), 0

    
    def chishiki_sagasu(self, question, limit=2):

        qt = self.chishiki_goi(question)
        total = len(self.facts)
        if not qt or not total:
            return []

        
        def idf(t):
            return math.log((total + 1) / (len(self.chishiki_idx.get(t, ())) + 1)) + 1

        weight = {t: idf(t) for t in qt}
        denom = sum(weight.values())
        known = sorted((t for t in qt if t in self.chishiki_idx), key=lambda t: weight[t], reverse=True)[:4]
        qkey = self.normalize(question)
        candidates = {}
        for t in known:
            for f in self.chishiki_idx[t][-2000:]:
                candidates[id(f)] = f
        scored = []
        for f in candidates.values():
            if self.normalize(f["t"]) == qkey:
                continue
            shared = self.chishiki_terms[id(f)] & weight.keys()
            sw = sum(weight[t] for t in shared)
            coverage = sw / denom if denom else 0.0
            explicit = bool(f["x"])
            if not ((coverage >= 0.7 and sw >= 3.0) or (explicit and coverage >= 0.5 and sw >= 1.0)):
                continue
            scored.append((coverage + (0.15 if explicit else 0.0) + 0.03 * min(len(f["by"]), 5), f))
        if not scored:
            return []
        scored.sort(key=lambda x: x[0], reverse=True)
        top_score, top = scored[0]
        picked = [top]
        for score, f in scored[1:]:
            if len(picked) >= max(1, limit):
                break
            a, b = self.chishiki_terms[id(top)], self.chishiki_terms[id(f)]
            if score >= top_score * 0.85 and len(a & b) / max(1, len(a | b)) < 0.8:
                picked.append(f)
        return picked

    
    def chishiki_zenpou(self, question, limit=3, force=False):


        topic, asked = self.chishiki_wadai(question)
        if not (asked or force) or (len(topic) < 2 and not re.fullmatch(r"[一-龥々〆]", topic)) or topic in chishiki_tomeru:
            return []
        qkey = self.normalize(question)
        loose_ok = len(topic) >= 3 or not re.fullmatch(r"[ぁ-ん]+", topic)
        found = []
        for key, f in self.chishiki_keys.items():
            if key == qkey or len(key) <= len(topic):
                continue
            subj, derived, rest = self.chishiki_shu[id(f)]
            if subj == topic or derived == topic:
                rank, answer = 3, (rest if derived == topic and subj in ("", topic) else f["t"])
            elif key.startswith(topic):
                rank, answer = 2, f["t"]
            elif loose_ok and topic in key:
                rank, answer = 1, f["t"]
            else:
                continue
            if len(self.normalize(answer)) < 2:
                answer = f["t"]
            found.append((rank, 1 if f.get("x") else 0, len(f["by"]), f["t"], answer.strip(" 　、。,.，．!！?？…~〜:：;；")))
        if not found:
            return []
        found.sort(key=lambda x: x[:3], reverse=True)
        best = found[0][0]
        return [(t, a) for r, _, _, t, a in found if r == best][:max(1, limit)]

    
    def chishiki_kensaku(self, keyword):
        kn = self.normalize(keyword)
        if not kn:
            return []
        return [f for f in self.facts if kn in self.normalize(f["t"]) or kn == self.normalize(f.get("s", ""))]

    
    def chishiki_wasureru(self, keyword, uid, gid, admin=False):

        targets = [f for f in self.chishiki_kensaku(keyword) if (admin and f["g"] == gid) or f["by"] == [uid]]
        if not targets:
            return 0
        ids = {id(f) for f in targets}
        self.facts = [f for f in self.facts if id(f) not in ids]
        self.facts_removed += 1
        self.chishiki_kouchiku()
        vec_index.discard({("f", f["t"], "", "") for f in targets})
        self.dirty += 1
        return len(targets)

    
    def chishiki_jojo_wasureru(self, gid, cid=0, tid=0):
        gid, cid, tid = int(gid), int(cid or 0), int(tid or 0)
        def match(f):
            if int(f.get("g", 0)) != gid:
                return False
            fc, ft = int(f.get("c", 0)), int(f.get("d", 0))
            if tid:
                return ft == tid
            if cid:
                return fc == cid
            return True
        targets = [f for f in self.facts if match(f)]
        self.facts = [f for f in self.facts if not match(f)]
        removed = len(targets)
        if removed:
            self.facts_removed += 1
            self.chishiki_kouchiku()
            vec_index.discard({("f", f["t"], "", "") for f in targets})
            self.dirty += removed
        return removed

    def forget_source(self, gid, cid=0, tid=0):
        targets = [key for key in set(self.source_relations) | set(self.source_vocab) if self.source_matches(key, gid, cid, tid)]
        if not targets:
            return 0
        for key in targets:
            self.source_vocab.pop(key, None)
            self.source_relations.pop(key, None)
        self._rebuild_from_sources()
        self.dirty += 1
        if self.dirty >= 20:
            self.save_async()
        return len(targets)

    def _rebuild_from_sources(self):

        rebuilt_vocab = {}
        for source_words in self.source_vocab.values():
            for word, count in source_words.items():
                rebuilt_vocab[word] = min(1000000, rebuilt_vocab.get(word, 0) + int(count))
        self.vocab = rebuilt_vocab
        rebuilt = {}
        for source_rows in self.source_relations.values():
            for left, rights in source_rows.items():
                row = rebuilt.setdefault(left, {})
                for right, count in rights.items():
                    row[right] = min(100000, int(row.get(right, 0)) + int(count))
        if len(rebuilt) > 20000:
            rebuilt = dict(sorted(rebuilt.items(), key=lambda item: sum(item[1].values()), reverse=True)[:16000])
        self.relations = rebuilt

    def forget_user(self, uid):


        uid = int(uid)
        targets = [key for key in set(self.source_relations) | set(self.source_vocab) if self.source_has_owner(key, uid)]
        for key in targets:
            self.source_vocab.pop(key, None)
            self.source_relations.pop(key, None)
        if targets:
            self._rebuild_from_sources()
        gone = [f for f in self.facts if f["by"] == [uid]]
        for f in self.facts:
            if uid in f["by"] and f["by"] != [uid]:
                f["by"] = [u for u in f["by"] if u != uid]                               
        if gone:
            ids = {id(f) for f in gone}
            self.facts = [f for f in self.facts if id(f) not in ids]
            self.facts_removed += 1
            self.chishiki_kouchiku()
            vec_index.discard({("f", f["t"], "", "") for f in gone})
        aliases = self.alias_by.pop(str(uid), None) or []
        if aliases:
            self.alias_rebuild()
        self.dirty += 1
        return {"sources": len(targets), "facts": len(gone), "alias": len(aliases)}

    
    def save(self):

        global data_purged
        if data_purged:
            return
        with self.save_lock:
            self.dirty = 0
            dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
            sentences, counts = list(self.sentences), dict(self.counts)
            turns, facts, rel, vocab = list(self.turns), list(self.facts), list(self.relations.items()), dict(self.vocab)
            source_relations, source_vocab = dict(self.source_relations), dict(self.source_vocab)
            alias_by = {u: list(rows) for u, rows in list(self.alias_by.items())}
            alias_base = list(self.alias_base)
            tmp = self.path.with_suffix(".tmp")
            with AngouWriter(tmp) as f:
                f.write('{"sentences":' + dump(sentences) + ',"counts":' + dump(counts) + ',"turns":[')
                f.write(",".join(dump(x) for x in turns))
                f.write('],"facts":[')
                f.write(",".join(dump(x) for x in facts))
                f.write('],"alias_groups":' + dump(self.alias_groups) + ',"relations":{')
                for i in range(0, len(rel), 300):
                    if i:
                        f.write(",")
                    f.write(",".join(dump(k) + ":" + dump(v) for k, v in rel[i:i + 300]))
                f.write('},"vocab":' + dump(vocab) + ',"source_relations":' + dump(source_relations) + ',"source_vocab":' + dump(source_vocab) + ',"alias_by":' + dump(alias_by) + ',"alias_base":' + dump(alias_base) + ',"vocab_ver":' + str(int(self.vocab_ver)) + '}')
            tmp.replace(self.path)

    
    def save_async(self):

        with self.save_state:
            if self.save_busy:
                self.save_again = True
                return
            self.save_busy = True

        
        def run():
            while True:
                with self.save_state:
                    self.save_again = False
                try:
                    self.save()
                except Exception as error:     
                    print(f"memory.json を保存できません: {error}")
                with self.save_state:
                    if not self.save_again:
                        self.save_busy = False
                        return

        threading.Thread(target=run, daemon=True).start()


shared_memory = SharedMemory()


def ruri_bunkatsu(text):
    text = re.sub(r"https?://\S+|www\.\S+", " ", str(text or ""))
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 2 or is_gibberish(text):
        return []
    out = []
    seen = set()

    def add(value):
        value = re.sub(r"\s+", " ", str(value or "")).strip(" ,，、")
        if len(value) < 2 or is_gibberish(value):
            return
        key = SharedMemory.normalize(value)
        if key and key not in seen:
            seen.add(key)
            out.append(value)

    for part in re.split(r"[。！？!?、,，；;：:]|(?:だけど|けど|ので|から|なら|のに|ても|そして|でも|また|ただ)|(?:\s+)", text):
        part = part.strip()
        if not part:
            continue
        if len(part) <= 32:
            add(part)
            continue
        toks = [w for w, kind, _ in nuun_wakachi(part) if kind != "sym"]
        if len(toks) >= 3:
            for width in (7, 5, 3):
                if len(out) >= 12:
                    break
                step = max(1, width - 2)
                for i in range(0, len(toks) - width + 1, step):
                    add("".join(toks[i:i + width]))
                    if len(out) >= 12:
                        break
        if not toks:
            for i in range(0, len(part), 24):
                add(part[i:i + 32])
                if len(out) >= 12:
                    break
    if not out and len(text) <= 32:
        add(text)
    return out[:12]


class VecIndex:


    
    def __init__(self):
        self.path = deeta / "memory_vec.npz"
        self.model = None
        self.state = "未読込"
        self.items = []
        self.mat = None
        self.keys = set()
        self.pending_items = []
        self.pending_vecs = []
        self.train_mtime = None
        self.todo = []              
        self.qcache = {}
        self.dirty = 0
        self.blocked_sources = []
        self.lock = threading.Lock()
        self.save_lock = threading.Lock()

    
    @property
    def ready(self):
        return self.model is not None and self.state == "使用中"

    
    @staticmethod
    def key_of(item):
        return (item["k"], item["t"], item.get("a", ""), item.get("s", ""))

    
    def encode_query(self, text):
        v = self.qcache.get(text)
        if v is None:
            v = self.encode([text])[0]
            if len(self.qcache) >= 256:
                self.qcache.pop(next(iter(self.qcache)))
            self.qcache[text] = v
        return v

    
    def encode(self, texts):
        vecs = np.asarray(self.model.encode([vec_prefix + t for t in texts], batch_size=32, show_progress_bar=False, normalize_embeddings=True), dtype=np.float32)
        if vecs.ndim == 1:
            vecs = vecs[None, :]
        return vecs / np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)

    
    def _flush(self):
        if not self.pending_items:
            return
        block = np.vstack(self.pending_vecs).astype(np.float32)
        self.mat = block if self.mat is None else np.vstack([self.mat, block])
        self.items.extend(self.pending_items)
        self.pending_items, self.pending_vecs = [], []

    
    def load(self):

        if np is None:
            self.state = "使えない(numpyが入っていません)"
            return False
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            self.state = "使えない(pip install sentence-transformers が必要)"
            return False
        self.state = "読込中"
        try:
            self.model = self._load_model(SentenceTransformer)
            self.model.max_seq_length = vec_max_len
        except Exception as error:
            self.model = None
            self.state = f"使えない(モデルを読み込めません: {type(error).__name__})"
            print(f"意味検索のモデルを読み込めません: {error}")
            return False
        self._load_cache()
        self.state = "使用中"
        return True

    
    @staticmethod
    def _load_model(SentenceTransformer):

        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"

        devices = [device]
        if device == "cuda":
            devices.append("cpu")

        last = None
        for target_device in devices:
            try:
                return SentenceTransformer(vec_model_name, device=target_device, local_files_only=True)
            except TypeError:
                pass
            except Exception as error:
                last = error
                if target_device == "cuda":
                    print(f"GPUでのモデル読み込みに失敗しました。CPUに切り替えます: {error}")

            for i in range(vec_dl_retries):
                try:
                    if i:
                        wait = min(vec_dl_wait * (2 ** (i - 1)), 600) + random.uniform(0, 3)
                        print(f"Hugging Faceが混み合っています。{wait:.0f}秒後に再試行します({i}/{vec_dl_retries - 1})")
                        time.sleep(wait)
                    model = SentenceTransformer(vec_model_name, device=target_device)
                    print(f"意味検索モデルの実行デバイス: {target_device}")
                    return model
                except Exception as error:
                    last = error
                    error_text = f"{type(error).__name__} {error}"
                    if not any(w in error_text for w in ("429", "Too Many Requests", "rate limit", "Rate limit", "ConnectionError", "Timeout", "503", "502")):
                        break

            if target_device == "cuda":
                print("GPUを利用できないためCPUで再試行します")

        if last is not None:
            raise last
        raise RuntimeError("意味検索モデルを読み込めませんでした")

    
    def _load_cache(self):
        try:
            if not self.path.is_file():
                return
            data = np.load(io.BytesIO(yomubytes(self.path)), allow_pickle=False)
            if str(data["model"].item()) != vec_model_name + "|" + vec_prefix + "|s2":
                return
            items = json.loads(str(data["meta"].item()))
            vecs = data["vecs"].astype(np.float32)
            if vecs.ndim == 2 and len(items) == len(vecs):
                clean_items = []
                clean_vecs = []
                for item, vec in zip(items, vecs):
                    if not isinstance(item, dict) or not isinstance(item.get("k"), str) or not isinstance(item.get("t"), str) or not item.get("t", "").strip():
                        continue
                    clean_items.append(item)
                    clean_vecs.append(vec)
                matrix = np.asarray(clean_vecs, dtype=np.float32) if clean_vecs else None
                with self.lock:
                    self.items, self.mat = clean_items, matrix
                    self.keys = {self.key_of(it) for it in clean_items}
            if not angoukabare(self.path):
                kakubytes(self.path, self.path.read_bytes())
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            pass

    
    def sync(self, sm):

        if self.model is None:
            return
        wanted = {}
        for f in list(sm.facts):
            it = {"k": "f", "t": f["t"]}
            wanted[self.key_of(it)] = it
        for t in list(sm.turns):
            it = {"k": "t", "t": t["q"], "a": t["a"]}
            wanted[self.key_of(it)] = it
        seeds, _, qas = load_train()    
        for text, weight, core in seeds:
            it = {"k": "s", "t": text, "w": weight}
            wanted[self.key_of(it)] = it
        for q, a, weight in qas:
            it = {"k": "t", "t": q, "a": a, "w": weight}
            wanted[self.key_of(it)] = it
        with self.lock:
            for it in self.items:
                if it.get("k") == "m" and it.get("t"):
                    wanted[self.key_of(it)] = it
        self.train_mtime = train_mtime()
        with self.lock:
            self._flush()
            if self.mat is not None:
                keep = [i for i, it in enumerate(self.items) if self.key_of(it) in wanted]
                if len(keep) != len(self.items):
                    self.items = [self.items[i] for i in keep]
                    self.mat = self.mat[keep] if keep else None
            self.keys = {self.key_of(it) for it in self.items}
            missing = [it for k, it in wanted.items() if k not in self.keys]
        for i in range(0, len(missing), 512):
            batch = [it for it in missing[i:i + 512] if it["t"].strip()]
            if not batch:
                continue
            vecs = self.encode([it.get("e", it["t"]) for it in batch])
            with self.lock:
                for it, vec in zip(batch, vecs):
                    if self.key_of(it) not in self.keys:
                        self.keys.add(self.key_of(it))
                        self.pending_items.append(it)
                        self.pending_vecs.append(vec)
                        self.dirty += 1
        self.save()

    
    def save_async(self):
        def run():
            try:
                self.save()
            except Exception as error:
                print(f"意味検索の保存に失敗: {error}")

        threading.Thread(target=run, daemon=True).start()

    def save(self):
        with self.save_lock:
            self._save_locked()

    def _save_locked(self):
        if data_purged or self.model is None:
            return
        if self.todo:
            self.drain()
        with self.lock:
            self._flush()
            items = list(self.items)
            mat = None if self.mat is None else self.mat.astype(np.float16)
            self.dirty = 0
        if mat is None or not items:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            return
        tmp = self.path.with_suffix(".tmp")
        buf = io.BytesIO()
        np.savez_compressed(buf, vecs=mat, meta=np.array(json.dumps(items, ensure_ascii=False)), model=np.array(vec_model_name + "|" + vec_prefix + "|s2"))
        kakubytes(tmp, buf.getvalue())
        tmp.replace(self.path)

    
    def forget_source(self, gid, cid=0, tid=0):
        target = SharedMemory.source_key((gid, cid, tid))
        with self.lock:
            if target and target not in self.blocked_sources:
                self.blocked_sources.append(target)
            keep = []
            keepvec = []
            for i, it in enumerate(self.items):
                if it.get("k") == "m" and SharedMemory.source_matches(it.get("s", ""), gid, cid, tid):
                    continue
                keep.append(it)
                if self.mat is not None:
                    keepvec.append(self.mat[i])
            self.items = keep
            self.mat = np.asarray(keepvec, dtype=np.float32) if keepvec else None
            self.keys = {self.key_of(it) for it in self.items}
            self.todo = [it for it in self.todo if not (it.get("k") == "m" and SharedMemory.source_matches(it.get("s", ""), gid, cid, tid))]
            old_pending = list(zip(self.pending_items, self.pending_vecs))
            kept_pending = [(it, vec) for it, vec in old_pending if not (it.get("k") == "m" and SharedMemory.source_matches(it.get("s", ""), gid, cid, tid))]
            self.pending_items = [it for it, _ in kept_pending]
            self.pending_vecs = [vec for _, vec in kept_pending]
            self.dirty += 1
        self.save_async()

    def forget_user(self, uid):

        uid = int(uid)

        def mine(it):
            return it.get("k") == "m" and SharedMemory.source_has_owner(it.get("s", ""), uid)

        with self.lock:
            before = len(self.items) + len(self.pending_items) + len(self.todo)
            keep, keepvec = [], []
            for i, it in enumerate(self.items):
                if mine(it):
                    continue
                keep.append(it)
                if self.mat is not None:
                    keepvec.append(self.mat[i])
            self.items = keep
            self.mat = np.asarray(keepvec, dtype=np.float32) if keepvec else None
            self.todo = [it for it in self.todo if not mine(it)]
            pending = [(it, vec) for it, vec in zip(self.pending_items, self.pending_vecs) if not mine(it)]
            self.pending_items = [it for it, _ in pending]
            self.pending_vecs = [vec for _, vec in pending]
            self.keys = {self.key_of(it) for it in self.items}
            self.keys.update(self.key_of(it) for it in self.pending_items)
            self.keys.update(self.key_of(it) for it in self.todo)
            removed = before - (len(self.items) + len(self.pending_items) + len(self.todo))
            if removed:
                self.dirty += 1
        if removed:
            self.save_async()
        return removed

    async def start(self, sm):

        self.sm = sm
        if await asyncio.to_thread(self.load):
            await asyncio.to_thread(self.sync, sm)
            print(f"意味検索: 使用中({len(self.items)}件)")
            self.pump_task = asyncio.create_task(self.pump())
        else:
            print(f"意味検索: {self.state}。語の重なりで代用します")

    
    def add(self, kind, text, answer="", source=None):

        if data_purged or self.state.startswith("使えない"):
            return
        text = str(text or "").strip()
        if not text:
            return
        it = {"k": kind, "t": text}
        if answer:
            it["a"] = answer
        if source is not None:
            sk = SharedMemory.source_key(source)
            if sk:
                it["s"] = sk
        with self.lock:
            if it.get("s") and any(SharedMemory.source_matches(it["s"], *[int(x) for x in key.split(":")]) for key in self.blocked_sources):
                return
            if self.key_of(it) in self.keys:
                return
            self.keys.add(self.key_of(it))
            self.todo.append(it)

    
    def drain(self):

        if data_purged or not self.ready:
            return
        with self.lock:
            batch, self.todo = self.todo, []
        for i in range(0, len(batch), 64):
            part = batch[i:i + 64]
            vecs = self.encode([it["t"] for it in part])
            with self.lock:
                for it, vec in zip(part, vecs):
                    if it.get("s") and any(SharedMemory.source_matches(it["s"], *[int(x) for x in key.split(":")]) for key in self.blocked_sources):
                        self.keys.discard(self.key_of(it))
                        continue
                    self.pending_items.append(it)
                    self.pending_vecs.append(vec)
                    self.dirty += 1

    
    async def pump(self):
        while True:
            await asyncio.sleep(3)
            try:
                if train_mtime() != self.train_mtime and getattr(self, "sm", None) is not None:
                    await asyncio.to_thread(self.sync, self.sm)     
                if self.todo:
                    await asyncio.to_thread(self.drain)
                if self.dirty >= 200:
                    await asyncio.to_thread(self.save)
            except Exception as error:
                print(f"意味検索の取り込みエラー: {error}")

    
    def discard(self, keys):

        if self.model is None or not keys:
            return
        keys = set(keys)
        with self.lock:
            self.todo = [it for it in self.todo if self.key_of(it) not in keys]
            pending = [(it, vec) for it, vec in zip(self.pending_items, self.pending_vecs) if self.key_of(it) not in keys]
            self.pending_items = [it for it, _ in pending]
            self.pending_vecs = [vec for _, vec in pending]
            if self.mat is not None and self.items:
                keep = [i for i, it in enumerate(self.items) if self.key_of(it) not in keys]
                if len(keep) != len(self.items):
                    self.items = [self.items[i] for i in keep]
                    self.mat = self.mat[keep] if keep else None
                    self.dirty += 1
            self.keys = {self.key_of(it) for it in self.items}
            self.keys.update(self.key_of(it) for it in self.pending_items)
            self.keys.update(self.key_of(it) for it in self.todo)
        self.save_async()

    def search(self, query, per_kind=6):

        if not self.ready:
            return None
        query = str(query or "").strip()
        out = {"f": [], "t": [], "s": [], "m": []}
        if not query:
            return out
        q = self.encode_query(query)
        qn = SharedMemory.normalize(query)
        with self.lock:
            self._flush()
            if self.mat is None or not self.items:
                return out
            sims = self.mat @ q
            order = np.argsort(-sims)[:per_kind * 12]
            for i in order:
                it = self.items[int(i)]
                kind = it.get("k")
                if kind not in out:
                    continue
                if len(out[kind]) >= per_kind or (SharedMemory.normalize(it["t"]) == qn and "w" not in it):
                    continue
                out[kind].append((float(sims[int(i)]), it))
        return out

    
    def hints(self, query, context=None):

        text = str(query or "").strip()
        if context and len(SharedMemory.normalize(text)) <= 8:
            text = f"{context} {text}"
        found = self.search(text)
        if found is None:
            return None
        cands = [(s, it.get("a", "")) for s, it in found["t"] if "w" in it and s >= vec_turn_min and it.get("a")]
        valid_facts = {SharedMemory.normalize(f["t"]) for f in shared_memory.facts if f.get("x")}
        cands += [(s, it["t"]) for s, it in found["f"] if s >= vec_fact_min and SharedMemory.normalize(it["t"]) in valid_facts]
        cands += [(s, it["t"]) for s, it in found["m"] if s >= vec_fact_min and it.get("t")]
        if not cands:
            return []
        cands.sort(key=lambda x: x[0], reverse=True)
        top = cands[0][0]
        hints = []
        for score, hint in cands:
            if score >= top - vec_margin and hint not in hints:
                hints.append(hint)
            if len(hints) >= vec_max_hints:
                break
        return hints


vec_index = VecIndex()

recent_replies = defaultdict(lambda: deque(maxlen=20))
nuun_gobi = ("ぬーん", "ぬーん", "ぬーん", "ぬん")


def _moji_kind(ch):
    if re.match(r"[一-龥々〆ヵヶ]", ch):
        return "k"      
    if re.match(r"[ぁ-ん]", ch):
        return "h"      
    if re.match(r"[ァ-ヴ]", ch):
        return "a"      
    if re.match(r"[A-Za-z0-9Ａ-Ｚａ-ｚ０-９]", ch):
        return "l"      
    return "o"          


nuun_joshi = "はがをにでともへや"


_tok = None
_tok_ng = False
nuun_jiritsu = {"名詞", "動詞", "形容詞", "副詞", "接続詞", "感動詞", "接頭詞"}


def get_tokenizer():

    global _tok, _tok_ng
    if _tok is None and not _tok_ng:
        try:
            from janome.tokenizer import Tokenizer
            _tok = Tokenizer()
        except Exception as error:
            _tok_ng = True
            print(f"形態素解析なし(pip install janome で単語境界が正確になる): {error}")
    return _tok


def nuun_kugiri_keitaiso(text, end):

    tok = get_tokenizer()
    if tok is None:
        return None
    try:
        toks = [(t.surface, t.part_of_speech.split(",")) for t in tok.tokenize(text)]
    except Exception:
        return None
    if sum(len(sf) for sf, _ in toks) != len(text):
        return None
    cuts = []
    pos = 0
    prev = None
    for surf, pp in toks:
        if prev is not None and 0 < pos < end:
            p1 = pp[0]
            p2 = pp[1] if len(pp) > 1 else ""
            q1 = prev[0]
            head = p1 in nuun_jiritsu and p2 not in ("非自立", "接尾")
            if q1 == "記号" and p1 != "記号":
                head = True
            if q1 in ("接頭詞", "連体詞"):
                head = False        
            elif q1 == p1 and q1 in ("名詞", "動詞"):
                head = False        
            if head:
                cuts.append(pos)
        pos += len(surf)
        prev = (pp[0],)
    return cuts


def nuun_kugiri(text, end):


    kinds = []
    for i, ch in enumerate(text):
        k = _moji_kind(ch)
        if ch in "ーｰ" and i:
            k = kinds[-1]       
        kinds.append(k)
    inside = set()
    for m in re.finditer(r"<[^>\n]*>", text):
        inside.update(range(m.start() + 1, m.end()))
    morph = nuun_kugiri_keitaiso(text, end)
    if morph is not None:
        
        return [i for i in morph if i not in inside and not (kinds[i - 1] == kinds[i] == "l")]
    out = []
    for i in range(1, end):
        if i in inside:
            continue
        a, b = kinds[i - 1], kinds[i]
        ok = False
        if a == b and a in ("l", "o"):
            ok = False          
        elif "o" in (a, b) or "l" in (a, b):
            ok = True
        elif a == "h" and b == "k":
            ok = True
        elif "a" in (a, b) and a != b:
            ok = True
        elif text[i - 1] == "を":
            ok = True
        elif text[i - 1] in nuun_joshi and i >= 2 and kinds[i - 2] in ("k", "a", "l"):
            ok = True
        if ok:
            out.append(i)
    return out


def nuunka(text):

    return str(text or "").strip()


_train_cache = {"mtime": None, "seeds": [], "fallbacks": [], "qas": []}
nuun_koe_moji = set("ぬヌぅぉんンーｰ〜~ぁぃぇっッ！!？?…・、。nNuU 　")


def train_mtime():
    try:
        return trainingfile.stat().st_mtime
    except OSError:
        return None


def load_train():


    mtime = train_mtime()
    if mtime is None:
        return [], [], []
    if _train_cache["mtime"] == mtime:
        return _train_cache["seeds"], _train_cache["fallbacks"], _train_cache["qas"]
    seeds, fallbacks, qas = {}, {}, []
    try:
        data = json.loads(trainingfile.read_text("utf-8"))
        st = data.get("settings", {})
        default_weight = max(1, int(st.get("default_weight", 2)))
        default_repeat = max(1, min(int(st.get("repeat", 1)), 50))
        group_mode = st.get("group_selection", "weight")
        item_mode = st.get("item_selection", "weight")
        for group in data.get("groups", []):
            if not isinstance(group, dict) or not group.get("enabled", True):
                continue
            group_weight = max(1, int(group.get("weight", default_weight)))
            group_fallback = bool(group.get("fallback", True))      
            group_repeat = max(1, min(int(group.get("repeat", default_repeat)), 50))
            if group_mode == "weight":
                group_repeat *= group_weight
            for item in group.get("items", []):
                questions = []
                item_fallback = group_fallback
                if isinstance(item, str):
                    text, item_weight, item_repeat = item, group_weight, group_repeat
                elif isinstance(item, dict) and item.get("enabled", True):
                    text = item.get("text", "")
                    item_weight = max(1, int(item.get("weight", group_weight)))
                    item_repeat = max(1, min(int(item.get("repeat", group_repeat)), 50))
                    item_fallback = bool(item.get("fallback", group_fallback))
                    q = item.get("q", [])
                    questions = [q] if isinstance(q, str) else [x for x in q if isinstance(x, str)]
                else:
                    continue
                text = str(text or "").strip()
                if not text:
                    continue
                weight = item_weight * item_repeat if item_mode == "weight" else item_weight
                qs = [x.strip() for x in questions if x.strip()]
                if qs:
                    qas.extend((x, text, weight) for x in qs)
                    continue
                
                seeds[text] = (seeds[text][0] + weight, text) if text in seeds else (weight, text)
                if item_fallback:
                    fallbacks[text] = fallbacks.get(text, 0) + weight
    except (json.JSONDecodeError, OSError, TypeError, ValueError, AttributeError):
        seeds, fallbacks, qas = {}, {}, []
    seeds = [(t, w, core) for t, (w, core) in seeds.items()]
    fallbacks = list(fallbacks.items())
    _train_cache.update(mtime=mtime, seeds=seeds, fallbacks=fallbacks, qas=qas)
    return seeds, fallbacks, qas


def load_seeds():


    return load_train()[1]


def nuun_kotoba():

    voices = [t for t, _ in load_seeds() if nuunre.fullmatch(t)]
    if voices and random.random() < 0.5:
        return random.choice(voices)
    return "ぬ" + "".join(random.choice("ーーーぅぉ") for _ in range(random.randint(1, 4))) + "ん"


def nuun_seisei(seed="", hints=None, minimum=12, maximum=18):

    try:
        minimum = max(8, min(int(minimum), 60))
        maximum = max(minimum, min(int(maximum), 60))
    except (TypeError, ValueError):
        minimum, maximum = 12, 18
    train_sources = load_train()[0]
    train_norms = [re.sub(r"[\s、。！？!?…~〜]", "", SharedMemory.normalize(source)) for source, _, _ in train_sources]
    for _ in range(24):
        try:
            text = nuun.generate(seed=seed, length=random.randint(minimum, maximum), hints=hints)
        except Exception:
            text = None
        if not text or not (minimum <= len(text) <= maximum) or not nuunre.search(text):
            continue
        norm = re.sub(r"[\s、。！？!?…~〜]", "", SharedMemory.normalize(text))
        if norm and not any(norm == sn or (len(norm) >= 12 and norm in sn and len(norm) / max(1, len(sn)) >= 0.75) for sn in train_norms if sn):
            return text
    return None


def kotaeru_sync(message_text, context_text, is_question, cid, gid=None):

    
    
    if gid is not None:
        nuun.use(gid)
        try:
            nuun.sync_knowledge_base(list(shared_memory.facts), shared_memory.facts_removed)
        except Exception as error:
            print(f"知識を生成の材料へ反映できません: {error}")
    ng = {SharedMemory.normalize(message_text), SharedMemory.normalize("ぬーんをやりるぬーん")}
    ng |= {SharedMemory.normalize(x) for x in recent_replies[cid]}

    
    def ok(x):
        x = str(x or "").strip()
        n = SharedMemory.normalize(x)
        return len(n) >= 2 and len(x) <= 200 and n not in ng and not re.search(r"https?://|<@|<#|@everyone|@here", x)

    
    def finish(out, pool=None, required_terms=None):

        answer = re.sub(r"\s+", " ", str(out or "").strip())
        if not answer:
            return None

        try:
            min_chars = max(8, min(int(nuun.settings.get("generation_min", 12)), 60))
            max_chars = max(min_chars, min(int(nuun.settings.get("generation_max", 18)), 60))
        except (TypeError, ValueError, AttributeError):
            min_chars, max_chars = 12, 18

        
        def norm(text):
            return re.sub(r"[\s、。！？!?…~〜]", "", SharedMemory.normalize(str(text or "")))

        
        def norm(text):
            return re.sub(r"[\s、。！？!?…~〜]", "", SharedMemory.normalize(str(text or "")))

        train_copy_sources = []
        try:
            seeds, _, qas = load_train()
            train_copy_sources.extend(str(source) for source, _, _ in seeds)
            train_copy_sources.extend(str(answer) for _, answer, _ in qas)
        except Exception:
            pass
        model_data = getattr(nuun, "model", {})
        if isinstance(model_data, dict):
            train_copy_sources.extend(str(x) for x in model_data.get("sentences", [])[-500:])
            train_copy_sources.extend(str(x) for x in model_data.get("talk", [])[-200:])
        try:
            train_copy_sources.extend(str(item.get("t", "")) for item in shared_memory.facts if isinstance(item, dict))
            train_copy_sources.extend(str(x) for x in shared_memory.sentences[-500:])
            for item in shared_memory.turns[-200:]:
                train_copy_sources.extend((str(item.get("q", "")), str(item.get("a", ""))))
        except Exception:
            pass
        training_norms = tuple(x for x in (norm(source) for source in train_copy_sources) if x)
        recent_norms = tuple(x for x in (norm(old) for old in list(recent_replies[cid])[-12:]) if x)

        def is_training_copy(text):
            n = norm(text)
            if not n:
                return True
            for sn in training_norms:
                if n == sn:
                    return True
                shorter, longer = (n, sn) if len(n) <= len(sn) else (sn, n)
                if len(shorter) >= 12 and shorter in longer and len(shorter) / max(1, len(longer)) >= 0.75:
                    return True
            return False

        def too_similar(candidate):
            n = norm(candidate)
            if not n:
                return False
            for old_n in recent_norms:
                if n == old_n:
                    return True
                if min(len(n), len(old_n)) >= 12 and difflib.SequenceMatcher(None, n, old_n, autojunk=False).ratio() >= .84:
                    return True
            return False

        def apply_dialect(text):

            text = str(text or "").strip()
            if not text:
                return text
            replacements = [
                (r"していました([。！？!?…~〜]?)$", r"していたぬーん\1"),
                (r"しています([。！？!?…~〜]?)$", r"しているぬーん\1"),
                (r"しました([。！？!?…~〜]?)$", r"したぬーん\1"),
                (r"でした([。！？!?…~〜]?)$", r"だったぬーん\1"),
                (r"です([。！？!?…~〜]?)$", r"なのだぬーん\1"),
                (r"だよ([。！？!?…~〜]?)$", r"だぬーん\1"),
                (r"だね([。！？!?…~〜]?)$", r"だぬーんね\1"),
                (r"する([。！？!?…~〜]?)$", r"しるぬーん\1"),
                (r"ない([。！？!?…~〜]?)$", r"なさぬーん\1"),
            ]
            for pattern, repl in replacements:
                changed = re.sub(pattern, repl, text)
                if changed != text:
                    return changed
            for old, new_word in (("かなしい", "かなぴぬーん"), ("悲しい", "かなぴぬーん"),
                                  ("うれしい", "うれぴぬーん"), ("嬉しい", "うれぴぬーん")):
                if old in text:
                    return text.replace(old, new_word, 1)
            return text

        
        def acceptable(candidate, *, question=False, required_terms=None):
            candidate = re.sub(r"\s+", " ", str(candidate or "").strip())
            if not candidate or not (min_chars <= len(candidate) <= max_chars):
                return None
            if not nuunre.search(candidate):
                return None
            if required_terms and any(self_term not in SharedMemory.normalize(candidate) for self_term in required_terms):
                return None
            if is_training_copy(candidate) or too_similar(candidate):
                return None
            return candidate


        def candidate_score(candidate):
            candidate = re.sub(r"\s+", " ", str(candidate or "").strip())
            if not candidate:
                return float("-inf")
            score = 0.0
            if min_chars <= len(candidate) <= max_chars:
                score += 4
            else:
                score -= min(8, abs(len(candidate) - max_chars if len(candidate) > max_chars else min_chars - len(candidate)) * 0.8)
            score += 4 if nuunre.search(candidate) else -3
            score += 3 if not is_training_copy(candidate) else -5
            score += 2 if not too_similar(candidate) else -3
            score += 2 if len(candidate) <= 200 else -5
            score += 3 if nuun.kiri(candidate) else -3                        
            score += 1 if not re.search(r"https?://|<@|<#|@everyone|@here", candidate) else -8
            if required_terms:
                present = sum(term in SharedMemory.normalize(candidate) for term in required_terms)
                score += 2 * present - 2 * (len(required_terms) - present)
            return score

        
        
        if is_question:
            generation_hints = [answer]
        else:
            generation_hints = [answer]

        
        
        
        generation_hints = [answer]
        generation_hints.extend(str(x) for x in (pool or []) if x)
        if required_terms:
            generation_hints.extend(required_terms)
        
        
        generated_candidates = []
        generated_seen = set()
        accepted_candidates = []
        for _ in range(32):
            generated = nuun.generate(
                seed=message_text,
                length=random.randint(min_chars, max_chars),
                hints=generation_hints,
            )
            if not generated or not str(generated).strip():
                continue
            generated = re.sub(r"\s+", " ", str(generated).strip())
            if generated in generated_seen:
                continue
            generated_seen.add(generated)
            generated_candidates.append(generated)
            accepted = acceptable(generated, question=is_question, required_terms=required_terms)
            if accepted:
                accepted_candidates.append(accepted)

        if not generated_candidates:
            print("返信候補を生成できませんでした(学習データが少ない可能性があります)")
            return None

        if accepted_candidates:
            best = max(accepted_candidates, key=candidate_score)
        else:
                                                          
                                                
            safe = []
            for cand in generated_candidates:
                if re.search(r"https?://|<@|<#|@everyone|@here", cand) or is_training_copy(cand) or is_broken_text(cand):
                    continue
                if not (nuun.kiri(cand) and nuunre.search(cand)):
                    cand = nuun.tojiru(cand)
                cand = re.sub(r"\s+", " ", str(cand or "").strip())
                if cand and nuunre.search(cand) and not is_training_copy(cand):
                    safe.append(cand)
            if not safe:
                return None
            best = max(safe, key=candidate_score)
        if not nuun.kiri(best):
                                                               
            closed = nuun.tojiru(best)
            if closed and nuunre.search(closed) and not is_training_copy(closed):
                best = closed
        recent_replies[cid].append(best)
        return best

    required_terms = []
    chains = shared_memory.chishiki_hitto(message_text)
    if chains:
        chain = max(chains, key=len)
        for i, term in enumerate(chain[1:], 1):
            if random.random() < (0.5 ** (i - 1)):
                required_terms.append(term)
        if chain[1] not in required_terms:
            required_terms.insert(0, chain[1])

    relation_hints = shared_memory.related_terms(message_text, limit=8)
    semantic_hints = []
    lex = []
    if is_question or shared_memory.chishiki_wadai(message_text)[1]:
        
        for full, _ in shared_memory.chishiki_zenpou(message_text, force=True, limit=3):
            if ok(full):
                lex.append((0.99, full))

    
    def pick_from(found):
        c = [(s, it["a"]) for s, it in found["t"] if "w" in it and s >= vec_turn_min and ok(it.get("a"))]
        c += lex
        if not c and is_question:
            valid_facts = {SharedMemory.normalize(f["t"]) for f in shared_memory.facts if f.get("x")}
            c = [(s, it["t"]) for s, it in found["f"] if s >= vec_fact_min and SharedMemory.normalize(it["t"]) in valid_facts and ok(it["t"])]
        return c

    if vec_index.ready and vec_index.todo:
        vec_index.drain()           
    found = vec_index.search(message_text)
    if found is not None:
        semantic_hints = [it["t"] for score, it in found.get("m", []) if score >= vec_fact_min and it.get("t")]
        cands = pick_from(found)
        if not cands and context_text and len(SharedMemory.normalize(message_text)) <= 8:
            
            found = vec_index.search(f"{context_text} {message_text}") or found
            semantic_hints = [it["t"] for score, it in found.get("m", []) if score >= vec_fact_min and it.get("t")]
            cands = pick_from(found)
    else:
        
        raw = [f["t"] for f in shared_memory.chishiki_sagasu(message_text)] if is_question else []
        raw.append(shared_memory.recall(message_text, context=context_text))
        cands = lex + [(1.0, x) for x in raw if ok(x)]
    hint_pool = relation_hints + [x for x in semantic_hints if x not in relation_hints]
    if not cands:
        return finish(message_text, pool=hint_pool, required_terms=required_terms)
    top = max(c[0] for c in cands)
    pool = [(s, c) for s, c in cands if s >= top - vec_margin]
    
    out = random.choices([c for _, c in pool], weights=[math.exp((s - top) / 0.03) for s, _ in pool], k=1)[0]
    return finish(out, pool=hint_pool, required_terms=required_terms)


nuun_lock = threading.Lock()   


def _kotaeru_locked(message_text, context_text, is_question, cid, gid):
    with nuun_lock:
        return kotaeru_sync(message_text, context_text, is_question, cid, gid)


def nuun_junbi():
    get_tokenizer()
    with nuun_lock:
        try:
            nuun.kidou()
        except Exception as error:
            print(f"学習データの準備に失敗: {error}")
    try:
        n = shared_memory.chishiki_kotoba_saisei()
        if n:
            print(f"語彙を日本語の語単位で作り直しました: {n}語")
            shared_memory.save_async()
    except Exception as error:
        print(f"語彙の作り直しに失敗: {error}")


def _nuun_manabu_locked(gid, text, source=None):
    with nuun_lock:
        nuun.use(gid)
        nuun.learn_vocabulary(text, source=source)
    ruri_manabu(text, source=source)


async def nuun_manabu(gid, text, source=None):
    try:
        await asyncio.to_thread(_nuun_manabu_locked, gid, text, source)
    except Exception as error:
        print(f"生成用の学習に失敗: {error}")


async def kotaeru(message_text, context_text, is_question, cid, gid=None):
    
    return await asyncio.to_thread(_kotaeru_locked, message_text, context_text, is_question, cid, gid)


def ruri_manabu(text, source=None):
    for part in ruri_bunkatsu(text):
        vec_index.add("m", part, source=source)


class NuunGakushu:
    
    def __init__(self):
        self.ngram = 3
        self.max_learn_length = 300
        self.generation_max = 20
        self.backoff_p = 0.10       
        self.dirty = 0
        self.models = {}                            
        self.legacy = None                                
        self.settings = {}
        self.recent = []
        self.recent_a = []
        self.base_models = {}
        self.saving = False
        self.model = self.sinki()
        self.load()

    
    def sinki(self):
        return {
            "total": 0, "chars": {}, "starts": {}, "ends": {},
            "sentences": [], "talk": [], "chars2": {}, "chars5": {},
            "privacy_learning_version": 2,
            "kioku": {"df": {}, "cooc": {}, "reply": {}, "short": {}, "aizuchi": {}, "n": 0, "pairs": 0},
        }

    
    def seiri(self, m):
        for name in ("chars", "starts", "ends", "chars2", "chars5"):
            m.setdefault(name, {})
        m.setdefault("total", 0)
        m.setdefault("sentences", [])
        m.setdefault("talk", [])
        m.pop("taiwa", None)
        try:
            privacy_version = int(m.get("privacy_learning_version", 0))
        except (TypeError, ValueError):
            privacy_version = 0
        if privacy_version < 2:
            for name in ("chars", "starts", "ends", "chars2", "chars5"):
                m[name] = {}
            m["total"] = 0
            m["sentences"] = []
            m["talk"] = []
            m.pop("training_hash_v2", None)
            m.pop("training_hash", None)
            m.pop("training_learned", None)
            m["privacy_learning_version"] = 2
            self.dirty += 1
        else:
            m["sentences"] = [x for x in m["sentences"] if isinstance(x, str) and not is_gibberish(x)]
            m["talk"] = []
        k = m.setdefault("kioku", {})
        for name in ("df", "cooc", "reply", "short", "aizuchi", "facts"):
            k.setdefault(name, {})
        if "sources" not in k:
            if k.get("df") or k.get("cooc") or k.get("reply") or k.get("short") or k.get("aizuchi") or k.get("n") or k.get("pairs"):
                self.dirty += 1
            k["df"] = {}
            k["cooc"] = {}
            k["reply"] = {}
            k["short"] = {}
            k["aizuchi"] = {}
            k["facts"] = {}
            k["n"] = 0
            k["pairs"] = 0
            k["sources"] = {}
        elif not isinstance(k.get("sources"), dict):
            k["sources"] = {}
        self._rebuild_kioku_sources(k)
        if not m["chars2"] or not m["chars5"]:
            for sentence in m["sentences"] + m["talk"]:
                for i in range(len(sentence) - 2):
                    self._add(m["chars2"], sentence[i:i + 2], sentence[i + 2], 1)
                for i in range(len(sentence) - 5):
                    self._add(m["chars5"], sentence[i:i + 5], sentence[i + 5], 1)

    
    @staticmethod
    def _topic_token(t):
        if nuunre.fullmatch(t):
            return False
        if len(t) >= 2:
            return bool(re.search(r"[ぁ-んァ-ヴ一-龥A-Za-z0-9]", t))
        return bool(re.fullmatch(r"[一-龥々〆]", t))

    
    def content_tokens(self, text):
        return {w for w, kind, _ in nuun_wakachi(self.clean(text)) if kind in ("word", "fixed") and self._topic_token(w)}

    
    def _add_sentence_to_base(self, base, sentence):
        text = self._knowledge_text(self.clean(sentence))     
        if len(text) < self.ngram + 1:
            return
        if text.replace(" ", "") == "ぬーんをやりるぬーん":
            return
        if is_broken_text(text):
            return      
        seen = base.setdefault("_seen", set())
        if text in seen:
            return
        seen.add(text)
        self._add(base["starts"], text[:self.ngram], text[0], 1)
        for i in range(len(text) - self.ngram):
            self._add(base["chars"], text[i:i + self.ngram], text[i + self.ngram], 1)
        for i in range(len(text) - 2):
            self._add(base["chars2"], text[i:i + 2], text[i + 2], 1)
        for i in range(len(text) - 5):
            self._add(base["chars5"], text[i:i + 5], text[i + 5], 1)
        self._add(base["ends"], text[-self.ngram:], text[-1], 1)
        words = self.word_tokens(text)
        if len(words) < 3:
            return
        if not re.fullmatch(r"[。！？!?…~〜]+", words[-1]):
            words.append("。")      
        base["word_starts"].append(words[:2])
        base["word_ends"].append(words[-1])
        topic_tokens = frozenset(self.content_tokens(text))
        if topic_tokens:
            entry = (tuple(words[:2]), topic_tokens)
            for token in topic_tokens:
                base.setdefault("topic_index", {}).setdefault(token, []).append(entry)
        for i in range(1, len(words)):
            self._add(base["word_next"], self.word_key(words[i - 1:i]), words[i], 1)
        
        w2 = base.setdefault("word_next2", {})
        for i in range(2, len(words)):
            self._add(w2, self.word_key(words[i - 2:i]), words[i], 1)

    
    def base_model(self, gid=None):
        if gid is None:
            gid = next((k for k, v in self.models.items() if v is self.model), None)
        gid = str(gid or "0")
        if gid in self.base_models:
            return self.base_models[gid]
        m = self.model
        base = {"chars": {}, "starts": {}, "ends": {}, "chars2": {}, "chars5": {},
                "word_next": {}, "word_starts": [], "word_ends": [], "topic_index": {}, "_seen": set()}
        
        extra = []
        try:
            seeds, _, qas = load_train()
            extra = [t for t, _, _ in seeds] + [a for _, a, _ in qas]
        except Exception:
            extra = []
        for sentence in extra + list(m.get("sentences", [])) + list(m.get("talk", [])):
            self._add_sentence_to_base(base, sentence)
        self.base_models[gid] = base
        return base

    
    def word_tokens(self, text):
        return [w for w, _kind, _pos in nuun_wakachi(self.clean(text))]

    
    def word_key(self, words):
        return "\x1f".join(words)

    
    def use(self, gid):

        gid = str(gid)
        m = self.models.get(gid)
        if m is None:
            m = self.models[gid] = self.sinki()
            self.model = m
            self.learn_settings()
        self.model = m
        self.base_model(gid)
        return m

    
    def kidou(self):
        self.yomu_settings()
        for gid in list(self.models):
            self.model = self.models[gid]
            self.learn_settings()
        for gid in self.models:
            self.model = self.models[gid]
            self.base_model(gid)
        print(f"学習データ: {len(self.models)}サーバー分")

    
    def load(self):
        data = {}
        if modelfile.is_file():
            try:
                data = json.loads(yomutext(modelfile))
            except (json.JSONDecodeError, OSError):
                data = {}
        if isinstance(data.get("saba"), dict):
            self.models = data["saba"]
            self.legacy = None
        elif data:
            self.legacy = None
        for m in self.models.values():
            self.seiri(m)
        if self.dirty:
            self.save()

    
    def save(self):
        global data_purged
        if data_purged:
            return
        cur = self.model
        for m in self.models.values():
            self.model = m
            self.prune()
        self.model = cur
        data = {"version": 3, "saba": self.models}
        if self.legacy:
            data["kyotsu"] = self.legacy
        tmp = modelfile.with_suffix(".tmp")
        kakutext(tmp, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        tmp.replace(modelfile)
        self.dirty = 0

    
    def clean(self, text):
        text = str(text or "")
        text = re.sub(r"<@!?\d+>", "", text)
        text = re.sub(r"<#\d+>", "", text)
        text = re.sub(r"<@&\d+>", "", text)
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"https?://\S+", "", text)
        text = text.replace("\\n", "").replace("\\r", "")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:self.max_learn_length]

    
    def _add(self, table, key, value, weight=1):
        table.setdefault(key, {})
        table[key][value] = table[key].get(value, 0) + weight

    
    def learn(self, text, weight=1, talk=False):
        text = self.clean(text)
        if len(text) < self.ngram + 1:
            return
        if is_gibberish(text):
            return      

        weight = max(1, min(int(weight), 100))
        self.model["total"] += weight
        self.dirty += 1

        self._add(self.model["starts"], text[:self.ngram], text[0], weight)

        for i in range(len(text) - self.ngram):
            self._add(
                self.model["chars"],
                text[i:i + self.ngram],
                text[i + self.ngram],
                weight
            )

        for i in range(len(text) - 2):
            self._add(self.model["chars2"], text[i:i + 2], text[i + 2], weight)

        for i in range(len(text) - 5):
            self._add(self.model["chars5"], text[i:i + 5], text[i + 5], weight)

        self._add(self.model["ends"], text[-self.ngram:], text[-1], weight)

        sentences = self.model["talk"] if talk else self.model["sentences"]
        if text not in sentences:
            sentences.append(text)
            limit = 2000 if talk else 5000
            if len(sentences) > limit:
                del sentences[:-limit]
            gid = str(next((k for k, value in self.models.items() if value is self.model), "0"))
            base = self.base_models.get(gid)
            if base is not None:
                self._add_sentence_to_base(base, text)

    
    def learn_vocabulary(self, text, weight=1, source=None):
        cleaned = self.clean(text)
        if len(cleaned) < 2 or is_gibberish(cleaned):
            return
        self.learn_kioku(cleaned, source=source)

    
    def yomu_settings(self):
        if not trainingfile.is_file():
            return None
        try:
            data = json.loads(trainingfile.read_text("utf-8"))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return None

        self.settings = data.get("settings", {})
        self.ngram = max(2, min(int(self.settings.get("ngram", 3)), 6))
        self.max_learn_length = max(
            self.ngram + 1,
            min(int(self.settings.get("max_learn_length", 300)), 1000)
        )
        self.generation_max = max(10, min(int(self.settings.get("generation_max", 18)), 60))
                                                   
        self.maxweak = max(0, min(int(self.settings.get("weak_join_max", 2)), 20))
        return data

    
    def learn_settings(self):
        data = self.yomu_settings()
        if data is None:
            return

                                                        
        digest = hashlib.sha256(
            json.dumps(data.get("groups", []), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if "training_hash_v2" not in self.model and (
            "training_hash" in self.model or self.model.get("training_learned")
        ):
            self.model["training_hash_v2"] = digest
            return
        if self.model.get("training_hash_v2") == digest:
            return

        default_weight = max(1, int(self.settings.get("default_weight", 2)))
        default_repeat = max(1, min(int(self.settings.get("repeat", 1)), 50))
        group_mode = self.settings.get("group_selection", "weight")
        item_mode = self.settings.get("item_selection", "weight")

        for group in data.get("groups", []):
            if not isinstance(group, dict) or not group.get("enabled", True):
                continue

            group_weight = max(1, int(group.get("weight", default_weight)))
            group_repeat = max(1, min(int(group.get("repeat", default_repeat)), 50))

            if group_mode == "weight":
                group_repeat *= group_weight

            for item in group.get("items", []):
                if isinstance(item, str):
                    text = item
                    item_weight = group_weight
                    item_repeat = group_repeat
                elif isinstance(item, dict) and item.get("enabled", True):
                    text = item.get("text", "")
                    item_weight = max(1, int(item.get("weight", group_weight)))
                    item_repeat = max(1, min(int(item.get("repeat", group_repeat)), 50))
                else:
                    continue

                if not text:
                    continue

                total_weight = (
                    item_weight * item_repeat
                    if item_mode == "weight"
                    else item_weight
                )
                self.learn(text, total_weight)

        self.model["training_hash_v2"] = digest
        self.save()

    
    def keyword_score(self, message, rule):
        message = self.clean(message)
        keywords = rule.get("kiwado", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        if not keywords:
            return 0.18

        hits = sum(1 for keyword in keywords if keyword and keyword in message)
        return min(1.0, 0.42 + hits * 0.16) if hits else 0.0

    
    def nuun_score(self, message):
        text = self.clean(message)
        if len(text) <= self.ngram:
            return 0.0

        known = 0
        total = 0

        for i in range(len(text) - self.ngram):
            total += 1
            if text[i:i + self.ngram] in self.model["chars"]:
                known += 1

        return known / total if total else 0.0

    
    def reply_probability(self, message, rule):
        try:
            base = max(0.0, min(100.0, float(rule.get("ritsu", 0)))) / 100.0
        except (TypeError, ValueError, AttributeError):
            return 0.0

        if base <= 0:
            return 0.0
        if base >= 1:
            return 1.0

        key_score = self.keyword_score(message, rule)
        style_score = self.nuun_score(message)

        probability = base * (0.72 + key_score * 0.20 + style_score * 0.08)

        if key_score > 0:
            probability = max(probability, base * 0.55)

        return max(0.0, min(1.0, probability))

    
    def weighted_choice(self, values):
        if not values:
            return None

        total = sum(max(0, float(value)) for value in values.values())
        if total <= 0:
            return random.choice(list(values))

        point = random.random() * total

        for value, weight in values.items():
            point -= max(0, float(weight))
            if point <= 0:
                return value

        return next(iter(values))

                             
    
    def kioku(self):
        return self.model["kioku"]

    
    def tokens(self, text):
        out = []
        for t in tokenre.findall(self.clean(text)):
            if t in tomeru or len(t) > 8 or nuunre.search(t) or t in out:
                continue
            out.append(t)
        return out[:8]

    
    def idf(self, t):
        k = self.kioku()
        return math.log((k["n"] + 2) / (k["df"].get(t, 0) + 1)) + 1

    
    def learn_kioku(self, text, source=None):
        k = self.kioku()
        toks = self.tokens(text)
        source_key = SharedMemory.source_key(source)
        if not toks or source_key is None:
            return
        record = k.setdefault("sources", {}).setdefault(source_key, {"n": 0, "df": {}, "cooc": {}}) if source_key else None
        k["n"] += 1
        self.dirty += 1
        if record is not None:
            record["n"] = int(record.get("n", 0)) + 1
        for t in toks:
            k["df"][t] = k["df"].get(t, 0) + 1
            if record is not None:
                record["df"][t] = int(record["df"].get(t, 0)) + 1
        for a in toks:
            for b in toks:
                if a != b:
                    self._add(k["cooc"], a, b)
                    if record is not None:
                        self._add(record["cooc"], a, b)

    
    def _rebuild_kioku_sources(self, k):
        sources = k.setdefault("sources", {})
        k["df"] = {}
        k["cooc"] = {}
        k["n"] = 0
        for record in sources.values():
            if not isinstance(record, dict):
                continue
            k["n"] += max(0, int(record.get("n", 0)))
            for word, count in record.get("df", {}).items():
                k["df"][word] = k["df"].get(word, 0) + max(0, int(count))
            for left, rights in record.get("cooc", {}).items():
                for right, count in rights.items():
                    self._add(k["cooc"], left, right, max(0, int(count)))
        k["reply"] = {}
        k["short"] = {}
        k["aizuchi"] = {}
        k["pairs"] = 0

    
    def forget_source(self, gid, cid=0, tid=0):
        model = self.models.get(str(gid))
        if model is None:
            return 0
        k = model.setdefault("kioku", {})
        sources = k.setdefault("sources", {})
        targets = [key for key in sources if SharedMemory.source_matches(key, gid, cid, tid)]
        if not targets:
            return 0
        for key in targets:
            sources.pop(key, None)
        self._rebuild_kioku_sources(k)
        self.dirty += 1
        return len(targets)

    
    def forget_user(self, uid):

        removed = 0
        for model in self.models.values():
            k = model.get("kioku") if isinstance(model, dict) else None
            sources = k.get("sources") if isinstance(k, dict) else None
            if not isinstance(sources, dict):
                continue
            targets = [key for key in sources if SharedMemory.source_has_owner(key, uid)]
            if not targets:
                continue
            for key in targets:
                sources.pop(key, None)
            self._rebuild_kioku_sources(k)
            removed += len(targets)
        if removed:
            self.dirty += 1
        return removed

    def learn_fact(self, text):
        text = self.clean(text)
        if len(text) < 2:
            return
        shared_memory.learn(text, store_sentence=False)

    
    def recall_fact(self, question, gid=0):
        return None

    
    def learn_pair(self, q, a):

        k = self.kioku()
        tq = self.tokens(q)[:6]
        ta = self.tokens(a)[:6]
        for x in tq:
            for y in ta:
                if x != y:
                    self._add(k["reply"], x, y)

        k["pairs"] += 1
        self.dirty += 1

    
    def prune(self):
        k = self.kioku()
        for name in ("cooc", "reply", "short"):
            table = k[name]
            for key in list(table):
                inner = table[key]
                if len(inner) > 60:
                    table[key] = dict(sorted(inner.items(), key=lambda kv: -kv[1])[:40])
            if len(table) > 6000:
                for key in [x for x, v in table.items() if sum(v.values()) <= 1]:
                    del table[key]
        if len(k["df"]) > 20000:
            for key in [x for x, v in k["df"].items() if v <= 1]:
                del k["df"][key]
        if len(k["aizuchi"]) > 3000:
            for key in [x for x, v in k["aizuchi"].items() if v <= 1]:
                del k["aizuchi"][key]

    
    def assoc_weights(self, t):
        k = self.kioku()
        w = {}
        for y, c in k["reply"].get(t, {}).items():
            w[y] = w.get(y, 0) + c * 3
        for y, c in k["cooc"].get(t, {}).items():
            w[y] = w.get(y, 0) + c
        return w

    
    def hentou(self, message, gid=0, hints=None):
        self.use(gid)
        out = self.generate(message, hints=hints)
        if not out and hints:
            
            out = self.generate(message)
        if out:
            self.recent = (self.recent + [out])[-20:]
        return out

    
    def topic_chars(self, seed):
        if self.kioku()["n"] < 20:
            return set()
        toks = sorted(self.tokens(seed), key=lambda t: -self.idf(t))[:2]
        return set("".join(toks))

    
    def bias(self, candidates, boost, factor=4):
        if not boost:
            return candidates
        return {c: (w * factor if c in boost else w) for c, w in candidates.items()}

    
    def hint_words(self, hints):

        words = set()
        for hint in hints or ():
            words |= self.content_tokens(hint)
        return words

    
    def copied_from_hints(self, out, hints):

        a = re.sub(r"[\s、。！？!?…~〜]", "", self.clean(out))
        if not a:
            return True
        for hint in hints or ():
            b = re.sub(r"[\s、。！？!?…~〜]", "", self.clean(hint))
            if not b:
                continue
            m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
            if m.size >= 10 or m.size >= 0.6 * len(a):
                return True
        return False

    
    def kioku_setsumei(self, go="", detail=False, gid=0):
        self.use(gid)
        k = self.kioku()
        go = self.clean(go)
        if not go:
            top = sorted(k["df"].items(), key=lambda kv: -kv[1])[:8]
            words = "、".join(f"{w}({c})" for w, c in top) or "まだない"
            aizuchi = sorted(k["aizuchi"].items(), key=lambda kv: -kv[1])[:5]
            ai = "、".join(f"{w}({c})" for w, c in aizuchi if c >= 2) or "まだない"
            return (
                f"このサーバーで覚えた発言: {k['n']}件 / 会話の流れ: {k['pairs']}件\n"
                f"よく出る言葉: {words}\n学んだ相づち: {ai}"
            )

        toks = self.tokens(go)
        x = toks[0] if toks else go
        aw = self.assoc_weights(x)
        lines = []
        if aw:
            rel = sorted(aw.items(), key=lambda kv: -kv[1])[:6]
            shorts = sorted(k["short"].get(x, {}).items(), key=lambda kv: -kv[1])[:4]
            lines.append(f"「{x}」と結びついた言葉: " + "、".join(f"{w}({c})" for w, c in rel))
            if shorts:
                lines.append("返されがちな相づち: " + "、".join(f"{w}({c})" for w, c in shorts))
        else:
            lines.append(f"「{x}」はまだ何も結びついていないぬーん")

        return "\n".join(lines)

    
    def too_close(self, a, b):

        a = re.sub(r"\s+", "", self.clean(a))
        b = re.sub(r"\s+", "", self.clean(b))
        if not a or not b:
            return False
        if a == b:
            return True
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        return len(shorter) >= 12 and shorter in longer and len(shorter) / len(longer) >= 0.65

    
    def pick_sentence(self, seed=""):
        seed = self.clean(seed)

        sentences = list(self.model.get("sentences", []))
        if not sentences:
            return None

        seed = self.clean(seed)
        far = [x for x in sentences if not self.too_close(x, seed)]
        if far:
            sentences = far

                                         
        if len(seed) >= 2:
            grams = list(dict.fromkeys(seed[i:i + 2] for i in range(len(seed) - 1)))[:40]
            scored = []
            for sentence in sentences:
                hit = sum(1 for gram in grams if gram in sentence)
                if hit:
                    scored.append((hit, sentence))
            if scored:
                best = max(hit for hit, _ in scored)
                sentences = [sentence for hit, sentence in scored if hit >= best * 0.6]

        preferred = [
            sentence for sentence in sentences
            if 10 <= len(sentence) <= self.generation_max
        ]

        if preferred:
            sentences = preferred

        return random.choice(sentences)

    
    def kiri(self, text):
        m = None
        for m in owarire.finditer(text):
            pass
        return bool(m) and m.end() == len(text)

    
    def tojiru(self, text, tail_only=False):

        last = 0
        for m in owarire.finditer(text):
            last = m.end()
        if last >= 6 and not tail_only and nuunre.search(text[:last]):
            return text[:last]

        endings = [
            x for x in self.model.get("sentences", [])
            if len(x) <= 6 and nuunre.fullmatch(x.strip("。！？…~〜 "))
        ]
        tail = random.choice(endings) if endings else "ぬーん"
        return (text.rstrip("。！？ ")[:self.generation_max - len(tail)] + tail)

    
    def seiritsu(self, out):

        if not out or len(out) < 3:
            return False
        for a, b in ("「」", "『』", "（）", "()", "[]", "【】"):
            if out.count(a) != out.count(b):
                return False
        particle = "はがをにでとものへ"
        if out[0] in particle + "、。！？)」』）":
            return False
        if re.search(r"[はがをにでとものへ]{2}(?![ぬんー])", out.replace("ぬーん", "")) and re.search(
            r"([はがをにへ])\1", out
        ):
            return False
        if re.search(r"[はがをにでとのへ][、。！？]", out) or re.search(r"、[、。！？]", out):
            return False
        grams = [out[i:i + 4] for i in range(len(out) - 3)]
        if len(grams) != len(set(grams)) and not re.fullmatch(r"[ぬんー！？。…~〜 ]+", out):
            return False
        for seg in re.split(r"[。！？!?…]+", out):
            seg = seg.strip()
            if seg and (len(seg) < 2 or seg[0] in particle):
                return False
        
        
        has_text = bool(re.sub(r"[ぬヌぅぉんンーｰ〜~ぁぃぇっッ！!？?…・、。nNuU\s　]", "", out))
        if has_text:
            if len(nuunre.findall(out)) > 2:
                return False
            if re.search(r"[んンN][ぬヌN]", out):
                return False        
            if re.search(r"(.)\1{5,}", out):
                return False        
        elif re.search(r"(.)\1{8,}", out):
            return False
        return True

    
    def maneka(self, out):

        text = re.sub(r"[\s、。！？!?…~〜]", "", self.clean(out))
        if not text:
            return True
        sources = list(self.model.get("sentences", []))[-400:] + list(self.model.get("talk", []))[-200:]
        for source in sources:
            source = re.sub(r"[\s、。！？!?…~〜]", "", self.clean(source))
            if not source:
                continue
            if text == source:
                return True
            shorter, longer = (text, source) if len(text) <= len(source) else (source, text)
            if len(shorter) >= 12 and shorter in longer and len(shorter) / len(longer) >= 0.65:
                return True
        return False

    
    def _knowledge_text(self, text):
        if "=" in text or "＝" in text:
            parts = shared_memory.chishiki_renkei(text)
            if len(parts) >= 2:
                return "、".join(parts) + "。"
        return text

    
    def sync_knowledge_base(self, facts, removed=0):


        gid = str(next((k for k, value in self.models.items() if value is self.model), "0"))
        base = self.base_model(gid)
        if base.get("_kn_removed", removed) != removed:
            self.base_models.pop(gid, None)
            base = self.base_model(gid)
        base["_kn_removed"] = removed
        done = base.setdefault("_kn_done", set())
        texts = [str(f.get("t", "")).strip() for f in facts if isinstance(f, dict)]
        texts = [t for t in texts if 4 <= len(t) <= 200 and not re.search(r"https?://|<@|<#|@everyone|@here", t)]
        for text in list(dict.fromkeys(texts))[-3000:]:
            if text in done:
                continue
            done.add(text)
            self._add_sentence_to_base(base, self._knowledge_text(text))

    
    def generate(self, seed="", length=None, hints=None):
        seed_clean = self.clean(seed)
        hard_max = self.generation_max if length is None else min(self.generation_max, int(length) + 3)
        best_output = None
        best_score = float("-inf")

        for _ in range(60):
            out = self._generate_once(seed_clean, length, hints)
            if not out:
                continue

            normalized_out = re.sub(r"[\s、。！？!?…~〜]", "", out)
            recent_copy = any(
                normalized_out == re.sub(r"[\s、。！？!?…~〜]", "", old)
                for old in self.recent[-5:]
            )
            hint_copy = bool(hints and self.copied_from_hints(out, hints))
            broken = is_broken_text(out)
            natural = self.seiritsu(out)
            not_copy = not self.maneka(out)
            valid_ending = self.kiri(out)
            has_nuun = bool(nuunre.search(out))

            score = 0.0
            score += 4 if natural else -2
            score += 3 if not broken else -12
            score += 2 if not_copy else -5
            score += 2 if valid_ending else -2
            score += 3 if has_nuun else -3
            score += 2 if not hint_copy else -5
            score += 2 if not recent_copy else -4
            score += 2 if len(out) <= hard_max else -min(10, len(out) - hard_max)
            score += 1 if len(out) >= 6 else -2

            if score > best_score:
                best_score = score
                best_output = out

            if len(out) > hard_max or broken or hint_copy or not natural or not_copy is False or not valid_ending or not has_nuun or recent_copy:
                continue
            return out

        return best_output

    
    def query_topic_overlap(self, seed, candidate):
        seed_tokens = self.content_tokens(seed)
        candidate_tokens = self.content_tokens(candidate)
        if not seed_tokens or not candidate_tokens:
            seed_chars = set(re.sub(r"[\s、。！？!?…~〜]", "", seed))
            candidate_chars = set(re.sub(r"[\s、。！？!?…~〜]", "", candidate))
            return len(seed_chars & candidate_chars) / max(1, len(seed_chars | candidate_chars))
        return len(seed_tokens & candidate_tokens) / max(1, len(seed_tokens | candidate_tokens))

    
    def _generate_once(self, seed="", length=None, hints=None):
        
        
        base = self.base_model()
        if not base.get("word_next") or not base.get("word_starts"):
            return None
        if length is None:
            length = random.randint(18, 70)
        length = max(8, min(int(length), self.generation_max))

        starts = [pair for pair in base["word_starts"] if len(pair) == 2]
        if not starts:
            return None

        
        
        hint_words = self.hint_words(hints)
        if seed or hint_words:
            seed_tokens = self.content_tokens(seed) | hint_words
            indexed_candidates = {}
            topic_index = base.get("topic_index", {})
            for token in seed_tokens:
                for entry in topic_index.get(token, ()):
                    indexed_candidates[entry] = None
            topic_starts = []
            for start_pair, candidate_tokens in indexed_candidates:
                overlap = len(seed_tokens & candidate_tokens) / max(1, len(seed_tokens | candidate_tokens))
                if overlap >= 0.16:
                    topic_starts.append((overlap, start_pair))
            if topic_starts:
                best_score = max(item[0] for item in topic_starts)
                near_best = [pair for score, pair in topic_starts if score >= best_score * 0.75]
                words = list(random.choice(near_best))
            else:
                words = list(random.choice(starts))
        else:
            words = list(random.choice(starts))
        natural = False
        max_tokens = max(12, min(80, length * 2))

        for _ in range(max_tokens):
            current = "".join(words)
            if len(current) >= max(12, int(length * 0.45)) and current[-1:] in "。！？!?…~〜":
                natural = True
                break
            candidates = None
            if len(words) >= 2:
                candidates = base.get("word_next2", {}).get(self.word_key(words[-2:]))
                
                
                if candidates and len(candidates) < 2 and random.random() < self.backoff_p:
                    candidates = None
            if not candidates:
                candidates = base["word_next"].get(self.word_key(words[-1:]))
            if not candidates:
                break
            if hint_words:
                
                candidates = self.bias(candidates, hint_words, 2)
            nxt = self.weighted_choice(candidates)
            if not nxt:
                break
            words.append(nxt)
            if len("".join(words)) >= length and nxt and re.fullmatch(r"[。！？!?…~〜]+", nxt):
                natural = True
                break
            if len("".join(words)) >= self.generation_max:
                break

        output = "".join(words).replace("\\n", "").replace("\\r", "")
        output = re.sub(r"\s+", " ", output).strip()
        if not output:
            return None
        return output[:self.generation_max]

    
    def finish(self, output, natural):
        if not output or not natural:
            return None
        if output[-1] not in "。！？!?…~〜":
            return None
        if not nuunre.search(output):
            return None
        return output

    
    def learn_conversation(self, message, response, source=None):
        if message:
            self.learn_vocabulary(message, source=source)
        if response:
            self.learn_vocabulary(response, source=source)

    
    def save_if_needed(self, every=30):

        if self.dirty < every or self.saving:
            return
        self.saving = True

        def run():
            try:
                with nuun_lock:
                    self.save()
            except Exception as error:
                print(f"model.json を保存できません: {error}")
            finally:
                self.saving = False

        threading.Thread(target=run, daemon=True).start()


nuun = NuunGakushu()
nuun.yomu_settings()    


def yobareta(m):
    if bot.user in m.mentions:
        return True
    ref = m.reference.resolved if m.reference else None
    return isinstance(ref, discord.Message) and ref.author == bot.user


                                                                                                 
consentfile = deeta / "consent.json"
CONSENT_VER = 1                                         

KIYAKU_TEXT = (
    "**ぬーん 学習についての利用規約・プライバシーポリシー**\n"
    "\n"
    "**1. 学習する内容**\n"
    "同意した人がサーバーで送ったメッセージ(URL・メンション・コードブロックは除く)から、語彙・言葉のつながり・会話の流れを学習し、ぬーんの返信を作る材料に使うぬーん。\n"
    "\n"
    "**2. 保存する情報**\n"
    "・メッセージの一部(文の断片)を、意味検索のために保存します\n"
    "・それを、送った人のユーザーID(数字)と、サーバー・チャンネル・スレッドのIDに紐づけて記録します\n"
    "・ユーザー名やアイコンは学習データには保存しません\n"
    "・学習内容は全サーバー共通で使われ、他のサーバーでの返信に影響することがあります\n"
    "・保存したデータはBotの管理者が閲覧できます。個人情報や秘密は送らないでください\n"
    "\n"
    "**3. 対象外**\n"
    "DM、`/`や`!`で始まるメッセージ、学習除外されたチャンネル、Botの発言\n"
    "\n"
    "**4. 同意しない場合**\n"
    "あなたの発言は学習せず、保存もしません。ぬーんの返信やガチャなどはこれまで通り使えます。\n"
    "\n"
    "**5. 削除と撤回**\n"
    "`/自分の学習削除` で、あなたの発言から学習した内容を消せます。`/学習同意撤回` で同意を取り消し、同じく削除します。"
    "ID記録を始める前に学習された分は、誰のものか判別できず消せないことがあります。\n"
    "\n"
    "**6. 規約の変更**\n"
    "内容を変えたときは、もう一度同意をお願いします。\n"
    "\n"
    "Discordを利用できる年齢に達していて、上記に同意する場合だけ「同意する」を押してください。"
)


def consentyomu():
    if not consentfile.is_file():
        return {}
    try:
        data = json.loads(yomutext(consentfile))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def consentkaku():
    tmp = consentfile.with_suffix(".tmp")
    kakutext(tmp, json.dumps(consent, ensure_ascii=False, indent=2))
    tmp.replace(consentfile)


consent = consentyomu()                                                                                 


def consented(uid):
    e = consent.get(str(uid))
    return isinstance(e, dict) and e.get("v") == CONSENT_VER


async def kiyaku_prompt(hatsu):

    key = str(hatsu.author.id)
    e = consent.setdefault(key, {"v": 0, "t": 0, "p": 0})
    if e.get("off") or e.get("p"):                                     
        return
    e["p"] = time.time()                                
    try:
        consentkaku()
    except OSError as error:
        print(f"consent.json を保存できません: {error}")
    try:
        await hatsu.channel.send(
            f"{hatsu.author.mention} ぬーんは発言から学習するぬーん。学習してよいか、規約を読んで選んでほしいぬーん\n"
            "-# 同意するまでは、あなたの発言は学習しません。ぬーんの返信はこれまで通り使えます。",
            view=KiyakuOpenView(),
            allowed_mentions=discord.AllowedMentions(users=[hatsu.author]),
        )
    except discord.HTTPException as error:
        print(f"同意の案内を送信できません: channel_id={hatsu.channel.id}: {error}")


class KiyakuAgreeView(discord.ui.View):


    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="同意する", style=discord.ButtonStyle.success, custom_id="nuun_kiyaku_agree")
    async def agree(self, interaction, button):
        e = consent.setdefault(str(interaction.user.id), {"v": 0, "t": 0, "p": 0})
        e.update({"v": CONSENT_VER, "t": time.time(), "off": 1})                                       
        consentkaku()
        await interaction.response.edit_message(
            content="同意ありがとうぬーん。これからあなたの発言を学習するぬーん\n"
                    "-# やめたいときは `/学習同意撤回`、学習した内容を消したいときは `/自分の学習削除`",
            view=None,
        )

    @discord.ui.button(label="同意しない", style=discord.ButtonStyle.secondary, custom_id="nuun_kiyaku_disagree")
    async def disagree(self, interaction, button):
        e = consent.setdefault(str(interaction.user.id), {"v": 0, "t": 0, "p": 0})
        e.update({"v": 0, "off": 1})                  
        consentkaku()
        await interaction.response.edit_message(
            content="わかったぬーん。あなたの発言は学習しないぬーん\n-# 気が変わったら `/規約` から同意できます",
            view=None,
        )


class KiyakuOpenView(discord.ui.View):


    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="規約を確認する", style=discord.ButtonStyle.primary, custom_id="nuun_kiyaku_open")
    async def open(self, interaction, button):
        await interaction.response.send_message(KIYAKU_TEXT, view=KiyakuAgreeView(), ephemeral=True)


async def gakushu_keshite(uid):

    for cid_, v in list(recent_human_messages.items()):                          
        if v[0] == uid:
            recent_human_messages.pop(cid_, None)

    def apply():
        with nuun_lock:
            kioku = nuun.forget_user(uid)
            if kioku:
                nuun.save()
        result = shared_memory.forget_user(uid)
        vec = vec_index.forget_user(uid)
        shared_memory.save()
        return kioku, result, vec

    return await asyncio.to_thread(apply)


def gakushu_houkoku(kioku, result, vec):
    if not (kioku or vec or any(result.values())):
        return "あなたのIDで記録された学習内容はなかったぬーん\n-# ID記録を始める前に学習した分は、誰の発言か分からないので消せないぬーん"
    return (
        "あなたの発言から学習した内容を忘れたぬーん\n"
        f"語彙・関連語の記録 {result['sources']}件 / 記憶 {kioku}件 / 意味検索 {vec}件\n"
        f"教えた知識 {result['facts']}件 / 別名 {result['alias']}件"
    )


class Bot(commands.Bot):
    async def _event_loop_watchdog(self, interval=0.5, threshold=1.0):

        loop = asyncio.get_running_loop()
        while not self.is_closed():
            expected = loop.time() + interval
            await asyncio.sleep(interval)
            lag = loop.time() - expected
            if lag >= threshold:
                print(f"[EVENT LOOP WARNING] lag={lag:.3f}s threshold={threshold:.3f}s")

    async def setup_hook(self):
        self.add_view(KiyakuOpenView())
        self.add_view(KiyakuAgreeView())
        await self.tree.sync()
        self.loop_watchdog_task = asyncio.create_task(self._event_loop_watchdog())
        self.vec_task = asyncio.create_task(vec_index.start(shared_memory))
        self.junbi_task = asyncio.create_task(asyncio.to_thread(nuun_junbi))

    async def close(self):
        watchdog = getattr(self, "loop_watchdog_task", None)
        if watchdog is not None:
            watchdog.cancel()
            await asyncio.gather(watchdog, return_exceptions=True)
        try:
            nuunchankaku()
        except Exception as error:
            print(f"nuunchan.json を保存できません: {error}")
        shared_memory.save()
        try:
            nuun.save()
        except Exception as error:
            print(f"model.json を保存できません: {error}")
        await asyncio.to_thread(vec_index.save)
        await super().close()


intents = discord.Intents.default()
                                                                   
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents)


nuunchang = app_commands.Group(name="ぬーんちゃん", description="あなたのぬーんちゃん", guild_only=True)
bot.tree.add_command(nuunchang)


@nuunchang.command(name="呼び方", description="ぬーんちゃんの呼び方を設定・確認")
async def nuunchanyobikata_cmd(yobi, namae: Optional[str] = None):
    u = nuunchanuser(yobi.user.id)
    if namae is None:
        return await yobi.response.send_message(f"あなたのぬーんちゃんの呼び方は「{u['yobikata']}」ぬーん", ephemeral=True)
    namae = namae.strip()[:30]
    if not namae:
        return await yobi.response.send_message("呼び方が空っぽぬーん", ephemeral=True)
    u["yobikata"] = namae
    nuunchankaku()
    await yobi.response.send_message(f"これから「{namae}」と呼ばれたら出てくるぬーん！", ephemeral=True)


@bot.tree.command(name="ぬーんランキング", description="ぬーんランキングを見る")
async def nuunranking(yobi):
    await yobi.response.defer()
    ranking_text = await nuunchanranktext(yobi.user.id, yobi.guild)
    try:
        await yobi.followup.send(ranking_text)
    except discord.HTTPException as error:
        print(f"ランキング送信エラー: {error}")

globalchat = app_commands.Group(name="グローバルチャット", description="サーバー間でチャットを共有", guild_only=True)
bot.tree.add_command(globalchat)


@globalchat.command(name="参加", description="このチャンネルをグローバルチャットに参加させる")
async def globalchat_join(yobi):
    if not kengen(yobi):
        return await yobi.response.send_message("管理権限が必要ぬーん", ephemeral=True)
    globalchat_add(yobi.channel.id)
    await yobi.response.send_message("このチャンネルをグローバルチャットに参加させたぬーん")


@globalchat.command(name="退出", description="このチャンネルをグローバルチャットから退出させる")
async def globalchat_leave(yobi):
    if not kengen(yobi):
        return await yobi.response.send_message("管理権限が必要ぬーん", ephemeral=True)
    if globalchat_remove(yobi.channel.id):
        await yobi.response.send_message("このチャンネルをグローバルチャットから退出させたぬーん")
    else:
        await yobi.response.send_message("このチャンネルはグローバルチャットに入っていないぬーん", ephemeral=True)


@globalchat.command(name="確認", description="グローバルチャットの登録状況を確認")
async def globalchat_check(yobi):
    groups = []
    for cid in globalchat_channels():
        ch = bot.get_channel(int(cid))
        if ch is None:
            continue
        guild = getattr(ch, "guild", None)
        if guild is None:
            continue
        name = getattr(ch, "name", "不明")
        groups.append(f"{guild.name}\n→ {name}")
    text = "\n\n".join(groups) if groups else "なし"
    await yobi.response.send_message("グローバルチャット参加チャンネル\n\n" + text, ephemeral=True)


banpu = app_commands.Group(name="バンプ", description="Bump通知の設定", guild_only=True)
hannou = app_commands.Group(name="反応", description="このチャンネルの自動反応", guild_only=True)
for g in (banpu, hannou):
    bot.tree.add_command(g)


@banpu.command(name="設定", description="Bump通知を設定")
async def banpukae(yobi, joutai: Kiri):
    if not kengen(yobi):
        return await yobi.response.send_message("管理権限が必要ぬーん", ephemeral=True)
    saba(yobi)["banpu"] = joutai == "オン"
    kaku()
    await yobi.response.send_message(f"バンプ通知を{joutai}にしたぬーん")


@banpu.command(name="確認", description="Bump通知を確認")
async def banpumi(yobi):
    await yobi.response.send_message(f"バンプ通知は{onofu(saba(yobi)['banpu'])}ぬーん")


@hannou.command(name="設定", description="自動反応を設定")
@app_commands.describe(joutai="オンかオフ", basho="対象のチャンネル/フォーラム/スレッド(省略するとこのチャンネル)")
async def hannoukae(yobi, joutai: Kiri, basho: Optional[Union[discord.TextChannel, discord.ForumChannel, discord.Thread]] = None):
    if not kengen(yobi):
        return await yobi.response.send_message("管理権限が必要ぬーん", ephemeral=True)
    target = basho or yobi.channel
    if getattr(target, "guild", None) is None or target.guild.id != yobi.guild.id:
        return await yobi.response.send_message("このサーバーの場所を指定してほしいぬーん", ephemeral=True)
    saba(yobi)["hannou"][str(target.id)] = joutai == "オン"
    kaku()
    await yobi.response.send_message(f"{target.mention} の自動反応を{joutai}にしたぬーん")


class hanview(discord.ui.View):
    def __init__(self, yobi):
        super().__init__(timeout=180)
        self.yuzahyo = yobi.user.id
        self.sabahyo = yobi.guild.id
        self.chid = []

    async def interaction_check(self, interaction):
        if interaction.user.id != self.yuzahyo:
            await interaction.response.send_message("この設定画面を開いた人だけ操作できるぬーん", ephemeral=True)
            return False
        return True

    @discord.ui.select(cls=discord.ui.ChannelSelect, channel_types=[discord.ChannelType.text, discord.ChannelType.news, discord.ChannelType.forum, discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.news_thread], min_values=1, max_values=5, placeholder="切り替えるチャンネルを最大5個選択")
    async def erabu(self, interaction, select):
        self.chid = [x.id for x in select.values]
        names = "、".join(f"#{x.name}" for x in select.values)
        await interaction.response.edit_message(content=f"選択中: {names}\n下のボタンで選択したチャンネルをまとめて切り替えられるぬーん", view=self)

    async def kirikae(self, interaction, joutai):
        if not self.chid:
            return await interaction.response.send_message("先にチャンネルを選択してほしいぬーん", ephemeral=True)
        saba = settei.setdefault(str(self.sabahyo), {"banpu": True, "hannou": {}})
        saba.setdefault("hannou", {})
        for cid in self.chid:
            saba["hannou"][str(cid)] = joutai
        kaku()
        hyoki = "オン" if joutai else "オフ"
        await interaction.response.edit_message(content=f"{len(self.chid)}チャンネルの自動反応を{hyoki}にしたぬーん", view=None)

    @discord.ui.button(label="選択したチャンネルをオン", style=discord.ButtonStyle.success, row=1)
    async def on(self, interaction, button):
        await self.kirikae(interaction, True)

    @discord.ui.button(label="選択したチャンネルをオフ", style=discord.ButtonStyle.secondary, row=1)
    async def off(self, interaction, button):
        await self.kirikae(interaction, False)


@hannou.command(name="複数設定", description="最大5チャンネルの自動反応をまとめて設定")
async def hannoufukusu(yobi):
    if not kengen(yobi):
        return await yobi.response.send_message(NASHI, ephemeral=True)
    await yobi.response.send_message("チャンネルを選択してからオン・オフを選んでほしいぬーん", view=hanview(yobi), ephemeral=True)


@hannou.command(name="全部オン", description="サーバー内の全チャンネル・フォーラム・スレッドで自動反応を有効化")
async def hannouzenon(yobi):
    if not kengen(yobi):
        return await yobi.response.send_message(NASHI, ephemeral=True)
    hannou = saba(yobi)["hannou"]
    basho = hannoubasho(yobi.guild)
    for channeru in basho:
        hannou[str(channeru.id)] = True
    kaku()
    await yobi.response.send_message(f"{len(basho)}か所(チャンネル・フォーラム・スレッド)の自動反応を全部オンにしたぬーん", ephemeral=True)


@hannou.command(name="全部オフ", description="サーバー内の全チャンネル・フォーラム・スレッドで自動反応を無効化")
async def hannouzenoff(yobi):
    if not kengen(yobi):
        return await yobi.response.send_message(NASHI, ephemeral=True)
    hannou = saba(yobi)["hannou"]
    basho = hannoubasho(yobi.guild)
    for channeru in basho:
        hannou[str(channeru.id)] = False
    kaku()
    await yobi.response.send_message(f"{len(basho)}か所(チャンネル・フォーラム・スレッド)の自動反応を全部オフにしたぬーん", ephemeral=True)


@hannou.command(name="確認", description="自動反応の状態を確認")
async def hannoumi(yobi):
    await yobi.response.send_message(
        f"このチャンネルの自動反応は{onofu(han(yobi))}、{ritsusetsu(yobi)}ぬーん"
    )


def hannoubasho(guild):
    forums = [c for c in guild.channels if isinstance(c, discord.ForumChannel)]
    return [*guild.text_channels, *forums, *guild.threads]


def kengen(yobi):
    return yobi.user.id == learningowner or yobi.permissions.manage_guild


NASHI = "管理権限が必要ぬーん"


@hannou.command(name="個人確率", description="あなたへの返信確率を設定(0〜100)")
async def hannoukojin(yobi, parasento: Optional[app_commands.Range[int, 0, 100]] = None):
    if parasento is None:
        v = ritsukojin(yobi)
        if v is None:
            return await yobi.response.send_message(
                "あなたへの返信確率は30パーセントぬーん（個人設定が未設定のため）", ephemeral=True
            )
        return await yobi.response.send_message(
            f"あなたへの返信確率は{v}パーセントぬーん", ephemeral=True
        )
    saba(yobi).setdefault("ritsu_kojin", {})[str(yobi.user.id)] = int(parasento)
    kaku()
    await yobi.response.send_message(f"あなたへの返信確率を{parasento}パーセントにしたぬーん", ephemeral=True)


@hannou.command(name="個人確率リセット", description="あなたへの返信確率の設定を消す")
async def hannoukojinkeshi(yobi):
    saba(yobi).setdefault("ritsu_kojin", {}).pop(str(yobi.user.id), None)
    kaku()
    await yobi.response.send_message("あなたへの返信確率の設定を消したぬーん", ephemeral=True)


@hannou.command(name="一覧", description="反応一覧")
async def hannouichi(yobi):
    if not kotoba["hannou"]:
        return await yobi.response.send_message("反応は登録されていないぬーん")
    await yobi.response.send_message("\n".join(
        f"{n} {'キーワード' if r.get('kiwado') else '常時'} "
        f"{r.get('ritsu', 0)}パーセント {r.get('bun') or '画像のみ'}"
        for n, r in enumerate(kotoba["hannou"], 1)
    ))


@bot.tree.command(name="ぬーんガチャ", description="ぬーんガチャを引く")
async def gacha(yobi):
    await yobi.response.send_message(**hiku())


@bot.tree.command(name="設定確認", description="サーバー設定を確認")
@app_commands.guild_only()
async def miru(yobi):
    await yobi.response.send_message(
        f"バンプ通知は{onofu(saba(yobi)['banpu'])}ぬーん\n"
        f"このチャンネルの自動反応は{onofu(han(yobi))}、{ritsusetsu(yobi)}ぬーん"
    )


chishiki = app_commands.Group(name="知識", description="ぬーんに知識を覚えさせる", guild_only=True)
bot.tree.add_command(chishiki)


def chishikiomoji(text, n=90):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= n else text[:n - 1] + "…"


@chishiki.command(name="教える", description="ぬーんに知識を1つ教える(全サーバー共通)")
async def chishikioshieru(yobi, shugo: app_commands.Range[str, 1, 20], naiyou: app_commands.Range[str, 1, 140]):
    if not consented(yobi.user.id):
        return await yobi.response.send_message("知識を覚えるには、学習の規約への同意が必要ぬーん\n以下を読んで同意してほしいぬーん\n\n" + KIYAKU_TEXT, view=KiyakuAgreeView(), ephemeral=True)
    shugo, naiyou = shugo.strip(), naiyou.strip()
    if re.search(r"https?://|<@|<#|@everyone|@here", shugo + naiyou):
        return await yobi.response.send_message("URLやメンションは覚えられないぬーん", ephemeral=True)
    text = naiyou if SharedMemory.normalize(shugo) in SharedMemory.normalize(naiyou) else f"{shugo}は{naiyou}"
    r = shared_memory.chishiki_oboeru(text, yobi.user.id, yobi.guild.id, subject=shugo, explicit=True, cid=yobi.channel.id if not isinstance(yobi.channel, discord.Thread) else yobi.channel.parent_id, tid=yobi.channel.id if isinstance(yobi.channel, discord.Thread) else 0)
    if r is None:
        return await yobi.response.send_message("覚えられなかったぬーん", ephemeral=True)
    shared_memory.save_async()
    await yobi.response.send_message(f"覚えたぬーん({r})：{text}")


@chishiki.command(name="忘れる", description="キーワードを含む知識を消す(管理権限なら自分のサーバーで覚えたもの、なければ自分だけが教えたもの)")
async def chishikiwasureru(yobi, kiwado: app_commands.Range[str, 1, 40]):
    n = shared_memory.chishiki_wasureru(kiwado, yobi.user.id, yobi.guild.id, kengen(yobi))
    if not n:
        return await yobi.response.send_message("消せる知識がなかったぬーん", ephemeral=True)
    shared_memory.save_async()
    await yobi.response.send_message(f"「{kiwado}」を含む知識を{n}件忘れたぬーん")


@chishiki.command(name="一覧", description="覚えている知識を見る")
async def chishikiichiran(yobi, kiwado: Optional[str] = None):
    if kiwado:
        hits = shared_memory.chishiki_kensaku(kiwado)
        if not hits:
            return await yobi.response.send_message("その知識はまだないぬーん", ephemeral=True)
        lines = [f"{'' if f['x'] else '・'}{chishikiomoji(f['t'])}" for f in reversed(hits[-12:])]
        return await yobi.response.send_message(
            f"{len(hits)}件ヒット(新しい順に最大12件、=教えてもらったもの)\n" + "\n".join(lines), ephemeral=True
        )
    total = len(shared_memory.facts)
    if not total:
        return await yobi.response.send_message("まだ何も覚えていないぬーん", ephemeral=True)
    explicit = sum(1 for f in shared_memory.facts if f["x"])
    top = sorted(shared_memory.chishiki_idx.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]
    await yobi.response.send_message(
        f"全サーバー共通で{total}件(うち教えてもらったもの{explicit}件)覚えているぬーん\n"
        + "、".join(f"{k}({len(v)})" for k, v in top),
        ephemeral=True,
    )


@chishiki.command(name="検索", description="意味検索の結果と類似度を確認する(しきい値の調整用)")
async def chishikikensaku(yobi, bun: app_commands.Range[str, 1, 200]):
    head = f"意味検索: {vec_index.state}({len(vec_index.items)}件)"
    found = vec_index.search(bun)
    if found is None:
        return await yobi.response.send_message(head + "\n今は語の重なりで探しているぬーん", ephemeral=True)
    lines = []
    for kind, label, limit in (("f", "知識", vec_fact_min), ("t", "会話", vec_turn_min), ("m", "自動学習", vec_fact_min)):
        for score, it in found[kind][:3]:
            body = it["t"] if kind != "t" else f"{it['t']} → {it.get('a', '')}"
            lines.append(f"{'' if score >= limit else '・'}{score:.2f} [{label}] {chishikiomoji(body, 70)}")
    if not lines:
        lines.append("近いものはまだないぬーん")
    await yobi.response.send_message(
        head + f"\n=ヒントに使う(知識{vec_fact_min}以上 / 会話{vec_turn_min}以上)\n" + "\n".join(lines), ephemeral=True
    )


@bot.tree.command(name="学習データ全削除", description="メモリーファイルとモデルファイルを完全に削除してBOTを再起動する")
@app_commands.guild_only()
async def gakushidatazen_sakujo(yobi):
    global data_purged
    if yobi.user.id != learningowner:
        return await yobi.response.send_message("このコマンドを実行できるユーザーではないぬーん", ephemeral=True)
    data_purged = True
    try:
        with vec_index.lock:
            vec_index.items = []
            vec_index.mat = None
            vec_index.pending_items = []
            vec_index.pending_vecs = []
            vec_index.todo = []
            vec_index.keys = set()
            vec_index.dirty = 0
        targets = {
            shared_memory.path,
            modelfile,
            shared_memory.path.with_suffix(".tmp"),
            modelfile.with_suffix(".tmp"),
            deeta / "memory_vec.npz",
            deeta / "memory_vec.npy",
            deeta / "model_vec.npz",
            deeta / "model_vec.npy",
        }
        targets.update(deeta.glob("memory*.npz"))
        targets.update(deeta.glob("memory*.npy"))
        targets.update(deeta.glob("model*.npz"))
        targets.update(deeta.glob("model*.npy"))
        for path in targets:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        await yobi.response.send_message("メモリーファイルとモデルファイルとNPZ NPYキャッシュを完全に削除したぬーん\nこれからBOTを再起動するぬーん", ephemeral=True)
        await asyncio.sleep(1.0)
        for path in targets:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        os.execv(sys.executable, [sys.executable, *sys.argv])
    except Exception as error:
        data_purged = False
        if not yobi.response.is_done():
            await yobi.response.send_message(f"えらーぬーん（{type(error).__name__}: {error}）-# お手数ですがふにゃくんまでご連絡いただけると幸いです。", ephemeral=True)
        else:
            try:
                await yobi.followup.send(f"えらーぬーん（{type(error).__name__}: {error}）-# お手数ですがふにゃくんまでご連絡いただけると幸いです。", ephemeral=True)
            except Exception:
                pass


@bot.tree.command(name="学習除外", description="指定した場所を学習対象から外して既知の場所情報を忘れる")
@app_commands.guild_only()
@app_commands.describe(serverid="サーバーID", channelid="チャンネルID 0ならサーバー全体", threadid="スレッドID 0ならチャンネル全体")
async def gakushujojo(yobi, serverid: str, channelid: str = "0", threadid: str = "0"):
    try:
        serverid = int(serverid)
        channelid = int(channelid)
        threadid = int(threadid)
    except (TypeError, ValueError):
        return await yobi.response.send_message("IDが正しくないぬーん", ephemeral=True)
    if yobi.user.id != learningowner:
        return await yobi.response.send_message("このコマンドを実行できるユーザーではないぬーん", ephemeral=True)
    if serverid <= 0 or channelid < 0 or threadid < 0:
        return await yobi.response.send_message("IDが正しくないぬーん", ephemeral=True)
    if threadid and not channelid:
        channelid = 0
    await yobi.response.defer(ephemeral=True)

    def apply():
        target = learningtarget(serverid, channelid, threadid)
        learningexclude[:] = [x for x in learningexclude if not (str(x.get("g")) == target["g"] and str(x.get("c", 0)) == target["c"] and str(x.get("t", 0)) == target["t"])]
        learningexclude.append(target)
        learningexcludekaku(learningexclude)
        forgot = shared_memory.chishiki_jojo_wasureru(serverid, channelid, threadid)
        shared_memory.forget_source(serverid, channelid, threadid)
        vec_index.forget_source(serverid, channelid, threadid)
        with nuun_lock:
            if not channelid and not threadid:
                gid = str(serverid)
                current = nuun.models.get(gid)
                nuun.models.pop(gid, None)
                nuun.base_models.pop(gid, None)
                if current is not None and nuun.model is current:
                    nuun.model = nuun.sinki()
                nuun.dirty += 1
                nuun.save()
            else:
                nuun.forget_source(serverid, channelid, threadid)
                nuun.save()
        shared_memory.save()
        return forgot

    forgot = await asyncio.to_thread(apply)
    scope = "サーバー" if not channelid and not threadid else "チャンネル" if not threadid else "スレッド"
    await yobi.followup.send(f"{scope}を学習対象から除外したぬーん\n忘れた保存済み知識 {forgot}件\n語彙と関連語の学習履歴も対象範囲から取り除いたぬーん", ephemeral=True)


@bot.tree.command(name="自分の学習削除", description="ぬーんが自分の発言から学習した内容(語彙・関連語・記憶・意味検索・教えた知識)を全サーバー分すべて忘れる")
async def jibungakushusakujo(yobi):
    await yobi.response.defer(ephemeral=True)
    text = gakushu_houkoku(*await gakushu_keshite(yobi.user.id))
    if consented(yobi.user.id):
        text += "\n-# 同意は残っているので、これから先の発言はまた学習するぬーん(止めるなら /学習同意撤回)"
    await yobi.followup.send(text, ephemeral=True)


@bot.tree.command(name="学習同意撤回", description="学習への同意を取り消して、自分の発言から学習した内容も全部忘れる")
async def gakushudouiteikkai(yobi):
    await yobi.response.defer(ephemeral=True)
    consent[str(yobi.user.id)] = {"v": 0, "t": 0, "p": time.time(), "off": 1}
    consentkaku()
    text = gakushu_houkoku(*await gakushu_keshite(yobi.user.id))
    await yobi.followup.send("学習への同意を取り消したぬーん。これから先の発言は学習しないぬーん\n" + text + "\n-# また学習してよければ `/規約` から同意できます", ephemeral=True)


@bot.tree.command(name="規約", description="学習についての利用規約・プライバシーポリシーを見て、同意するか選ぶ")
async def kiyakuhyouji(yobi):
    if consented(yobi.user.id):
        return await yobi.response.send_message(KIYAKU_TEXT.rsplit("\n\n", 1)[0] + "\n\n-# すでに同意済みぬーん。取り消すときは `/学習同意撤回`", ephemeral=True)
    await yobi.response.send_message(KIYAKU_TEXT, view=KiyakuAgreeView(), ephemeral=True)


@chishiki.command(name="履歴学習", description="チャンネルの過去発言から知識を学習する(管理権限が必要)")
async def chishikirireki(yobi, channel: Optional[discord.TextChannel] = None, kensuu: app_commands.Range[int, 10, 1000] = 200):
    if not kengen(yobi):
        return await yobi.response.send_message(NASHI, ephemeral=True)
    channel = channel or yobi.channel
    if learningexcluded(yobi.guild.id, channel.id, getattr(channel, "parent_id", 0) or channel.id):
        return await yobi.response.send_message("この場所は学習対象から除外されているぬーん", ephemeral=True)
    me = yobi.guild.me
    if not isinstance(channel, discord.TextChannel) or not channel.permissions_for(me).read_message_history:
        return await yobi.response.send_message("そのチャンネルの履歴を読めないぬーん", ephemeral=True)
    if yobi.guild.id in chishiki_crawling:
        return await yobi.response.send_message("このサーバーはもう履歴学習中ぬーん", ephemeral=True)
    chishiki_crawling.add(yobi.guild.id)
    await yobi.response.defer(thinking=True)
    new = upd = seen = 0
    try:
        async for m in channel.history(limit=kensuu):
            if m.author.bot or not m.content or m.content.startswith(("/", "!")) or not consented(m.author.id):
                continue
            if is_gibberish(nuun.clean(m.content)):
                continue
            seen += 1
            if seen % 10 == 0:
                await asyncio.sleep(0)
            a, b = shared_memory.chishiki_manabu(m.content, m.author.id, yobi.guild.id, channel.id if not isinstance(channel, discord.Thread) else channel.parent_id, channel.id if isinstance(channel, discord.Thread) else 0)
            new += a
            upd += b
    except discord.Forbidden:
        return await yobi.followup.send("履歴を読む権限が途中でなくなったぬーん")
    finally:
        chishiki_crawling.discard(yobi.guild.id)
        shared_memory.save()
    await yobi.followup.send(f"{channel.mention} の{seen}件を読んで、語彙と関連語を{new}件分取り込んだぬーん")


@bot.event
async def on_raw_reaction_add(payload):
    await globalchat_reaction(payload, True)


@bot.event
async def on_raw_reaction_remove(payload):
    await globalchat_reaction(payload, False)


@bot.event
async def on_message_edit(before, after):
    if before.content == after.content and len(before.attachments) == len(after.attachments):
        return
    await globalchat_edit(after)


@bot.event
async def on_message_delete(message):
    await globalchat_delete(message)


@bot.event
async def on_ready():
    print(f"ログインしました {bot.user}")
    print(f"参加サーバー: {len(bot.guilds)}")
    for guild in sorted(bot.guilds, key=lambda g: g.name.casefold()):
        print(guild.name)


@bot.event
async def on_message(hatsu):
    if not hatsu.guild:
        return

    if hatsu.author.bot and hatsu.author.id != bot.user.id:
        if hatsu.author.id == banpuid and saba(hatsu)["banpu"]:
            await okuru(hatsu.channel, kotoba.get("banpu") or {})
        return

    try:
        await globalchat_relay(hatsu)
    except Exception as error:
        print(f"グローバルチャット中継エラー: {type(error).__name__}: {error}")

    if hatsu.author.bot:
        return

    gacha_text = re.sub(r"[\s　、。！？!?]", "", hatsu.content or "")
    if gachago in gacha_text:
        try:
            await hatsu.channel.send(**hiku())
        except discord.Forbidden:
            print(f"ぬーんガチャを送信できません: channel_id={hatsu.channel.id}。Botにメッセージ送信権限がありません。")
        except discord.HTTPException as error:
            print(f"ぬーんガチャ送信エラー: {error}")
        await bot.process_commands(hatsu)
        return

    context_for_recall = recent_human_messages.get(hatsu.channel.id)

    learn_target = bool(hatsu.content) and not hatsu.content.startswith(("/", "!")) and not learningexcluded(hatsu.guild.id, hatsu.channel.id if not isinstance(hatsu.channel, discord.Thread) else hatsu.channel.parent_id, hatsu.channel.id if isinstance(hatsu.channel, discord.Thread) else 0)
    if learn_target and not consented(hatsu.author.id):
        await kiyaku_prompt(hatsu)                          
    if learn_target and consented(hatsu.author.id):
        learned_text = nuun.clean(hatsu.content)
        if is_gibberish(learned_text):
            learned_text = ""       
        if len(learned_text) >= 2:
            channel_id = hatsu.channel.id if not isinstance(hatsu.channel, discord.Thread) else hatsu.channel.parent_id
            thread_id = hatsu.channel.id if isinstance(hatsu.channel, discord.Thread) else 0
            source = (hatsu.guild.id, channel_id, thread_id)
            _learn_started = time.perf_counter()
            shared_memory.chishiki_manabu(hatsu.content, hatsu.author.id, *source)
            _learn_elapsed = time.perf_counter() - _learn_started
            if _learn_elapsed >= 0.25:
                print(f"[SLOW SYNC] shared_memory.chishiki_manabu={_learn_elapsed:.3f}s guild={hatsu.guild.id}")
            await nuun_manabu(hatsu.guild.id, learned_text, source=source + (hatsu.author.id,))
        if len(learned_text) >= 4:

            referenced = hatsu.reference.resolved if hatsu.reference else None
            if (
                isinstance(referenced, discord.Message)
                and not referenced.author.bot
                and consented(referenced.author.id)
                and referenced.author.id != hatsu.author.id
                and referenced.content
            ):
                _turn_started = time.perf_counter()
                shared_memory.learn_turn(referenced.content, learned_text, source=source, q_uid=referenced.author.id, a_uid=hatsu.author.id)
                _turn_elapsed = time.perf_counter() - _turn_started
                if _turn_elapsed >= 0.25:
                    print(f"[SLOW SYNC] shared_memory.learn_turn={_turn_elapsed:.3f}s guild={hatsu.guild.id}")
            else:
                previous = recent_human_messages.get(hatsu.channel.id)
                now_for_learning = time.monotonic()
                if (
                    previous
                    and previous[0] != hatsu.author.id
                    and now_for_learning - previous[2] <= 90
                ):
                    _turn_started = time.perf_counter()
                    shared_memory.learn_turn(previous[1], learned_text, source=source, q_uid=previous[0], a_uid=hatsu.author.id)
                    _turn_elapsed = time.perf_counter() - _turn_started
                    if _turn_elapsed >= 0.25:
                        print(f"[SLOW SYNC] shared_memory.learn_turn={_turn_elapsed:.3f}s guild={hatsu.guild.id}")

            recent_human_messages[hatsu.channel.id] = (
                hatsu.author.id,
                learned_text,
                time.monotonic(),
            )

    if shared_memory.dirty:
        shared_memory.save_async()    

    now = time.monotonic()
    q = renpo[hatsu.author.id]
    while q and now - q[0] >= renpo_window:
        q.popleft()
    if len(q) >= renpo_limit:
        nuun.save_if_needed()
        if shared_memory.dirty:
            shared_memory.save_async()
        await bot.process_commands(hatsu)
        return
    q.append(now)

    nuun_count = len(nuunrank_re.findall(hatsu.content))
    if nuun_count:
        nuunchanrank(hatsu.author.id, hatsu.guild.id, nuun_count)
        nuunchankaku_later()

                                 
    context_text = context_for_recall[1] if context_for_recall and time.monotonic() - context_for_recall[2] <= 120 else None
    message_text = hatsu.content.strip()
    is_question = (
        any(mark in message_text for mark in ("?", "？"))
        or SharedMemory.chishiki_wadai(message_text)[1]
        or re.search(r"(?:は|って)[?？]$", message_text) is not None
        or (context_text is not None and len(SharedMemory.normalize(message_text)) <= 8)
    )
    
    
    
    generation_seed = message_text

    if hatsu.content.strip() == "ぬーんランキング":
        try:
            await hatsu.channel.send(await nuunchanranktext(hatsu.author.id, hatsu.guild))
        except discord.Forbidden:
            print(f"ランキングを送信できません: channel_id={hatsu.channel.id}。Botにメッセージ送信権限がありません。")
        except discord.HTTPException as error:
            print(f"ランキング送信エラー: {error}")
        nuunchankaku()
        nuun.save_if_needed()
        await bot.process_commands(hatsu)
        return

                        

                                                      
    
    
    
    
    if not han(hatsu):
        nuun.save_if_needed()
        if shared_memory.dirty:
            shared_memory.save_async()
        await bot.process_commands(hatsu)
        return

    try:
        reply_chance = max(0.0, min(1.0, ritsumoji(hatsu) / 100.0))
    except Exception:
        reply_chance = 0.30
    
    
    if random.random() >= reply_chance:
        nuun.save_if_needed()
        if shared_memory.dirty:
            shared_memory.save_async()
        await bot.process_commands(hatsu)
        return

    pet_response = nuunchanart(hatsu.content, hatsu.author.id)
    if pet_response:
        if nuunre.search(pet_response):
            await hatsu.channel.send(pet_response, allowed_mentions=discord.AllowedMentions.none())
        nuunchankaku()
        nuun.save_if_needed()
        await bot.process_commands(hatsu)
        return

    fixed_reacted = False

    if han(hatsu):
        for r in kotoba.get("hannou", []):
            keywords = r.get("kiwado", r.get("kotoba", []))
            if isinstance(keywords, str):
                keywords = [keywords]
            keywords = [str(k).strip() for k in keywords if str(k).strip()]

            if keywords and hatsu.content.strip() not in keywords:
                continue

            try:
                ritsu = float(r.get("ritsu", 0))
            except (TypeError, ValueError):
                ritsu = 0

            if random.random() * 100 >= ritsu:
                continue

            await okuru(hatsu.channel, r)
            fixed_reacted = True
            break

    if fixed_reacted:
        nuun.save_if_needed()
        await bot.process_commands(hatsu)
        return

    
    
    
    try:
        reply = await kotaeru(message_text, context_text, is_question, hatsu.channel.id, hatsu.guild.id)
    except Exception as error:
        print(f"返信の生成中にエラー: {error}")
        error_text = f"{type(error).__name__}: {error}"[:1200]
        error_message = f"えらーぬーん（{error_text}）-# お手数ですがふにゃくんまでご連絡いただけると幸いです。"
        try:
            await hatsu.channel.send(error_message, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as send_error:
            print(f"生成エラー通知の送信に失敗: {send_error}")
        reply = None
    if reply:
        try:
            await hatsu.channel.send(reply, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            print(f"返信を送信できません: channel_id={hatsu.channel.id}。Botにメッセージ送信権限がありません。")
        except discord.HTTPException as error:
            print(f"返信の送信エラー: {error}")
        

                                               
    nuun.save_if_needed()
    if shared_memory.dirty:
        shared_memory.save_async()
    await bot.process_commands(hatsu)


if __name__ == "__main__":
    bot.run("とくくん")
