import os
import threading
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask

# ------------------------------------------------------------------
# 1. TẠO FLASK SERVER ĐỂ KEEP-ALIVE TRÊN RENDER
# ------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot Roblox Vip Server đang hoạt động 24/7!"

def run_flask():
    # Render sẽ tự cấp cổng qua biến môi trường PORT (mặc định 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Chạy Flask ở thread riêng biệt
threading.Thread(target=run_flask, daemon=True).start()

# ------------------------------------------------------------------
# 2. CẤU HÌNH BOT DISCORD
# ------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="hx!", intents=intents, help_command=None)

# Lưu trữ dữ liệu bộ nhớ tạm (Có thể nâng cấp sang Database nếu muốn lưu lâu dài)
# Structure: { guild_id: "global" | "vng" }
guild_settings = {}

# Structure: { user_id: ["acc1", "acc2"] }
user_accounts = {}

# Structure: { user_id: [{"name": "server_name", "link": "http://..."}, ...] }
user_servers = {}

@bot.event
async def on_ready():
    print(f"✨ Bot đã đăng nhập thành công dưới tên: {bot.user}")

# ------------------------------------------------------------------
# 3. NHÓM LỆNH MỚI VÀO SERVER: hx!setup
# ------------------------------------------------------------------
class SetupSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Roblox Global (Quốc tế)", 
                value="global", 
                description="Thiết lập hệ thống tạo Server VIP bản Quốc tế",
                emoji="🌐"
            ),
            discord.SelectOption(
                label="Roblox VNG", 
                value="vng", 
                description="Thiết lập hệ thống tạo Server VIP bản VNG",
                emoji="🇻🇳"
            ),
        ]
        super().__init__(placeholder="👉 Chọn phiên bản Roblox mặc định...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        region = self.values[0]
        guild_settings[interaction.guild_id] = region
        region_name = "🌐 Roblox Global (Quốc tế)" if region == "global" else "🇻🇳 Roblox VNG"
        
        embed = discord.Embed(
            title="🎉 Cấu hình hoàn tất!",
            description=f"Server này đã được thiết lập mặc định tạo Server VIP theo phiên bản **{region_name}**.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

class SetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(SetupSelect())

@bot.command(name="setup")
async def setup_command(ctx):
    """Cấu hình phiên bản Roblox cho Server"""
    embed = discord.Embed(
        title="⚙️ Thiết lập vùng Roblox cho Server",
        description="Chủ phòng/Quản trị viên vui lòng chọn phiên bản Roblox muốn áp dụng cho server này:",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=SetupView())

# ------------------------------------------------------------------
# 4. NHÓM ACCOUNT: hx!account_create, hx!account_delete
# ------------------------------------------------------------------
class AccountCreateModal(discord.ui.Modal, title="👤 Tạo Tài Khoản Roblox"):
    acc_name = discord.ui.TextInput(
        label="Tên tài khoản là gì?",
        placeholder="Nhập tên tài khoản Roblox của bạn tại đây...",
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        account_input = self.acc_name.value.strip()

        if user_id not in user_accounts:
            user_accounts[user_id] = []

        if account_input in user_accounts[user_id]:
            embed = discord.Embed(
                title="❌ Tên tài khoản đã tồn tại!",
                description=f"Tài khoản **{account_input}** đã có trong danh sách của bạn.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user_accounts[user_id].append(account_input)
        embed = discord.Embed(
            title="✅ Tạo tài khoản thành công!",
            description=f"Đã thêm tài khoản **{account_input}** vào hồ sơ của bạn thành công.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="account_create")
async def account_create_command(ctx):
    """Mở Modal nhập tên tài khoản"""
    # Vì Modal chỉ gửi được qua Interaction, dùng giao diện nút bấm để gọi Modal
    class OpenModalView(discord.ui.View):
        @discord.ui.button(label="➕ Bấm vào đây để nhập tên tài khoản", style=discord.ButtonStyle.primary, emoji="📝")
        async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(AccountCreateModal())

    embed = discord.Embed(
        title="👤 Tạo Tài Khoản Mới",
        description="Nhấn vào nút bên dưới để mở ô nhập tên tài khoản Roblox của bạn.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=OpenModalView())

@bot.command(name="account_delete")
async def account_delete_command(ctx, *, account_name: str = None):
    """Xóa tài khoản đã lưu"""
    user_id = ctx.author.id
    accounts = user_accounts.get(user_id, [])

    if not accounts:
        embed = discord.Embed(title="❌ Lỗi", description="Bạn chưa có tài khoản nào được lưu!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if not account_name:
        acc_list = "\n".join([f"• `{acc}`" for acc in accounts])
        embed = discord.Embed(
            title="⚠️ Thiếu Tên Tài Khoản",
            description=f"Vui lòng nhập tên tài khoản cần xóa theo cú pháp: `hx!account_delete <tên_tài_khoản>`\n\n**Danh sách tài khoản của bạn:**\n{acc_list}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    if account_name in accounts:
        user_accounts[user_id].remove(account_name)
        embed = discord.Embed(
            title="🗑️ Xóa Thành Công",
            description=f"Đã xóa tài khoản **{account_name}** khỏi danh sách.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="❌ Không Tìm Thấy",
            description=f"Không tìm thấy tài khoản **{account_name}** trong danh sách của bạn.",
            color=discord.Color.red()
        )
    await ctx.send(embed=embed)

# ------------------------------------------------------------------
# 5. NHÓM TẠO SERVER VIP ROBLOX: hx!server_create, hx!server_delete
# ------------------------------------------------------------------
@bot.command(name="server_create")
async def server_create_command(ctx, server_name: str = None):
    """Tạo Server VIP và gửi Link qua DM"""
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    # Kiểm tra xem Server đã setup chưa
    if guild_id not in guild_settings:
        embed = discord.Embed(
            title="🚫 Chưa Cấu Hình Server",
            description="Máy chủ này chưa được thiết lập! Vui lòng dùng lệnh `hx!setup` trước.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Bắt buộc có ít nhất 1 account
    accounts = user_accounts.get(user_id, [])
    if not accounts:
        embed = discord.Embed(
            title="⚠️ Yêu Cầu Cần Có Tài Khoản",
            description="Bạn phải tạo ít nhất 1 tài khoản trước bằng lệnh `hx!account_create` thì mới có thể tạo Server VIP!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    if not server_name:
        embed = discord.Embed(
            title="⚠️ Thiếu Tên Server VIP",
            description="Vui lòng nhập tên Server VIP muốn tạo theo cú pháp: `hx!server_create <tên_server>`",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    region = guild_settings[guild_id]
    region_label = "🌐 Roblox Global" if region == "global" else "🇻🇳 Roblox VNG"
    
    # Tạo Link Server Giả Lập / Mẫu theo khu vực đã cấu hình
    mock_link = f"https://www.roblox.com/games/share?code={hash(server_name + str(user_id))}&type=Server&region={region}"

    # Lưu thông tin Server VIP
    if user_id not in user_servers:
        user_servers[user_id] = []
    user_servers[user_id].append({"name": server_name, "link": mock_link})

    # Thử gửi liên kết vào DM của người dùng
    try:
        dm_embed = discord.Embed(
            title="🎉 Server VIP Roblox Đã Được Tạo!",
            description=f"Đây là Server VIP của bạn dành cho phiên bản **{region_label}**.",
            color=discord.Color.purple()
        )
        dm_embed.add_field(name="📛 Tên Server:", value=f"`{server_name}`", inline=False)
        dm_embed.add_field(name="🔗 Link Server VIP:", value=f"[Nhấn vào đây để vào Server VIP]({mock_link})", inline=False)
        dm_embed.set_footer(text="Cảm ơn bạn đã sử dụng dịch vụ!")
        
        await ctx.author.send(embed=dm_embed)
        
        # Báo lại ở channel công khai
        pub_embed = discord.Embed(
            title="✅ Tạo Server VIP Thành Công!",
            description=f"Link Server VIP **{server_name}** ({region_label}) đã được gửi trực tiếp qua **Tin Nhắn Riêng (DM)** của bạn! 📩",
            color=discord.Color.green()
        )
        await ctx.send(embed=pub_embed)

    except discord.Forbidden:
        # Nếu người dùng khóa DM
        err_embed = discord.Embed(
            title="❌ Không Thể Gửi DM!",
            description="Bot không thể gửi tin nhắn riêng cho bạn. Vui lòng mở khóa DM (Allow direct messages from server members) trong Cài đặt riêng tư của Discord và thử lại!",
            color=discord.Color.red()
        )
        await ctx.send(embed=err_embed)

@bot.command(name="server_delete")
async def server_delete_command(ctx, *, server_name: str = None):
    """Xóa Server VIP"""
    user_id = ctx.author.id
    servers = user_servers.get(user_id, [])

    if not servers:
        embed = discord.Embed(title="❌ Lỗi", description="Bạn chưa sở hữu Server VIP nào!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if not server_name:
        srv_list = "\n".join([f"• `{s['name']}`" for s in servers])
        embed = discord.Embed(
            title="⚠️ Thiếu Tên Server VIP",
            description=f"Vui lòng nhập tên Server VIP cần xóa theo cú pháp: `hx!server_delete <tên_server>`\n\n**Danh sách Server VIP của bạn:**\n{srv_list}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    # Lọc danh sách loại bỏ server được yêu cầu
    target_server = next((s for s in servers if s['name'] == server_name), None)
    
    if target_server:
        user_servers[user_id].remove(target_server)
        embed = discord.Embed(
            title="🗑️ Xóa Thành Công",
            description=f"Đã xóa Server VIP **{server_name}** khỏi danh sách.",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="❌ Không Tìm Thấy",
            description=f"Không tìm thấy Server VIP tên **{server_name}** trong danh sách của bạn.",
            color=discord.Color.red()
        )
    await ctx.send(embed=embed)

# ------------------------------------------------------------------
# 6. NHÓM LỆNH HỖ TRỢ: hx!help
# ------------------------------------------------------------------
@bot.command(name="help")
async def help_command(ctx):
    """Hiển thị danh sách câu lệnh"""
    embed = discord.Embed(
        title="🤖 Danh Sách Câu Lệnh Bot Roblox VIP Server",
        description="Dưới đây là toàn bộ các lệnh hiện có của bot:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🛠️ **Nhóm Cấu Hình Server**",
        value="`hx!setup` : Cấu hình vùng chơi Roblox (Global hoặc VNG) khi bot mới vào server.",
        inline=False
    )
    embed.add_field(
        name="👤 **Nhóm Tài Khoản**",
        value="`hx!account_create` : Mở giao diện điền tên tài khoản Roblox.\n`hx!account_delete <tên_acc>` : Xóa tài khoản đã lưu khỏi hệ thống.",
        inline=False
    )
    embed.add_field(
        name="🎮 **Nhóm Server VIP Roblox**",
        value="`hx!server_create <tên_server>` : Tạo Server VIP (Tự động gửi Link vào DM).\n`hx!server_delete <tên_server>` : Xóa Server VIP đã tạo.",
        inline=False
    )
    embed.add_field(
        name="❓ **Nhóm Hỗ Trợ**",
        value="`hx!help` : Hiển thị bảng hướng dẫn này.",
        inline=False
    )

    embed.set_footer(text="Lưu ý: Bạn phải tạo ít nhất 1 account trước khi tạo Server VIP!")
    await ctx.send(embed=embed)

# ------------------------------------------------------------------
# 7. KÍCH HOẠT BOT
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Đặt Token Bot trong biến môi trường DISCORD_TOKEN trên Render
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Lỗi: Chưa cấu hình DISCORD_TOKEN trong biến môi trường!")
