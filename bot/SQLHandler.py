from loguru import logger
import psycopg2

class SQLHandler:

    # def __init__(self) -> None:
        # self.conn_arg=
    @logger.catch
    def sql_unsubscribe_from(self, chat_id, forum_full_name):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        '''Отписался от форума'''
        cur.execute(f"""
            DELETE FROM forum_subscriber
                WHERE
                    subscriber_id=(
                        SELECT id FROM subscriber WHERE chat_id={chat_id}
                    )
                AND forum_id=(
                    SELECT id FROM forum WHERE full_name='{forum_full_name}'
                )
                RETURNING date_subscribed
        """)
        success = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return success

    @logger.catch
    def sql_list_unsubscriptions(self, chat_id):
        logger.debug(f'123 {self.conn_arg=}')
        conn = psycopg2.connect(self.conn_arg)
        cur = conn.cursor()
        '''Подписан на форумы:'''
        cur.execute(f"""
            SELECT * FROM forum WHERE id NOT IN(
                SELECT forum_id FROM forum_subscriber WHERE subscriber_id=(
                    SELECT id FROM subscriber WHERE chat_id={chat_id}
                )
            )
        """)
        sub = cur.fetchall()
        logger.info(f'{sub=}')
        cur.close()
        conn.close()
        return sub

    @logger.catch
    def sql_list_subscriptions(self, chat_id):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        '''Подписан на форумы:'''
        cur.execute(f"""
            SELECT * FROM forum WHERE id IN(
                SELECT forum_id FROM forum_subscriber WHERE subscriber_id=(
                    SELECT id FROM subscriber WHERE chat_id={chat_id}
                )
            )
        """)
        sub = cur.fetchall()
        logger.info(f'{sub=}')
        cur.close()
        conn.close()
        return sub

    @logger.catch
    def sql_subscribe(self, first_name, last_name, chat_id, forum):
        
        conn = psycopg2.connect(self.conn_arg)
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO subscriber VALUES (
                DEFAULT,
                '{first_name}',
                '{last_name}',
                CURRENT_TIMESTAMP,
                {chat_id}
            )
            ON CONFLICT DO NOTHING
        """)
        conn.commit()
        cur.execute(f"""
            SELECT id FROM subscriber WHERE chat_id={chat_id}
        """)
        subscriber = cur.fetchone()

        cur.execute(f"""
            SELECT id FROM forum WHERE full_name='{forum}'
        """)
        forum_id = cur.fetchone()[0]

        cur.execute(f"""
        INSERT INTO forum_subscriber VALUES (
            {forum_id},
            '{subscriber[0]}',
            CURRENT_TIMESTAMP,
            DEFAULT
        )
        ON CONFLICT DO NOTHING
        RETURNING date_subscribed
        """)
        conn.commit()
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result