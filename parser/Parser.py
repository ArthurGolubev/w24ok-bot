import os
from loguru import logger
from time import sleep
from notifiers import get_notifier
from notifiers.logging import NotificationHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from SQLHandler import SQLHandler

class Parser(SQLHandler):
    @logger.catch
    def __init__(self):
        self.comments = {}
        self.conn_arg = os.getenv("W24OK_BOT_DB_CONN_ARGS")
        logger.debug(f'{self.conn_arg=}')
        logger.info(f'{os.getenv("W24OK_MASTER_BOT_TOKEN")=}')
        # logger через telegram для MasterBot
        self.params = {
            "token": os.getenv("W24OK_MASTER_BOT_TOKEN"),
            "chat_id": int(os.getenv(f"MY_CHAT_ID")),
            "parse_mode": "html"
        }

        handler = NotificationHandler('telegram', defaults=self.params)
        logger.add(handler, level="INFO")
        # logger.add('/home/containers/w24ok-bot/logs/ParserParser.log', rotation="10:00", compression="zip", level="INFO", retention=7)
        logger.info(f'\n\n\U0001F9FE <b><i>Start ParserParser</i></b>')

        self.telegram = get_notifier('telegram')
        
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.page_load_strategy = 'eager'
        self.browser    = webdriver.Remote("http://w24ok-bot-selenium-svc:4444/wd/hub", options=options)
        self.auth()
        
        # self.sql_create_tables()
        self.forums = self.sql_get_forums()
        try:
            self.start_monitoring()
        except Exception as e:
            logger.error(f'{e=}')
        finally:
            self.browser.quit()


    @logger.catch
    def auth(self):

        self.browser.get('https://24-ok.ru/user/login')
        login_input     = self.browser.find_element('xpath', '//input[@id="loginform-username"]')
        password_input  = self.browser.find_element('xpath', '//input[@id="loginform-password"]')
        # button          = self.browser.find_element('xpath', '//button[@type="submit" and contains(@class, "btn") and contains(@class, "btn-gray-245") and contains(@class, "rounded-lg") and contains(@class, "px-4")]')
        button          = self.browser.find_element('xpath', '//button[@type="submit" and contains(@class, "btn") and contains(@class, "btn-dark-12") ]')
        logger.info(f"{button=}")
        login_input.send_keys(os.getenv("FORUM0"))
        password_input.send_keys(os.getenv("FORUM1"))
        button.click()
        sleep(10)
        if(self.browser.current_url == 'https://24-ok.ru/site/index?logaction=success'):
            logger.info(f'\n\n<b><i>ParserParser auth successfully</i></b>')
        else:
            logger.info(f'{self.browser.current_url=}')
            logger.info(f'\n\n<b><i>ParserParser auth failed</i></b>')


    @logger.catch
    def start_monitoring(self):
        """Следить за последним коментарием темы ЦРа. Если появятся изменения - отправить всем подпищикам на бота этой темы"""
        logger.info(f'start forum monitoring')

        # Step 1: Первая инициализация комента - последнего комента из БД
        for forum in self.forums:
            short_name = forum[1]
            comment = self.sql_last_comment(forum_id=forum[0])
            self.comments[short_name] = comment

        while(True):
            for forum in self.forums:
                self.forum_monitoring(forum)

    @logger.catch
    def forum_monitoring(self, forum):
        # Step 2: проход по всем страницам и сравнения комента в кэше с последнем на странице
        self.browser.get(forum[3])
        sleep(5)
        last_comment = self.get_last_comment(forum) # Последний комент на странице
        if not self.comments[forum[1]] or last_comment.get('comment_id') != self.comments[forum[1]][3]:
            '''Сохраняем его в БД'''
            new_comment = self.sql_insert_comment_into_db(last_comment)
            if new_comment:
                short_name = forum[1]
                comment = self.sql_last_comment(forum_id=forum[0])
                self.comments[short_name] = comment
                
                subscribers = self.sql_select_subscribers(forum_id=forum[0])
            
                for subscriber in subscribers:
                    logger.info(f'sub -> {subscriber}')
                    params = {
                        "token": os.getenv(f"FORUM_MONITORING_BOT"),
                        "chat_id": subscriber[4],
                        "parse_mode": "html"
                    }
                    self.telegram.notify(
                        message=f'<b><i>\U0001F4AC {forum[2]}</i></b>\n\n<b>\U0001f464 {last_comment["participant"]}</b>\n\n{last_comment["comment_text"]}',
                        **params
                        )

    @logger.catch
    def get_last_comment(self, forum):
        """Найти последний коментарий из списка коментариев на открытой странице темы ЦРа"""
        # последняя карточка
        elem = self.browser.find_elements('xpath', f".//div[contains(@class, 'row') and contains(@class, 'h-100')]")[-1]

        return {
            'comment_id': elem.find_element("xpath",".//div[contains(@id, 'pt')]").get_attribute('id'),
            'comment_text': elem.find_element("xpath",".//div[contains(@id, 'pt')]").text,
            'participant': elem.find_element("xpath",".//a[contains(@class, 'font-weight-bold')]").text,
            'forum_id': forum[0],
            'forum_short_name': forum[1]
            }


    
if __name__ == "__main__":
    Parser()