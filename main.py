import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8496475334:AAFVBYMsb_d_K80YkD06V3ZlcASS2jzV0uQ')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7251748706'))
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY', '51444506-bffefcaf12816bd85a20222d1')

# In-memory storage (for production, consider using a database)
users_data = {}
force_channels = []  # List of channel usernames
banned_users = set()
bot_stats = {
    'total_users': 0,
    'total_searches': 0,
    'start_date': datetime.now().isoformat()
}

class PixabayBot:
    def __init__(self):
        self.pixabay_base_url = "https://pixabay.com/api/"
        self.search_types = {
            'photo': '📷 الصور',
            'illustration': '🎨 الرسوم التوضيحية', 
            'vector': '📐 الرسوم المتجهة',
            'video': '🎬 الفيديو',
            'music': '🎵 الموسيقى',
            'gif': '🎞️ الصور المتحركة'
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Check if user is banned
        if user_id in banned_users:
            await update.message.reply_text("❌ تم حظرك من استخدام البوت")
            return
        
        # Add user to database if not exists
        if user_id not in users_data:
            users_data[user_id] = {
                'username': username,
                'join_date': datetime.now().isoformat(),
                'search_count': 0,
                'current_search': None,
                'search_results': [],
                'current_result_index': 0,
                'selected_search_type': 'all',
                'waiting_for_search': False
            }
            bot_stats['total_users'] += 1
        
        # Check force subscription
        if not await self.check_user_subscriptions(user_id, context):
            await self.send_subscription_message(update)
            return
        
        # User is subscribed, show main menu
        await self.send_main_menu(update)
    
    async def check_user_subscriptions(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is subscribed to all mandatory channels"""
        if not force_channels:
            return True
        
        for channel in force_channels:
            try:
                member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.error(f"Error checking subscription for {channel}: {e}")
                # If we can't check, assume not subscribed
                return False
        
        return True
    
    async def send_subscription_message(self, update: Update):
        """Send subscription verification message"""
        message = """   (•_•)  
  <)   )╯  
   /   \\  
🎧 | اشترك في القنوات اولا"""
        
        keyboard = []
        
        # Add channel buttons
        for channel in force_channels:
            keyboard.append([InlineKeyboardButton(f"📢 {channel}", url=f"https://t.me/{channel.replace('@', '')}")])
        
        # Add verification button
        keyboard.append([InlineKeyboardButton("تحقق | Verify ✅", callback_data="verify_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def send_main_menu(self, update: Update):
        """Send main menu after successful verification"""
        message = """(⊙_☉)  
  /|\\
  / \\
هل تريد بدء بحث؟!"""
        
        keyboard = [
            [InlineKeyboardButton("بدء البحث 🎧", callback_data="start_search")],
            [InlineKeyboardButton("نوع البحث 💐", callback_data="search_type_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # Check if user is banned
        if user_id in banned_users:
            await query.edit_message_text("❌ تم حظرك من استخدام البوت")
            return
        
        if data == "verify_subscription":
            if await self.check_user_subscriptions(user_id, context):
                await self.send_main_menu(update)
            else:
                await query.edit_message_text("❌ لم تشترك في جميع القنوات المطلوبة!")
        
        elif data == "start_search":
            await query.edit_message_text("🔍 ارسل كلمة البحث:")
            users_data[user_id]['waiting_for_search'] = True
        
        elif data == "search_type_menu":
            await self.show_search_type_menu(query, user_id)
        
        elif data.startswith("search_type_"):
            search_type = data.replace("search_type_", "")
            users_data[user_id]['selected_search_type'] = search_type
            await self.show_search_type_menu(query, user_id)
        
        elif data == "search_with_type":
            await query.edit_message_text("🔍 ارسل كلمة البحث:")
            users_data[user_id]['waiting_for_search'] = True
        
        elif data == "next_result":
            await self.navigate_results(query, user_id, 1)
        
        elif data == "prev_result":
            await self.navigate_results(query, user_id, -1)
        
        elif data == "select_result":
            await self.select_result(query, user_id)
        
        elif data == "back_to_main":
            await self.send_main_menu(update)
        
        # Admin callbacks
        elif data.startswith("admin_"):
            if user_id == ADMIN_ID:
                await self.handle_admin_callback(query, data)
    
    async def show_search_type_menu(self, query, user_id: int):
        """Show search type selection menu"""
        current_type = users_data[user_id].get('selected_search_type', 'all')
        
        keyboard = []
        for search_type, display_name in self.search_types.items():
            indicator = "👻" if current_type == search_type else ""
            keyboard.append([InlineKeyboardButton(f"{display_name} {indicator}", callback_data=f"search_type_{search_type}")])
        
        keyboard.append([InlineKeyboardButton("بدء البحث عن النوع المحدد 🔍", callback_data="search_with_type")])
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("اختر نوع البحث:", reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        
        # Check if user is banned
        if user_id in banned_users:
            await update.message.reply_text("❌ تم حظرك من استخدام البوت")
            return
        
        # Check if user exists and is verified
        if user_id not in users_data:
            await update.message.reply_text("ارسل /start أولاً")
            return
        
        if not await self.check_user_subscriptions(user_id, context):
            await self.send_subscription_message(update)
            return
        
        # Handle admin commands
        if user_id == ADMIN_ID and update.message.text.startswith('/admin'):
            await self.handle_admin_command(update, context)
            return
        
        # Handle search queries
        if users_data[user_id].get('waiting_for_search'):
            await self.perform_search(update, user_id)
            users_data[user_id]['waiting_for_search'] = False
    
    async def perform_search(self, update: Update, user_id: int):
        """Perform Pixabay search"""
        search_query = update.message.text
        search_type = users_data[user_id].get('selected_search_type', 'all')
        
        # Pixabay API parameters
        params = {
            'key': PIXABAY_API_KEY,
            'q': search_query,
            'per_page': 20,
            'safesearch': 'true',
            'lang': 'ar'
        }
        
        # Set category based on search type
        if search_type != 'all' and search_type in self.search_types:
            if search_type == 'music':
                # Music search uses different endpoint
                url = "https://pixabay.com/api/music/"
            elif search_type == 'video':
                url = "https://pixabay.com/api/videos/"
            else:
                params['category'] = search_type
                url = self.pixabay_base_url
        else:
            url = self.pixabay_base_url
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('total', 0) == 0:
                await update.message.reply_text("""   ¯\\_(ツ)_/¯
    كلماتك غريبة يا غلام""")
                return
            
            # Store search results
            users_data[user_id]['search_results'] = data['hits']
            users_data[user_id]['current_result_index'] = 0
            users_data[user_id]['current_search'] = search_query
            
            # Update statistics
            users_data[user_id]['search_count'] += 1
            bot_stats['total_searches'] += 1
            
            # Show first result
            await self.show_search_result(update, user_id)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("❌ حدث خطأ في البحث، حاول مرة أخرى")
    
    async def show_search_result(self, update: Update, user_id: int, edit_message=False):
        """Display search result with navigation"""
        results = users_data[user_id]['search_results']
        index = users_data[user_id]['current_result_index']
        
        if not results or index >= len(results):
            return
        
        result = results[index]
        
        # Prepare result message
        if 'webformatURL' in result:  # Image/Video
            image_url = result['webformatURL']
            caption = f"🔍 النتيجة {index + 1} من {len(results)}\n"
            caption += f"👀 المشاهدات: {result.get('views', 'غير محدد')}\n"
            caption += f"👍 الإعجابات: {result.get('likes', 'غير محدد')}\n"
            caption += f"📥 التحميلات: {result.get('downloads', 'غير محدد')}"
        else:  # Music
            caption = f"🎵 {result.get('name', 'غير محدد')}\n"
            caption += f"🎤 الفنان: {result.get('artist', 'غير محدد')}\n"
            caption += f"⏱️ المدة: {result.get('duration', 'غير محدد')} ثانية\n"
            caption += f"🔍 النتيجة {index + 1} من {len(results)}"
            image_url = None
        
        # Navigation keyboard
        keyboard = []
        nav_row = []
        
        if index > 0:
            nav_row.append(InlineKeyboardButton("« السابق", callback_data="prev_result"))
        if index < len(results) - 1:
            nav_row.append(InlineKeyboardButton("التالي »", callback_data="next_result"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([InlineKeyboardButton("اختيار 🥇", callback_data="select_result")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if image_url and not edit_message:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif edit_message and hasattr(update, 'callback_query'):
                if image_url:
                    await update.callback_query.edit_message_caption(
                        caption=caption,
                        reply_markup=reply_markup
                    )
                else:
                    await update.callback_query.edit_message_text(
                        text=caption,
                        reply_markup=reply_markup
                    )
            else:
                await update.message.reply_text(caption, reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error showing result: {e}")
            await update.message.reply_text(caption, reply_markup=reply_markup)
    
    async def navigate_results(self, query, user_id: int, direction: int):
        """Navigate through search results"""
        current_index = users_data[user_id]['current_result_index']
        results = users_data[user_id]['search_results']
        
        new_index = current_index + direction
        
        if 0 <= new_index < len(results):
            users_data[user_id]['current_result_index'] = new_index
            
            # Create a mock update object for show_search_result
            class MockUpdate:
                def __init__(self, callback_query):
                    self.callback_query = callback_query
                    self.message = None
            
            mock_update = MockUpdate(query)
            await self.show_search_result(mock_update, user_id, edit_message=True)
    
    async def select_result(self, query, user_id: int):
        """Handle result selection"""
        results = users_data[user_id]['search_results']
        index = users_data[user_id]['current_result_index']
        
        if results and index < len(results):
            result = results[index]
            
            # Remove keyboard and show selected result
            if 'webformatURL' in result:
                caption = f"✅ تم اختيار النتيجة\n"
                caption += f"👀 المشاهدات: {result.get('views', 'غير محدد')}\n"
                caption += f"👍 الإعجابات: {result.get('likes', 'غير محدد')}\n"
                caption += f"📥 التحميلات: {result.get('downloads', 'غير محدد')}"
                
                await query.edit_message_caption(caption=caption)
            else:
                caption = f"✅ تم اختيار النتيجة\n"
                caption += f"🎵 {result.get('name', 'غير محدد')}\n"
                caption += f"🎤 الفنان: {result.get('artist', 'غير محدد')}\n"
                caption += f"⏱️ المدة: {result.get('duration', 'غير محدد')} ثانية"
                
                await query.edit_message_text(caption)
    
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin commands"""
        command = update.message.text.split()
        
        if len(command) < 2:
            await self.show_admin_panel(update)
            return
        
        action = command[1]
        
        if action == "panel":
            await self.show_admin_panel(update)
        
        elif action == "ban" and len(command) >= 3:
            try:
                target_id = int(command[2])
                banned_users.add(target_id)
                await update.message.reply_text(f"✅ تم حظر المستخدم {target_id}")
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم غير صحيح")
        
        elif action == "unban" and len(command) >= 3:
            try:
                target_id = int(command[2])
                banned_users.discard(target_id)
                await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {target_id}")
            except ValueError:
                await update.message.reply_text("❌ معرف المستخدم غير صحيح")
        
        elif action == "stats":
            await self.show_bot_stats(update)
        
        elif action == "broadcast" and len(command) >= 3:
            message = " ".join(command[2:])
            await self.broadcast_message(update, message)
        
        elif action == "addchannel" and len(command) >= 3:
            channel = command[2]
            if not channel.startswith('@'):
                channel = '@' + channel
            force_channels.append(channel)
            await update.message.reply_text(f"✅ تم إضافة القناة {channel} للاشتراك الإجباري")
        
        elif action == "removechannel" and len(command) >= 3:
            channel = command[2]
            if not channel.startswith('@'):
                channel = '@' + channel
            if channel in force_channels:
                force_channels.remove(channel)
                await update.message.reply_text(f"✅ تم إزالة القناة {channel} من الاشتراك الإجباري")
            else:
                await update.message.reply_text(f"❌ القناة {channel} غير موجودة في قائمة الاشتراك الإجباري")
    
    async def show_admin_panel(self, update: Update):
        """Show admin control panel"""
        message = """🔧 لوحة تحكم المدير

الأوامر المتاحة:
/admin panel - عرض هذه اللوحة
/admin stats - إحصائيات البوت
/admin ban [ID] - حظر مستخدم
/admin unban [ID] - إلغاء حظر مستخدم
/admin broadcast [message] - إرسال رسالة لجميع المستخدمين
/admin addchannel [channel] - إضافة قناة للاشتراك الإجباري
/admin removechannel [channel] - إزالة قناة من الاشتراك الإجباري"""
        
        await update.message.reply_text(message)
    
    async def show_bot_stats(self, update: Update):
        """Show bot statistics"""
        start_date = datetime.fromisoformat(bot_stats['start_date'])
        days_running = (datetime.now() - start_date).days
        
        message = f"""📊 إحصائيات البوت

👥 إجمالي المستخدمين: {bot_stats['total_users']}
🔍 إجمالي البحثات: {bot_stats['total_searches']}
📢 قنوات الاشتراك الإجباري: {len(force_channels)}
🚫 المستخدمون المحظورون: {len(banned_users)}
📅 أيام تشغيل البوت: {days_running}
🕐 تاريخ بدء البوت: {start_date.strftime('%Y-%m-%d %H:%M')}

القنوات المطلوبة للاشتراك:
{chr(10).join(force_channels) if force_channels else 'لا توجد قنوات'}"""
        
        await update.message.reply_text(message)
    
    async def broadcast_message(self, update: Update, message: str):
        """Broadcast message to all users"""
        sent_count = 0
        failed_count = 0
        
        for user_id in users_data.keys():
            try:
                await update.get_bot().send_message(chat_id=user_id, text=message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id}: {e}")
                failed_count += 1
        
        await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {sent_count} مستخدم\n❌ فشل الإرسال إلى {failed_count} مستخدم")
    
    async def handle_admin_callback(self, query, data: str):
        """Handle admin callback queries"""
        # Implementation for admin callback handling
        pass

def main():
    """Start the bot"""
    # Create bot instance
    bot = PixabayBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start the bot
    logger.info("Starting Pixabay Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()