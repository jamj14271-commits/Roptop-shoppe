import discord
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread

# --- CẤU HÌNH WEB CHẠY NGẦM 24/7 ---
app = Flask('')
@app.route('/')
def home():
    return "Bot Duyệt Ảnh GD đang chạy!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- DỮ LIỆU GỐC TỪ ZALO CHUYỂN SANG (Lưu theo Tên Zalo) ---
zalo_backup = {
    "Luân KT": {"mp": 17435, "mac": "Leader", "discord_id": None},
    "Toàn Phát NVP": {"mp": 9750, "mac": "Thánh nổ", "discord_id": None},
    "Hoàng Gd": {"mp": 7250, "mac": None, "discord_id": None},
    "Ken Miền Tây": {"mp": 5645, "mac": "Jet Jet", "discord_id": None},
    "Nguyễn Vĩnh Phúc": {"mp": 1010, "mac": None, "discord_id": None},
    "Tuấn": {"mp": 750, "mac": None, "discord_id": None},
    "Trần Hồng Gia Bảo": {"mp": 120, "mac": None, "discord_id": None},
    "Xuân Na": {"mp": 0, "mac": None, "discord_id": None},
    "Lê Đinh Hoàng": {"mp": 0, "mac": None, "discord_id": None},
    "Cheems": {"mp": 0, "mac": None, "discord_id": None},
    "Chồng Của Em": {"mp": 0, "mac": None, "discord_id": None},
    "Hải Sigma": {"mp": 0, "mac": "Kid Blox Fruit", "discord_id": None},
    "Tạ Văn Huy": {"mp": 0, "mac": None, "discord_id": None},
    "Thanh Tình": {"mp": 0, "mac": None, "discord_id": None},
    "Tiến Bull": {"mp": 0, "mac": None, "discord_id": None},
    "Khánh Job": {"mp": 0, "mac": None, "discord_id": None},
    "Miengz (Trei)": {"mp": 0, "mac": None, "discord_id": None},
    "Lê Minh Tú": {"mp": 35115, "mac": None, "discord_id": None},
    "LongThanhz": {"mp": 10690, "mac": "Gay", "discord_id": None},
    "Tung Qan (A C U)": {"mp": 67400, "mac": "Spammer tối cổ", "discord_id": None}
}

# Hàng đợi duyệt ảnh
pending_queue = []
ADMIN_CHANNEL_ID = 123456789012345678  # BẠN HÃY THAY ID PHÒNG ADMIN CỦA BẠN VÀO ĐÂY

MP_RULES = {
    "easy": 5, "normal": 10, "hard": 25, "harder": 50, "insane": 100,
    "easy_demon": 250, "medium_demon": 500, "hard_demon": 1000, "insane_demon": 5000, "extreme_demon": 10000
}

def get_rank(mp):
    if mp >= 100000: return "Á THẦN"
    elif mp >= 50000: return "GOD"
    elif mp >= 10000: return "PRO"
    else: return "THƯỜNG"

def get_user_data(discord_id):
    """Tìm dữ liệu dựa trên Discord ID, nếu chưa liên kết thì tạo mới"""
    for name, data in zalo_backup.items():
        if data["discord_id"] == discord_id:
            return name, data
    return None, None

@bot.event
async def on_ready():
    print(f"Bot Group GD đã sẵn sàng: {bot.user}")
    process_queue.start()

# --- LỆNH LIÊN KẾT TÀI KHOẢN ZALO CŨ VÀO DISCORD (DÀNH CHO ADMIN) ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def add_id(ctx, ten_zalo: str, member: discord.Member):
    """Liên kết tên Zalo cũ với Nick Discord mới"""
    if ten_zalo in zalo_backup:
        zalo_backup[ten_zalo]["discord_id"] = member.id
        await ctx.send(f"✅ Đã liên kết tài khoản cũ **{ten_zalo}** với nick Discord {member.mention} thành công!")
    else:
        await ctx.send(f"❌ Không tìm thấy tên `{ten_zalo}` trong danh sách dữ liệu cũ. Hãy kiểm tra lại chính xác!")

# --- GIAO DIỆN NÚT BẤM DUYỆT BÀI ---
class ReviewView(discord.ui.View):
    def __init__(self, user_id, cap_do, points, display_name, ctx_channel_id, name_key):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.cap_do = cap_do
        self.points = points
        self.display_name = display_name
        self.ctx_channel_id = ctx_channel_id
        self.name_key = name_key

    @discord.ui.button(label="✅ Duyệt (Cộng MP)", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Bạn không có quyền duyệt bài!", ephemeral=True)

        if self.name_key:
            zalo_backup[self.name_key]["mp"] += self.points
            current_mp = zalo_backup[self.name_key]["mp"]
        else:
            zalo_backup[self.display_name] = {"mp": self.points, "mac": None, "discord_id": self.user_id}
            current_mp = self.points

        for item in self.children: item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"🎉 Đã duyệt bài thành công cho {self.display_name}!")
        
        chan = bot.get_channel(self.ctx_channel_id)
        if chan:
            await chan.send(f"✅ Minh chứng của <@{self.user_id}> đã được phê duyệt!\n"
                            f"➕ Cộng **+{self.points} MP** ({self.cap_do.upper()}).\n"
                            f"💰 Số dư hiện tại: `{current_mp} MP` ({get_rank(current_mp)})")

    @discord.ui.button(label="❌ Từ chối", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Bạn không có quyền từ chối!", ephemeral=True)

        for item in self.children: item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"❌ Đã từ chối bài của {self.display_name}.")
        
        chan = bot.get_channel(self.ctx_channel_id)
        if chan:
            await chan.send(f"❌ Minh chứng cấp độ `{self.cap_do.upper()}` của <@{self.user_id}> đã bị **Từ chối**.")

# --- LỆNH GỬI DUYỆT BÀI DÀNH CHO THÀNH VIÊN ---
@bot.command()
async def duyet(ctx, cap_do: str):
    cap_do = cap_do.lower()
    if cap_do not in MP_RULES:
        return await ctx.send("❌ Cấp độ không hợp lệ! Hãy chọn cấp độ chuẩn (ví dụ: easy_demon, extreme_demon...)")
    if not ctx.message.attachments:
        return await ctx.send("❌ Bạn quên đính kèm ảnh/video minh chứng rồi! Thao tác lại kèm PROOF rõ ràng.")

    image_url = ctx.message.attachments[0].url
    name_key, data = get_user_data(ctx.author.id)
    display_name = name_key if name_key else ctx.author.name

    pending_queue.append({
        "user_id": ctx.author.id, "cap_do": cap_do, "url": image_url,
        "ctx_channel": ctx.channel.id, "display_name": display_name, "name_key": name_key
    })
    await ctx.send(f"📥 {ctx.author.mention}, bot đã nhận PROOF cấp độ `{cap_do.upper()}`.\n"
                   f"⏳ Đã đưa vào hàng đợi xếp hàng chờ duyệt bài (Đang có `{len(pending_queue)}` bài chờ).")

# --- VÒNG LẶP GỬI ẢNH CHO ADMIN MỖI 30 PHÚT ---
@tasks.loop(minutes=30)
async def process_queue():
    if not pending_queue: return
    item = pending_queue.pop(0)
    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if not admin_channel: return

    pts = MP_RULES[item["cap_do"]]
    embed = discord.Embed(title="📸 KIỂM DUYỆT PROOF GEOMETRY DASH", color=0xffa500)
    embed.add_field(name="👤 Người chơi", value=f"<@{item['user_id']}> (`{item['display_name']}`)", inline=True)
    embed.add_field(name="🎮 Cấp độ", value=item["cap_do"].upper(), inline=True)
    embed.add_field(name="💰 MP cộng thêm", value=f"**{pts} MP**", inline=True)
    embed.set_image(url=item["url"])
    embed.set_footer(text="Check kỹ tỉ lệ ảnh 16:9, video show acc và cheat indicator trước khi bấm!")

    view = ReviewView(item["user_id"], item["cap_do"], pts, item["display_name"], item["ctx_channel"], item["name_key"])
    await admin_channel.send(embed=embed, view=view)

# --- TÍNH NĂNG TRA CỨU VÍ SỐ DƯ ---
@bot.command()
async def vi(ctx, member: discord.Member = None):
    target = member or ctx.author
    name_key, data = get_user_data(target.id)
    
    if data:
        mp = data["mp"]
        mac = f" (Mác: {data['mac']})" if data["mac"] else ""
        rank = get_rank(mp)
        await ctx.send(f"💼 **Ví Group GD của {target.mention} (`{name_key}`):**\n💰 Số dư: **{mp} MP**\n🎖️ Phân hạng: `{rank}`{mac}")
    else:
        await ctx.send(f"❌ {target.mention} chưa được Admin liên kết tài khoản Zalo cũ bằng lệnh `!add_id`!")

# --- LỆNH XEM BẢNG XẾP HẠNG CHUẨN MỤC ---
@bot.command()
async def bxh(ctx):
    thuong, pro, god, athan = [], [], [], []
    leader_text = ""

    for name, data in zalo_backup.items():
        mp = data["mp"]
        mac_text = f" (Mác: {data['mac']})" if data["mac"] else ""
        user_display = f"<@{data['discord_id']}>" if data["discord_id"] else f"**{name}**"
        
        item_text = f"{user_display}: {mp:,} MP{mac_text}"
        item_data = (item_text, mp)

        if name == "Luân KT":
            leader_text = f"👑 **Leader: {user_display}: {mp:,} MP**\n\n"
            continue

        rank = get_rank(mp)
        if rank == "Á THẦN": athan.append(item_data)
        elif rank == "GOD": god.append(item_data)
        elif rank == "PRO": pro.append(item_data)
        else: thuong.append(item_data)

    def sort_and_format(lst):
        sorted_list = sorted(lst, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_list]

    embed_text = "🏆 **BẢNG XẾP HẠNG THÀNH TÍCH GROUP GD** 🏆\n-----------------------------------\n"
    embed_text += leader_text

    embed_text += "🔹 **MỤC THƯỜNG (0 - 9.999 MP)**\n"
    for i, p in enumerate(sort_and_format(thuong), 1): embed_text += f"{i}st. {p}\n"
    
    embed_text += "\n🔸 **MỤC PRO (10.000 - 49.999 MP)**\n"
    for i, p in enumerate(sort_and_format(pro), 1): embed_text += f"{i}st. {p}\n"

    embed_text += "\n🔥 **MỤC GOD (50.000 - 99.999 MP)**\n"
    for i, p in enumerate(sort_and_format(god), 1): embed_text += f"{i}st. {p}\n"

    embed_text += "\n⚡ **MỤC Á THẦN (100.000+ MP)**\n"
    if not athan: embed_text += "- Chưa có thành viên\n"
    else:
        for i, p in enumerate(sort_and_format(athan), 1): embed_text += f"{i}st. {p}\n"

    embed_text += "\n-----------------------------------\n👑 **KỶ LỤC GROUP**\n- Hardest hiện tại: \"Sweather Weather\"\n- Người hoàn thành: Tung Qan (A C U)\n\n📢 **LƯU Ý:** Không có proof = tính 0 MP."
    
    await ctx.send(embed_text)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
  
