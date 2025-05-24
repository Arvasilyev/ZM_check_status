import os
from datetime import datetime, timedelta
import psutil
import subprocess
import glob  # Для работы с шаблонами директорий
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # Для планировщика задач
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройки
TELEGRAM_BOT_TOKEN = '8************'  # Ваш токен
CHECK_INTERVAL_MINUTES = 2  # Интервал проверки записей в минутах

# Глобальная переменная для хранения chat_id
CHAT_ID = *******

# Список директорий для проверки записей ZoneMinder
DIRECTORIES_TO_CHECK = [
    'mntdisk2zonemindervideo32025-05',
    'mntdisk2zonemindervideo42025-05',
    'mntdisk3zonemindervideo32025-05',
    'mntdisk3zonemindervideo42025-05'
]

# Команда start
async def start(update Update, context ContextTypes.DEFAULT_TYPE)
    global CHAT_ID
    try
        logger.info(Команда start выполнена.)
        CHAT_ID = update.message.chat_id  # Сохраняем chat_id
        await update.message.reply_text(
            Доступные командыn
            server_status — Проверить состояние сервераn
            zm_status — Проверить статус записей в ZoneMinder
        )
    except Exception as e
        logger.error(fОшибка при выполнении команды start {e})

# Проверка состояния сервера
def check_server_status()
    try
        logger.info(Начало проверки состояния сервера...)

        # Список дисков для проверки
        disks_to_check = [
            {'mount_point' '', 'name' 'Системный диск'},
            {'mount_point' 'mntdisk3', 'name' 'Основной диск'},
            {'mount_point' 'mntdisk2', 'name' 'Резервный диск'}
        ]

        disk_info = []
        for disk in disks_to_check
            try
                logger.info(fПроверка свободного места на {disk['name']} ({disk['mount_point']})...)
                disk_usage = psutil.disk_usage(disk['mount_point'])
                free_space_gb = round(disk_usage.free  (1024  3), 2)
                total_space_gb = round(disk_usage.total  (1024  3), 2)
                disk_info.append(f{disk['name']} {free_space_gb} GB свободно из {total_space_gb} GB)
                logger.info(f{disk['name']} {free_space_gb} GB свободно из {total_space_gb} GB)
            except Exception as e
                logger.error(fОшибка при проверке свободного места на {disk['name']} {e})
                disk_info.append(f{disk['name']} Недоступно)

        # Загрузка CPU
        try
            logger.info(Проверка загрузки CPU...)
            cpu_usage = psutil.cpu_percent(interval=1)
            logger.info(fЗагрузка CPU {cpu_usage}%)
        except Exception as e
            logger.error(fОшибка при проверке загрузки CPU {e})
            cpu_usage = Недоступно

        # Температура CPU
        try
            logger.info(Проверка температуры CPU...)
            result = subprocess.run(['sensors'], stdout=subprocess.PIPE, text=True)
            cpu_temp = None

            # Ищем строку с температурой temp1
            for line in result.stdout.splitlines()
                if 'temp1' in line and '(high' in line  # Выбираем строку с temp1 и high
                    cpu_temp = line.split()[1]  # Берём второе значение (температура)
                    break

            if not cpu_temp
                cpu_temp = Температура недоступна
            else
                logger.info(fТемпература CPU {cpu_temp})

        except Exception as e
            logger.error(fОшибка при проверке температуры CPU {e})
            cpu_temp = Температура недоступна

        return {
            disk_info disk_info,
            cpu_usage cpu_usage,
            cpu_temp cpu_temp,
            ip_address get_ip_address('enp0s7'),
        }
    except Exception as e
        logger.error(fКритическая ошибка при проверке состояния сервера {e})
        return {
            disk_info [Состояние дисков Недоступно],
            cpu_usage Недоступно,
            cpu_temp Недоступно,
        }

#Получение адреса
def get_ip_address(interface='enp0s7')
    try
        result = subprocess.run(['ip', 'addr', 'show', interface],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode != 0
            return Неизвестный IP
        for line in result.stdout.splitlines()
            if 'inet ' in line and not 'inet6' in line
                ip = line.strip().split()[1].split('')[0]
                return ip
        return Неизвестный IP
    except Exception as e
        logger.error(fОшибка при получении IP-адреса {e})
        return Неизвестный IP

# Проверка записей в ZoneMinder
def check_recordings()
    try
        logger.info(Проверка записей в ZoneMinder...)
        now = datetime.now()
        threshold_time = now - timedelta(minutes=CHECK_INTERVAL_MINUTES)

        # Проходим по всем указанным шаблонам директорий
        recent_files_found = False
        for directory_pattern in DIRECTORIES_TO_CHECK
#            logger.info(fПроверка директорий по шаблону {directory_pattern})
            
            # Получаем список директорий, соответствующих шаблону
            matching_directories = glob.glob(directory_pattern)
            
            if not matching_directories
#                logger.warning(fНет директорий, соответствующих шаблону {directory_pattern})
                continue

            for directory in matching_directories
#               logger.info(fПроверка директории {directory})
                
                # Проверяем, что это директория
                if not os.path.isdir(directory)
#                    logger.warning(fПуть не является директорией {directory})
                    continue

                try
                    # Рекурсивно обходим файлы в директории
                    for root, dirs, files in os.walk(directory)
#                        logger.debug(fПроверка файлов в директории {root})
                        
                        for file in files
                            file_path = os.path.join(root, file)
                            
                            # Проверяем, что это файл
                            if not os.path.isfile(file_path)
#                                logger.warning(fПуть не является файлом {file_path})
                                continue

                            # Проверяем время модификации файла
                            try
                                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
#                                logger.debug(fПроверен файл {file_path}, время модификации {file_mtime})
                                
                                if file_mtime  threshold_time
#                                    logger.info(fНайден новый файл {file_path})
                                    recent_files_found = True
                                    break  # Прекращаем поиск, если нашли новый файл
                            except Exception as e
                                logger.error(fОшибка при проверке файла {file_path} {e})
                        
                        if recent_files_found
                            break  # Прекращаем поиск, если нашли новый файл
                
                except Exception as e
                    logger.error(fОшибка при обходе директории {directory} {e})

                if recent_files_found
                    break  # Прекращаем поиск, если нашли новый файл

        return recent_files_found
    except Exception as e
        logger.error(fКритическая ошибка при проверке записей в ZoneMinder {e})
        return False

# Команда server_status
async def server_status(update Update, context ContextTypes.DEFAULT_TYPE)
    try
        logger.info(Команда server_status выполнена.)
        server_status = check_server_status()

        # Формируем сообщение о состоянии дисков
        disk_message = n.join(server_status[disk_info])

        status_message = (
            f📊 Состояние сервераn
            f💿 Дискиn{disk_message}n
            f💻 Загрузка CPU {server_status['cpu_usage']}%n
            f🌡️ Температура CPU {server_status['cpu_temp']}n
            f🔗 Перейти к записям камеры http{server_status['ip_address']}zm
        )
        await update.message.reply_text(status_message)
    except Exception as e
        logger.error(fОшибка при выполнении команды server_status {e})
        await update.message.reply_text(Произошла ошибка при проверке состояния сервера.)

# Команда zm_status
async def zm_status(update Update, context ContextTypes.DEFAULT_TYPE)
    try
        logger.info(Команда zm_status выполнена.)
        if check_recordings()
            await update.message.reply_text(✅ Запись в ZoneMinder активна.)
        else
            await update.message.reply_text(⚠️ Запись в ZoneMinder прекратилась!)
    except Exception as e
        logger.error(fОшибка при выполнении команды zm_status {e})
        await update.message.reply_text(Произошла ошибка при проверке статуса записей.)

# Автоматическая проверка записей
async def auto_check_recordings(context ContextTypes.DEFAULT_TYPE)
    global CHAT_ID
    try
        logger.info(Автоматическая проверка записей в ZoneMinder...)
        if check_recordings()
            logger.info(Запись в ZoneMinder активна.)
        else
            logger.warning(Запись в ZoneMinder прекратилась!)
            if CHAT_ID
                try
                    await context.bot.send_message(chat_id=CHAT_ID, text=⚠️ Запись в ZoneMinder прекратилась!)
                except Exception as e
                    logger.error(fОшибка при отправке уведомления {e})
            else
                logger.error(Не могу отправить уведомление chat_id не установлен.)
    except Exception as e
        logger.error(fОшибка при автоматической проверке записей {e})

# Основная функция
def main()
    try
        logger.info(Запуск бота...)
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Добавляем обработчики команд
        application.add_handler(CommandHandler(start, start))
        application.add_handler(CommandHandler(server_status, server_status))
        application.add_handler(CommandHandler(zm_status, zm_status))

        # Добавляем планировщик задач
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            auto_check_recordings,
            'interval',
            minutes=CHECK_INTERVAL_MINUTES,
            args=[application]
        )
        scheduler.start()

        application.run_polling()
    except Exception as e
        logger.critical(fКритическая ошибка при запуске бота {e})

if __name__ == __main__
    main()
