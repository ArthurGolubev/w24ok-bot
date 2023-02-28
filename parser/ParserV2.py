import os
import re
from time import sleep
from loguru import logger
from bs4 import BeautifulSoup
from notifiers import get_notifier
from urllib.request import urlopen
from notifiers.logging import NotificationHandler
from SQLHandler import SQLHandler


class ParserV2(SQLHandler):
    def __init__(self) -> None:
        self.comments = {}
        self.conn_arg = os.getenv("W24OK_BOT_DB_CONN_ARGS")
        self.params = {
            "token": os.getenv("W24OK_MASTER_BOT_TOKEN"),
            "chat_id": int(os.getenv(f"MY_CHAT_ID")),
            "parse_mode": "html"
        }

        handler = NotificationHandler('telegram', defaults=self.params)
        logger.add(handler, level="INFO")
        logger.info(f'\n\n\U0001F9FE <b><i>Start ParserParser</i></b>')
        self.telegram = get_notifier('telegram')
        self.forums = self.sql_get_forums()




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
                sleep(10)


    def forum_monitoring(self, forum):
        # Step 2: проход по всем страницам и сравнения комента в кэше с последнем на странице
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
                    logger.info(f'sub -> {subscriber} sand message')
                    params = {
                        "token": os.getenv(f"FORUM_MONITORING_BOT"),
                        "chat_id": subscriber[4],
                        "parse_mode": "html"
                    }
                    self.telegram.notify(
                        message=f'<b><i>\U0001F4AC {forum[2]}</i></b>\n\n<b>\U0001f464 {last_comment["participant"]}</b>\n\n{last_comment["comment_text"]}',
                        **params
                        )



    def get_last_comment(self, forum):
        """Найти последний коментарий из списка коментариев на открытой странице темы ЦРа"""
        html = urlopen(forum[3])

        html = html.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        # последняя карточка
        last_comment = soup.find_all('div', ['row h-100'])[-1]
        id_ = last_comment.find("div", id=re.compile("^pt")).attrs.get("id")
        text = last_comment.find("div", id=re.compile("^pt")).text.strip()
        participant = last_comment.find("a", class_='font-weight-bold').text

        return {
            'comment_id': id_,
            'comment_text': text,
            'participant': participant,
            'forum_id': forum[0],
            'forum_short_name': forum[1]
            }

if __name__ == '__main__':
    p = ParserV2()
    p.start_monitoring()