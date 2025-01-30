from configparser import ConfigParser
from telegram import Update
from telegram.ext import (ApplicationBuilder,
                          ContextTypes,
                          filters,
                          CommandHandler,
                          MessageHandler)
import api
import db

config = ConfigParser()
config.read('config.ini')
TELEGRAM_BOT_TOKEN = config['telegram']['token']
ACTIVATION_CODE = config['activation']['code']


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /start """

    user = update.effective_user
    if db.is_user_in_whitelist(user.id):
        await update.message.reply_text('Введите <imei> <test/live>\n'
                                        'Для проверки в тестовом режиме test\nПри проверке в live режиме может быть '
                                        'исчерпан лимит запросов')
    else:
        await update.message.reply_text('Для доступа к боту, отправьте команду /activate <код>')


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /activate """

    code = context.args[0] if context.args else None
    if code == ACTIVATION_CODE:
        user_id = update.effective_user.id
        if not db.is_user_in_whitelist(user_id):
            db_sess = db.session_local()
            try:
                db.add_user(db_sess, user_id)
                await update.message.reply_text('Успешно активировано!\n'
                                                'Введите <imei> <test/live>\n'
                                                'Для проверки в тестовом режиме test\nПри проверке в live режиме может быть '
                                                'исчерпан лимит запросов')
            except Exception as _:
                await update.message.reply_text('Успешно активировано, но не удалось получить данные о пользователе!')
            finally:
                db_sess.close()
        else:
            await update.message.reply_text('Вы уже имеете доступ к боту.'
                                            'Введите <imei> <test/live>\n'
                                            'Для проверки в тестовом режиме test\nПри проверке в live режиме может быть '
                                            'исчерпан лимит запросов'
                                            )
    else:
        await update.message.reply_text(f'Неверный код активации')


async def check_imei(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Обрабатывает сообщения с IMEI-кодами """

    if db.is_user_in_whitelist(update.effective_user.id):
        try:
            text = update.message.text
            parts = text.split()
            if len(parts) != 2:
                await update.message.reply_text('Неверный формат. Введите <imei> <test/live>')
                return

            imei = parts[0].strip()
            env = parts[1].lower().strip()
            if env not in ['test', 'live']:
                await update.message.reply_text('Неверный формат. Введите <imei> <test/live>')
                return

            if env == 'test':
                on_test = True
            elif env == 'live':
                on_test = False

            if api.validator_imei(imei):
                ans = api.check_imei(imei, on_test)
                if type(ans) is str:
                    await update.message.reply_text(ans)
                else:
                    await update.message.reply_text(f'Результат проверки IMEI: {ans}')
            else:
                await update.message.reply_text('Вы ввели некорректный imei')

        except Exception as e:
            await update.message.reply_text(f'Ошибка при проверке IMEI: {e}')
    else:
        await update.message.reply_text('Извините, доступ ограничен\n'
                                        'Для доступа к боту, отправьте команду /activate <код>')


def main() -> None:
    """ Запуск бота """

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    activate_handler = CommandHandler('activate', activate)
    check_imei_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, check_imei)

    application.add_handler(start_handler)
    application.add_handler(activate_handler)
    application.add_handler(check_imei_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
