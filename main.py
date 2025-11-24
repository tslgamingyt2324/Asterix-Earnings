import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from config import Config
from database import Database

# Initialize database
db = Database()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AsterixEarningsBot:
    def __init__(self):
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self.user_ad_sessions = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = {
            'user_id': user.id,
            'first_name': user.first_name,
            'username': user.username,
            'phone_number': None
        }
        
        db.create_user(user_data)
        
        welcome_text = f"""
🤖 *Welcome to Asterix Earnings Bot* 💰

*Hi {user.first_name}!* 👋

Earn money by watching ads!

📱 *Features:*
• Watch ads and earn $0.02 per ad
• Minimum withdrawal: ${Config.MIN_WITHDRAWAL}
• Multiple payment methods

⚡ *Quick Start:*
1. Click *'📺 Watch Ads'* to start earning
2. Open the ad link and wait 30 seconds
3. Get paid automatically!
        """
        
        keyboard = [
            [KeyboardButton("💰 Balance"), KeyboardButton("📺 Watch Ads")],
            [KeyboardButton("💳 Withdraw"), KeyboardButton("📋 Instructions")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.get_user(update.effective_user.id)
        if user:
            balance_text = f"""
💼 *Your Account Balance*

💰 *Available Balance:* `${user.balance:.2f}`
🏆 *Total Earned:* `${user.total_earned:.2f}`
📊 *Ads Watched:* `{user.ads_watched}`

💡 *Withdrawal Minimum:* `${Config.MIN_WITHDRAWAL}`
            """
            await update.message.reply_text(balance_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Please use /start to register first.")
    
    async def watch_ads_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text("❌ Please use /start to register first.")
            return
        
        if user.is_watching_ad:
            await update.message.reply_text("⏳ You are already watching an ad. Please complete it first.")
            return
        
        db.set_watching_ad(user_id, True)
        
        ad_message = f"""
🎬 *Watch Ad & Earn ${Config.EARN_PER_AD}*

💰 *Earning:* `${Config.EARN_PER_AD}`
⏰ *Time:* `{Config.AD_DURATION} seconds`

📋 *Instructions:*
1. Click the button below to open ad
2. Wait for {Config.AD_DURATION} seconds
3. Return and click *'✅ I Completed Watching'*

⚠️ *Rules:*
• Stay on ad for full {Config.AD_DURATION} seconds
• Payment is automatic
        """
        
        keyboard = [
            [InlineKeyboardButton("🎬 👉 Click Here 👈 - Watch & Earn $0.02", url=Config.AD_LINK)],
            [InlineKeyboardButton("✅ I Completed Watching", callback_data="confirm_ad")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_ad")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await update.message.reply_text(ad_message, reply_markup=reply_markup, parse_mode='Markdown')
        
        self.user_ad_sessions[user_id] = {
            'message_id': message.message_id,
            'start_time': datetime.now()
        }
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = db.get_user(update.effective_user.id)
        
        if not user:
            await update.message.reply_text("❌ Please use /start to register first.")
            return
        
        if user.balance < Config.MIN_WITHDRAWAL:
            await update.message.reply_text(f"❌ Minimum withdrawal is ${Config.MIN_WITHDRAWAL}. Your balance: ${user.balance:.2f}")
            return
        
        keyboard = []
        for method in Config.PAYMENT_METHODS:
            keyboard.append([InlineKeyboardButton(f"📱 {method.upper()}", callback_data=f"withdraw_{method}")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdraw")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💳 *Withdrawal Request*\n💰 Balance: ${user.balance:.2f}\nChoose method:",
            reply_markup=reply_markup, parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📋 *Instructions*

🎯 *How to Earn:*
1. Click *'📺 Watch Ads'*
2. Click *'👉 Click Here 👈'*
3. Wait 30 seconds on ad page
4. Click *'✅ I Completed Watching'*
5. Get *$0.02* automatically

💰 *Withdrawal:*
- Minimum: $1.00
- Methods: bKash, Nagad, Rocket, PayPal
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        
        if text == "💰 Balance":
            await self.balance_command(update, context)
        elif text == "📺 Watch Ads":
            await self.watch_ads_command(update, context)
        elif text == "💳 Withdraw":
            await self.withdraw_command(update, context)
        elif text == "📋 Instructions":
            await self.help_command(update, context)
        else:
            await update.message.reply_text("Please use the menu buttons or /help")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == "confirm_ad":
            await self.confirm_ad_watching(query, context)
        elif data == "cancel_ad":
            await self.cancel_ad_watching(query, context)
        elif data.startswith("withdraw_"):
            method = data.replace("withdraw_", "")
            await self.handle_withdrawal_method(query, context, method)
        elif data == "cancel_withdraw":
            await query.edit_message_text("❌ Withdrawal cancelled.")
    
    async def confirm_ad_watching(self, query, context):
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user or not user.is_watching_ad:
            await query.answer("❌ Start watching an ad first!", show_alert=True)
            return
        
        user = db.update_user_balance(user_id, Config.EARN_PER_AD)
        
        if user:
            success_text = f"""
✅ *Payment Credited!* 🎉

💰 *Earned:* `${Config.EARN_PER_AD}`
📊 *New Balance:* `${user.balance:.2f}`
🏆 *Total Ads:* `{user.ads_watched}`

Keep watching to earn more!
            """
            
            if user_id in self.user_ad_sessions:
                del self.user_ad_sessions[user_id]
            
            await query.edit_message_text(success_text, parse_mode='Markdown')
    
    async def handle_withdrawal_method(self, query, context, method):
        user = db.get_user(query.from_user.id)
        await query.edit_message_text(f"💳 Withdrawal via {method.upper()}\nSend: /{method} YOUR_ACCOUNT_NUMBER")
    
    async def cancel_ad_watching(self, query, context):
        user_id = query.from_user.id
        db.set_watching_ad(user_id, False)
        if user_id in self.user_ad_sessions:
            del self.user_ad_sessions[user_id]
        await query.edit_message_text("❌ Ad watching cancelled.")

# Create bot instance
bot = AsterixEarningsBot()
