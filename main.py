from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== CONFIG =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8655440994:AAFwDjwQVgKxb506gNEJ5zlr0vDylId6Tmk")

MAX_WARNINGS   = 3          # 3 warnings pe mute
MUTE_HOURS     = 2          # Kitne ghante ka mute
WARN_AUTO_DEL  = 20         # Warning message auto-delete (seconds)
MUTE_AUTO_DEL  = 60         # Mute message auto-delete (seconds)

DEVELOPER = "SovitX"
CREDIT    = f"\n\n💎 *Developed by {DEVELOPER}*"

# ===================== DATA =====================
# { user_id: { 'warnings': int, 'muted': bool } }
user_data = defaultdict(lambda: {'warnings': 0, 'muted': False})


# =================== HELPERS ====================
def esc(text: str) -> str:
    """Escape MarkdownV2 special characters"""
    if not text:
        return ""
    for ch in r'\_*[]()~`>#+-=|{}.!':
        text = str(text).replace(ch, f'\\{ch}')
    return text


async def is_admin(bot, chat_id: int, user_id: int) -> bool:
    """Check karo ki user admin hai ya nahi"""
    try:
        admins = await bot.get_chat_administrators(chat_id)
        return any(a.user.id == user_id for a in admins)
    except Exception:
        return False


# =================== COMMANDS ===================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ka introduction"""
    chat_type = update.effective_chat.type

    if chat_type == "private":
        text = (
            f"👋 *Namaste\\! Main hoon Forward Blocker Bot\\!*\n"
            f"💎 *Jo ki {esc(DEVELOPER)} dwara banaya gaya hoon\\.*\n\n"
            f"{'─'*35}\n\n"
            f"🛡️ *Mera Kaam:*\n"
            f"├─ Group me forward messages turant delete karna\n"
            f"├─ Forward karne wale user ko warn karna\n"
            f"└─ {MAX_WARNINGS} warnings pe user ko {MUTE_HOURS}h ke liye mute karna\n\n"
            f"{'─'*35}\n\n"
            f"⚙️ *Setup Karo:*\n\n"
            f"*Step 1:* Mujhe apne group me add karo\n\n"
            f"*Step 2:* Mujhe Admin banao with:\n"
            f"├─ ✅ Delete Messages\n"
            f"├─ ✅ Restrict Members\n"
            f"└─ ✅ Ban Users\n\n"
            f"*Step 3:* Done\\! 🎉 Main apna kaam shuru kar dunga\\!\n\n"
            f"{'─'*35}\n"
            f"_Group admins ke messages kabhi delete nahi honge\\._"
            f"{CREDIT}"
        )
    else:
        text = (
            f"🔥 *FORWARD BLOCKER BOT — ACTIVE*\n"
            f"💎 *Developed by {esc(DEVELOPER)}*\n\n"
            f"{'─'*35}\n\n"
            f"✅ *Main is group ki raksha kar raha hoon\\!*\n\n"
            f"📋 *Rules:*\n"
            f"├─ Forward message = ⚠️ Warning\n"
            f"├─ {MAX_WARNINGS} warnings = 🔇 {MUTE_HOURS}h Mute\n"
            f"└─ Admins exempt hain ✅\n\n"
            f"👮 *Admin Commands:*\n"
            f"├─ `/warnings @user` \\- User ki warnings dekho\n"
            f"├─ `/resetwarn @user` \\- Warnings reset karo\n"
            f"└─ `/help` \\- Help dekho"
            f"{CREDIT}"
        )

    await update.message.reply_text(text, parse_mode='MarkdownV2')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    text = (
        f"📖 *HELP — FORWARD BLOCKER BOT*\n"
        f"💎 *Developed by {esc(DEVELOPER)}*\n\n"
        f"{'─'*35}\n\n"
        f"🤖 *Bot Kya Karta Hai:*\n"
        f"Group me koi bhi forward message bheje, bot:\n"
        f"├─ Message turant delete kar deta hai\n"
        f"├─ User ko warn karta hai\n"
        f"└─ {MAX_WARNINGS} warns hone pe {MUTE_HOURS}h ke liye mute karta hai\n\n"
        f"👮 *Admin Commands:*\n"
        f"├─ `/warnings` — Kisi user ki warnings dekho \\(reply karke\\)\n"
        f"├─ `/resetwarn` — Kisi user ki warnings reset karo \\(reply karke\\)\n"
        f"└─ `/help` — Ye message\n\n"
        f"🛡️ *Note:*\n"
        f"_Group admins ke messages kabhi delete nahi honge\\._"
        f"{CREDIT}"
    )
    await update.message.reply_text(text, parse_mode='MarkdownV2')


async def warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kisi user ki warnings dekho"""
    chat_id = update.effective_chat.id
    requester_id = update.effective_user.id

    if not await is_admin(context.bot, chat_id, requester_id):
        await update.message.reply_text("❌ Sirf admins ye command use kar sakte hain!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Kisi user ke message ko reply karke ye command use karo!")
        return

    target = update.message.reply_to_message.from_user
    warns  = user_data[target.id]['warnings']

    text = (
        f"📊 *Warning Info*\n\n"
        f"👤 User: {esc(target.full_name)}\n"
        f"⚠️ Warnings: *{warns}/{MAX_WARNINGS}*\n"
        f"🔇 Muted: *{'Haan' if user_data[target.id]['muted'] else 'Nahi'}*"
        f"{CREDIT}"
    )
    await update.message.reply_text(text, parse_mode='MarkdownV2')


async def reset_warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ki warnings reset karo"""
    chat_id = update.effective_chat.id
    requester_id = update.effective_user.id

    if not await is_admin(context.bot, chat_id, requester_id):
        await update.message.reply_text("❌ Sirf admins ye command use kar sakte hain!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Kisi user ke message ko reply karke ye command use karo!")
        return

    target = update.message.reply_to_message.from_user
    user_data[target.id]['warnings'] = 0
    user_data[target.id]['muted']    = False

    # Unmute bhi karo
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            )
        )
    except Exception:
        pass

    text = (
        f"✅ *Warnings Reset!*\n\n"
        f"👤 User: {esc(target.full_name)}\n"
        f"🔄 Warnings clear ho gayi aur unmute bhi ho gaye\\!"
        f"{CREDIT}"
    )
    await update.message.reply_text(text, parse_mode='MarkdownV2')


# =============== FORWARD BLOCKER ================
async def forward_blocker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main forward message detector aur blocker"""
    message = update.message
    if not message:
        return

    # Check karo ki message forward hai ya nahi
    is_forward = (
        message.forward_origin is not None or
        message.forward_from is not None or
        message.forward_from_chat is not None or
        message.forward_sender_name is not None
    )

    if not is_forward:
        return

    user    = message.from_user
    chat_id = message.chat_id

    # Admins exempt hain
    if await is_admin(context.bot, chat_id, user.id):
        return

    # Forward message delete karo
    try:
        await message.delete()
        logger.info(f"🗑️ Forward message deleted — User: {user.full_name} ({user.id})")
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return

    # Warning add karo
    user_data[user.id]['warnings'] += 1
    current_warns = user_data[user.id]['warnings']
    safe_name     = esc(user.full_name)

    # ---- MUTE (3rd warning) ----
    if current_warns >= MAX_WARNINGS:
        mute_until = datetime.now() + timedelta(hours=MUTE_HOURS)

        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=mute_until
            )
            user_data[user.id]['muted']    = True
            user_data[user.id]['warnings'] = 0  # Reset after mute

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔓 Unmute", callback_data=f"unmute_{user.id}"),
                    InlineKeyboardButton("🚫 Ban",    callback_data=f"ban_{user.id}")
                ]
            ])

            mute_text = (
                f"🔇 *USER MUTE HO GAYA\\!*\n\n"
                f"👤 User: {safe_name}\n"
                f"⏰ Duration: *{MUTE_HOURS} ghante*\n"
                f"📋 Reason: *{MAX_WARNINGS} forward messages*\n\n"
                f"_Admins neeche se action le sakte hain\\._"
                f"{CREDIT}"
            )

            sent = await context.bot.send_message(
                chat_id=chat_id,
                text=mute_text,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )

            # Auto delete mute message
            context.job_queue.run_once(
                _delete_msg,
                MUTE_AUTO_DEL,
                data={'chat_id': chat_id, 'message_id': sent.message_id}
            )

            logger.info(f"🔇 Muted: {user.full_name} for {MUTE_HOURS}h")

        except Exception as e:
            logger.error(f"Mute error: {e}")

    # ---- WARNING (1st & 2nd) ----
    else:
        remaining = MAX_WARNINGS - current_warns

        warn_text = (
            f"⚠️ *FORWARD MESSAGE DELETE HUA\\!*\n\n"
            f"👤 User: {safe_name}\n"
            f"📊 Warning: *{current_warns}/{MAX_WARNINGS}*\n"
            f"🔢 Bacha: *{remaining} aur warning*\n\n"
            f"_Is group me forward messages allowed nahi hain\\!_"
            f"{CREDIT}"
        )

        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=warn_text,
            parse_mode='MarkdownV2'
        )

        # Auto delete warning message
        context.job_queue.run_once(
            _delete_msg,
            WARN_AUTO_DEL,
            data={'chat_id': chat_id, 'message_id': sent.message_id}
        )

        logger.info(f"⚠️ Warning {current_warns}/{MAX_WARNINGS}: {user.full_name}")


# ================ CALLBACKS =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin buttons: Unmute / Ban"""
    query   = update.callback_query
    await query.answer()

    chat_id    = query.message.chat_id
    admin_id   = query.from_user.id
    admin_name = esc(query.from_user.first_name)

    if not await is_admin(context.bot, chat_id, admin_id):
        await query.answer("❌ Sirf admins ye kar sakte hain!", show_alert=True)
        return

    action, user_id = query.data.split('_')
    user_id = int(user_id)

    if action == "unmute":
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True,
                )
            )
            user_data[user_id]['muted']    = False
            user_data[user_id]['warnings'] = 0

            await query.edit_message_text(
                f"✅ *USER UNMUTE HO GAYA\\!*\n\n"
                f"👮 Admin: {admin_name}\n"
                f"🔄 Warnings bhi clear ho gayi\\!"
                f"{CREDIT}",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)

    elif action == "ban":
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            user_data.pop(user_id, None)

            await query.edit_message_text(
                f"🚫 *USER BAN HO GAYA\\!*\n\n"
                f"👮 Admin: {admin_name}\n"
                f"📋 Reason: Forward message violation"
                f"{CREDIT}",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)


# ================ UTILS =========================
async def _delete_msg(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled message delete"""
    try:
        await context.bot.delete_message(
            chat_id=context.job.data['chat_id'],
            message_id=context.job.data['message_id']
        )
    except Exception:
        pass


# =================== MAIN =======================
def main():
    print("\n" + "="*50)
    print("🛡️  FORWARD BLOCKER BOT")
    print(f"💎  Developed by {DEVELOPER}")
    print("="*50)
    print(f"\n⚙️  Settings:")
    print(f"   ├─ Max Warnings : {MAX_WARNINGS}")
    print(f"   ├─ Mute Duration: {MUTE_HOURS} hours")
    print(f"   ├─ Warn Auto-Del: {WARN_AUTO_DEL}s")
    print(f"   └─ Mute Auto-Del: {MUTE_AUTO_DEL}s")
    print("\n🚀 Bot start ho raha hai...\n")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",     start_command))
    app.add_handler(CommandHandler("help",      help_command))
    app.add_handler(CommandHandler("warnings",  warnings_command,  filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("resetwarn", reset_warn_command, filters=filters.ChatType.GROUPS))
    app.add_handler(CallbackQueryHandler(button_callback))

    # ALL messages check karo — text, photo, video, document, sticker sab
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        forward_blocker
    ))

    print("✅ Bot successfully start ho gaya!")
    print("🛡️  Protection: ACTIVE\n")
    print("="*50)

    app.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)


if __name__ == '__main__':
    main()
