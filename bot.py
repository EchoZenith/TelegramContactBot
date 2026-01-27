import os
import logging
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes


# --- 从环境变量读取配置 ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
DB_FILE = os.getenv('DB_PATH', '/app/data/messages.db')
GITHUB_URL = os.getenv('GITHUB_URL', 'https://github.com/EchoZenith/TelegramContactBot')


# 启用日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# 初始化数据库
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        # 记录：管理员端消息ID <-> 用户端消息ID <-> 用户ID
        await db.execute('''CREATE TABLE IF NOT EXISTS msg_pairs 
                          (admin_msg_id INTEGER PRIMARY KEY, user_msg_id INTEGER, user_id INTEGER)''')
        await db.commit()


# 处理 /start 命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    keyboard = [[InlineKeyboardButton("🌟 查看项目源码", url=GITHUB_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("Hello!\n\nYou can contact us using this bot.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("你好，管理员！有人给机器人发消息时，我会转发给你。你直接【回复】该消息即可回信。")

# 处理同步修改逻辑
async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    edited_msg = update.edited_message
    if not edited_msg:
        return
        
    user_id = edited_msg.chat.id
    async with aiosqlite.connect(DB_FILE) as db:
        if user_id != ADMIN_ID:
            # 1. 查找旧的转发记录
            async with db.execute("SELECT admin_msg_id FROM msg_pairs WHERE user_msg_id = ? AND user_id = ?", 
                                 (edited_msg.message_id, user_id)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    old_admin_msg_id = row[0]
                    # 获取新内容（文字或媒体说明）
                    content = edited_msg.text or edited_msg.caption or ""
                    new_text = f"【此消息已修改】\n{content}"
                    
                    try:
                        # 2. 判断是纯文本还是带媒体的消息
                        if edited_msg.text:
                            # 发送纯文字消息，并回复在旧消息上
                            new_msg = await context.bot.send_message(
                                chat_id=ADMIN_ID,
                                text=new_text,
                                reply_to_message_id=old_admin_msg_id
                            )
                        else:
                            # 如果是图片/视频等媒体，复制它并修改其 Caption
                            new_msg = await context.bot.copy_message(
                                chat_id=ADMIN_ID,
                                from_chat_id=user_id,
                                message_id=edited_msg.message_id,
                                caption=new_text,
                                reply_to_message_id=old_admin_msg_id
                            )
                            
                        # 3. 更新映射关系，确保管理员回复这条带“【新消息】”提示的消息时，也能回传
                        await db.execute("INSERT OR REPLACE INTO msg_pairs VALUES (?, ?, ?)", 
                                         (new_msg.message_id, edited_msg.message_id, user_id))
                        await db.commit()
                        
                    except Exception as e:
                        logger.error(f"处理用户修改回传失败: {e}")
        else:
            # 管理员修改逻辑保持不变（原地编辑用户收到的消息）
            async with db.execute("SELECT user_id, user_msg_id FROM msg_pairs WHERE admin_msg_id = ?", 
                                 (edited_msg.message_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        new_content = edited_msg.text or edited_msg.caption
                        await context.bot.edit_message_text(chat_id=row[0], message_id=row[1], text=new_content)
                    except Exception as e:
                        logger.warning(f"管理员修改同步略过: {e}")


# 处理所有普通消息
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_chat.id
    message = update.message
    
    # 1. 用户 -> 管理员
    if user_id != ADMIN_ID:
        try:
            forwarded_msg = await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user_id, message_id=message.message_id)
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute("INSERT INTO msg_pairs VALUES (?, ?, ?)", 
                                 (forwarded_msg.message_id, message.message_id, user_id))
                await db.commit()
        except Exception as e: logger.error(f"转发失败: {e}")
        
    # 2. 管理员回复 -> 用户
    elif message.reply_to_message:
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT user_id FROM msg_pairs WHERE admin_msg_id = ?", (message.reply_to_message.message_id,)) as cursor:
                row = await cursor.fetchone()
        
        if row:
            target_user_id = row[0]
            try:
                sent_msg = await context.bot.copy_message(chat_id=target_user_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
                # 记录管理员发出的回复，以便管理员后续修改这条回复时能同步给用户
                async with aiosqlite.connect(DB_FILE) as db:
                    await db.execute("INSERT INTO msg_pairs (admin_msg_id, user_msg_id, user_id) VALUES (?, ?, ?)", 
                                     (message.message_id, sent_msg.message_id, target_user_id))
                    await db.commit()
            except Exception as e: await message.reply_text(f"回复失败: {e}")


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
    # 监听修改消息的更新
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE & filters.TEXT, handle_edit))
    # 监听普通消息
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    print(f"机器人已启动... 管理员ID: {ADMIN_ID}")
    application.run_polling()