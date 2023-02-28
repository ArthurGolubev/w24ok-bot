import os

from loguru import logger
from telegram.constants import ParseMode
from SQLHandler import SQLHandler
from notifiers.logging import NotificationHandler

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, Application

class Bot(SQLHandler):
    help = "Всегда активный бот, дающий возможность подписаться через хендлер sub"
    def __init__(self):
        self.conn_arg = os.getenv("W24OK_BOT_DB_CONN_ARGS")
        self.params = {
            "token": os.getenv("W24OK_MASTER_BOT_TOKEN"),
            "chat_id": int(os.getenv(f"MY_CHAT_ID")),
            "parse_mode": "html"
        }
        self.handler = NotificationHandler('telegram', defaults=self.params)
        logger.add(self.handler, level="INFO")
        # logger.add('/home/containers/w24ok-bot/logs/BotBot.log', rotation="10:00", compression="zip", level="INFO", retention=7)


        application = Application.builder().token(os.getenv(f"FORUM_MONITORING_BOT")).build()

        #  handlers

        conv_handler_subscribe = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^(Подписаться|подписаться|Список|список)$'), self.sub_step_1)],
            states={
                0: [MessageHandler(filters.Regex(
                    '^(Ястынское поле|Мамино солнышко|Андреевский|Железногорск|Железногорск - Ленинградский)$'), self.sub_step_2)],
            },
            fallbacks=[CommandHandler('cancel', self.fallbacks)],
        )
        conv_handler_unsubscribe = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^(Отписаться|отписаться)$'), self.unsub_step_1)],
            states={
                0: [MessageHandler(filters.Regex(
                    '^(Ястынское поле|Мамино солнышко|Андреевский|Железногорск|Железногорск - Ленинградский)$'), self.unsub_step_2)],
            },
            fallbacks=[CommandHandler('cancel', self.fallbacks)],
        )
        # unsubscribe = MessageHandler(Regex('^(Отписаться|отписаться)$'), self.unsubscribe)

        application.add_handler(conv_handler_subscribe)
        application.add_handler(conv_handler_unsubscribe)

        #  add to dispatcher
        logger.info(f'\n\n\U0001F916 <b><i>Start СледящийЗаТемой-Бот</i></b>')
        
        application.run_polling()


    @logger.catch
    async def unsub_step_1(self, update, context):
        chat_id   = update.message.chat.id
        subscriptions = self.sql_list_subscriptions(chat_id)
        logger.info(f'{subscriptions=}')
        if len(subscriptions) != 0:
            reply_keyboard = [[forum[2]] for forum in subscriptions]
            if not reply_keyboard:
                reply_keyboard=[['/cancel']]
                await update.message.reply_text(
                    'Нет подписок',
                    reply_markup=ReplyKeyboardMarkup(
                        reply_keyboard, one_time_keyboard=True
                    ),
                )
            else:
                await update.message.reply_text(
                'Отписаться от:',
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
        return 0

    @logger.catch
    async def unsub_step_2(self, update, context):
        chat_id   = update.message.chat.id
        success = self.sql_unsubscribe_from(chat_id, update.message.text)

        first_name  = update.message.chat.first_name
        last_name   = update.message.chat.last_name
        if success:
            logger.info(f'\n\n\U0001F916 <b>Bot {update.message.text}</b>\n<b>Success unsubscribed!\nUser: {first_name} {last_name}</b>')
            await update.message.reply_text(
                text=f'<b>\u261D Отписка оформлена!</b>',
                reply_markup=ReplyKeyboardMarkup(
                    [['Подписаться'], ['Отписаться']], one_time_keyboard=True
                ),    
                parse_mode=ParseMode.HTML)
        else:
            logger.info(f'\n\n\U0001F916 <b>Bot {update.message.text}</b>\n<b>User: {first_name} {last_name}</b>\n<i>Failure unsubscribed!</i>\n')
            await update.message.reply_text(
                text=f'<b>\u261D Отписка <i>не</i> оформлена!</b>',
                reply_markup=ReplyKeyboardMarkup(
                    [['Подписаться'], ['Отписаться']], one_time_keyboard=True
                ),
                parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        

    @logger.catch
    async def fallbacks(self, update, context):
        await update.message.reply_text(
            'Темы на выбор:',
            reply_markup=ReplyKeyboardMarkup(
                [['Подписаться'], ['Отписаться']], one_time_keyboard=True
            ),    
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    @logger.catch
    async def sub_step_1(self, update, context):
        logger.info(f'Step 1')
        chat_id   = update.message.chat.id
        logger.info(f'{chat_id=}')
        subscriptions = self.sql_list_unsubscriptions(chat_id)
        logger.info(f'{subscriptions=}')
        reply_keyboard = [[forum[2]] for forum in subscriptions]
        if not reply_keyboard:
            reply_keyboard=[['/cancel']]
            await update.message.reply_text(
                'Подписка уже оформлена на всё',
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
        else:
            await update.message.reply_text(
            'Подписаться на:',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            ),
        )

        return 0

    @logger.catch
    async def sub_step_2(self, update, context):
        logger.info(f'Step 2')
        logger.info(f'{update.message=}')
        logger.info(f'{update.message.chat.first_name=}')
        logger.info(f'{update.message.chat.last_name=}')
        logger.info(f'{update.message.chat.id=}')
        first_name  = update.message.chat.first_name
        last_name   = update.message.chat.last_name
        chat_id   = update.message.chat.id
        if not first_name: first_name = '\u2014'
        if not last_name: last_name = '\u2014'

        sub = self.sql_subscribe(
            first_name=first_name,
            last_name=last_name,
            chat_id=chat_id,
            forum=update.message.text
            )
        logger.info(f'{sub=}')
        

        if sub:
            logger.info(f'\n\n\U0001F916 <b>Bot {update.message.text}</b>\n<b>#NewSubscriber!\nUser: {first_name} {last_name} {chat_id}</b>')
            await update.message.reply_text(
                text=f'<b>\u261D Подписка оформлена!</b>',
                reply_markup=ReplyKeyboardMarkup(
                    [['Подписаться'], ['Отписаться']], one_time_keyboard=True
                ),    
                parse_mode=ParseMode.HTML)
        else:
            logger.info(f'\n\n\U0001F916 <b>Bot {update.message.text}</b>\n<b>User: {first_name} {last_name}</b>\n<i>Already subscribed!</i>\n')
            await update.message.reply_text(
                text=f'<b>\u261D Подписка <i>уже</i> оформлена!</b>',
                reply_markup=ReplyKeyboardMarkup(
                    [['Подписаться'], ['Отписаться']], one_time_keyboard=True
                ),
                parse_mode=ParseMode.HTML)
        
        return ConversationHandler.END


if __name__ == "__main__":
    Bot()