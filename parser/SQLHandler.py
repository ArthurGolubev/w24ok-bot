from loguru import logger
import psycopg2

class SQLHandler:

    @logger.catch
    def sql_select_subscribers(self, forum_id):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        cur.execute(f"""
            SELECT * FROM subscriber WHERE id IN (
                SELECT subscriber_id FROM forum_subscriber WHERE forum_id='{forum_id}'
            )
        """)
        subscribers = cur.fetchall()
        cur.close()
        conn.close()
        return subscribers

    @logger.catch
    def sql_insert_comment_into_db(self, last_comment):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO
                participant (id, username) VALUES (DEFAULT, '{last_comment["participant"]}')
            ON CONFLICT DO NOTHING
        """)
        conn.commit()
        cur.execute(f"""
            SELECT id from participant WHERE username='{last_comment["participant"]}'
        """)
        participant = cur.fetchone()[0]
        cur.execute(f"""
            INSERT INTO
                comment (
                    id,
                    forum_id,
                    comment_timestamp,
                    comment_id,
                    comment_text,
                    participant_id
                    )
            VALUES
                (
                    DEFAULT,
                    '{last_comment["forum_id"]}',
                    NOW(),
                    '{last_comment["comment_id"]}',
                    '{last_comment["comment_text"].replace("'", "-").replace('"', "-").replace("`", "-")}',
                    '{participant}'
                    )
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        conn.commit()
        new_comment = cur.fetchone()
        cur.close()
        conn.close()
        return new_comment

    @logger.catch
    def sql_last_comment(self, forum_id):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        cur.execute(f"""
            SELECT * FROM comment WHERE forum_id={forum_id} ORDER BY comment_timestamp DESC LIMIT 1
        """)
        comment = cur.fetchone()
        cur.close()
        conn.close()
        return comment
        
    @logger.catch
    def sql_get_forums(self):
        conn = psycopg2.connect(self.conn_arg) 
        cur = conn.cursor()
        '''Склады'''
        cur.execute("""
            SELECT * FROM forum
        """)
        forums = cur.fetchall()
        cur.close()
        conn.close()
        return forums
