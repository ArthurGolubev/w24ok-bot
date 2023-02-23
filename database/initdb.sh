#! /bin/bash

set -e

psql -v ON_ERROR_STOP = 1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS forum (
                id SERIAL PRIMARY KEY,
                short_name varchar(10) UNIQUE,
                full_name varchar(100),
                page varchar(255)
            );
    
    CREATE TABLE IF NOT EXISTS subscriber (
                id SERIAL PRIMARY KEY,
                first_name varchar(50),
                last_name varchar(50) NULL,
                subsc_date timestamp,
                chat_id integer UNIQUE
            );

    CREATE TABLE IF NOT EXISTS forum_subscriber (
                    forum_id int NOT NULL,
                    subscriber_id int NOT NULL,
                    date_subscribed timestamp,
                    active boolean DEFAULT true,
                    PRIMARY KEY (forum_id, subscriber_id),
                    FOREIGN KEY (subscriber_id) REFERENCES subscriber(id) ON UPDATE CASCADE,
                    FOREIGN KEY (forum_id) REFERENCES forum(id) ON UPDATE CASCADE
                );
    
    CREATE TABLE IF NOT EXISTS participant (
                id SERIAL PRIMARY KEY,
                username varchar(255) UNIQUE
            );
    
    CREATE TABLE IF NOT EXISTS comment (
                id SERIAL PRIMARY KEY,
                forum_id integer,
                comment_timestamp timestamp,
                comment_id varchar(50) UNIQUE,
                comment_text varchar(500),
                participant_id integer,
                CONSTRAINT forum_id FOREIGN KEY (forum_id) REFERENCES forum(id),
                CONSTRAINT participant_id FOREIGN KEY (participant_id) REFERENCES participant(id)
            );

    INSERT INTO forum(
        id, short_name, full_name, page)
        VALUES (DEFAULT, 'YP', 'Ястынское поле', 'https://24-ok.ru/topic/99743?page=20000');
        
    INSERT INTO forum(
        id, short_name, full_name, page)
        VALUES (DEFAULT, 'MS', 'Мамино солнышко', 'https://24-ok.ru/topic/3510?page=20000');
        
    INSERT INTO forum(
        id, short_name, full_name, page)
        VALUES (DEFAULT, 'AN', 'Андреевский', 'https://24-ok.ru/topic/301162?page=20000');
            
    INSERT INTO forum(
        id, short_name, full_name, page)
        VALUES (DEFAULT, 'ZH1', 'Железногорск', 'https://24-ok.ru/topic/5770?page=20000');
        
    INSERT INTO forum(
        id, short_name, full_name, page)
        VALUES (DEFAULT, 'ZH2', 'Железногорск - Ленинградский', 'https://24-ok.ru/topic/71396?page=20000');
EOSQL