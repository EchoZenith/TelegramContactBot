import os
import logging
import aiosqlite
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- 从环境变量读取配置 ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
DB_FILE = os.getenv('DB_PATH', '/app/data/messages.db')

# 启用日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化数据库
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS msg_map 
                          (admin_msg_id INTEGER PRIMARY KEY, user_id INTEGER)''')
        await db.commit()

# 处理 /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Hello!\n\nYou can contact us using this bot.")
    else:
        await update.message.reply_text("你好，管理员！有人给机器人发消息时，我会转发给你。你直接【回复】该消息即可回信。")

# 处理所有普通消息（文字、图片、语音、文件等）
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    user_id = update.effective_chat.id
    message = update.message

    # 1. 用户发给机器人 -> 转发给管理员
    if user_id != ADMIN_ID:
        try:
            forwarded_msg = await context.bot.forward_message(
                chat_id=ADMIN_ID,
                from_chat_id=user_id,
                message_id=message.message_id
            )
            
            # 记录对应关系到数据库
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute("INSERT INTO msg_map VALUES (?, ?)", 
                                 (forwarded_msg.message_id, user_id))
                await db.commit()
        except Exception as e:
            logger.error(f"转发失败: {e}")

    # 2. 管理员回复转发的消息 -> 回传给用户
    else:
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
            
            async with aiosqlite.connect(DB_FILE) as db:
                async with db.execute("SELECT user_id FROM msg_map WHERE admin_msg_id = ?", (reply_id,)) as cursor:
                    row = await cursor.fetchone()
            
            if row:
                target_user_id = row[0]
                try:
                    # 使用 copy_message 原样复制回复的内容
                    await context.bot.copy_message(
                        chat_id=target_user_id,
                        from_chat_id=ADMIN_ID,
                        message_id=message.message_id
                    )
                except Exception as e:
                    await message.reply_text(f"回复发送失败，可能用户已停用机器人: {e}")
            else:
                await message.reply_text("找不到该消息的来源记录，无法回复。")
        # 如果管理员没用回复功能，而是直接发消息，不执行任何操作

async def post_init(application: Application):
    await init_db()

if __name__ == '__main__':
    # 检查配置
    if not BOT_TOKEN or ADMIN_ID == 0:
        print("错误: 请确保环境变量 BOT_TOKEN 和 ADMIN_ID 已正确设置！")
        exit(1)

    # 构建应用
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # 处理器注册
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    print(f"机器人已启动... 管理员ID: {ADMIN_ID}")
    application.run_polling()
