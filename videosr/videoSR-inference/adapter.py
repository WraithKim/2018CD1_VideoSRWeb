#! /usr/bin/env python

import pika, psycopg2
import json, logging, logging.config, time

# logger config
with open('/home/wraithkim/videoSRWeb/videosr/videoSR-inference/logging.json', 'r') as f:
    logConfig = json.load(f)

logging.config.dictConfig(logConfig)

logger = logging.getLogger("sr_adapter")

# db config
with open('/home/wraithkim/videoSRWeb/config.json', 'r') as f:
    dbConfig = json.load(f)

conn_string = "host='{hostname}' dbname='{dbname}' user='{username}' password='{password}'".format(
            hostname="localhost",
            dbname=dbConfig['DATABASE']['NAME'],
            username=dbConfig['DATABASE']['USER'],
            password=dbConfig['DATABASE']['PASSWORD']
        )

class SRDefaultWebAdapter:
    """SR모듈을 웹서버와 연결하기 위한 어댑터 클래스
    """
    def __init__(self, srm):
        """SR 모듈을 웹서버와 연결
        
        Arguments:
            srm {InfModule} -- 실행할 sr 모듈
        """
        self.srm = srm

    def _run_mq(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        # 어느 큐에 연결할지 선언함
        # 만약 선언한 큐가 존재하지 않으면 rabbitMQ에 자동으로 생성함.
        channel.queue_declare(queue='sr_queue', durable=True)
        # 이미 메세지를 처리 중인 worker에게는 메세지를 전달하지 않음(공평한 작업 분배)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(self._callback_mq, queue='sr_queue')

        logger.debug("Waiting for request.")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            # Gracefully close the connection
            connection.close()

    def _callback_mq(self, ch, method, properties, body):

        ### 메세지 처리
        logger.info("Received %r" % body)
        # list[0] = file_id, list[1] = 처리할 파일 경로, list[2] = 처리 후 결과물 경로
        decoded_body = body.decode('utf-8')
        file_info_list = decoded_body.split(" ")
        # FIXME: Test용 코드
        time.sleep(10)
        self._update_state_in_progress(int(file_info_list[0]))
        # FIXME: Test용 코드
        time.sleep(30)
        self._update_state_finished(int(file_info_list[0]))
        logger.info("Done")
        ### 메세지 처리 끝

        # 반드시 큐에도 ack를 보내야 큐에서도 메세지가 사라짐
        # (그렇지 않으면 큐에 이 작업이 다시 들어감)
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def _update_state_in_progress(self, file_id):
        sql = """ UPDATE videosr_uploadedfile
                    SET progress_status = %s
                    WHERE id = %s"""
        conn = None
        updated_rows = 0

        try: 
            conn = psycopg2.connect(conn_string)
            # create a new cursor
            cur = conn.cursor()
            # execute the UPDATE  statement
            cur.execute(sql, ("IP", file_id))
            # get the number of updated rows
            updated_rows = cur.rowcount
            # Commit the changes to the database
            conn.commit()
            # Close communication with the PostgreSQL database
            cur.close()
            logger.info("UPDATE progress to IP: {}".format(file_id))
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
        finally:
            if conn is not None:
                conn.close()

        return updated_rows

    def _update_state_finished(self, file_id):
        sql = """ UPDATE videosr_uploadedfile
                    SET progress_status = %s
                    WHERE id = %s"""
        conn = None
        updated_rows = 0

        try: 
            conn = psycopg2.connect(conn_string)
            # create a new cursor
            cur = conn.cursor()
            # execute the UPDATE  statement
            cur.execute(sql, ("FI", file_id))
            # get the number of updated rows
            updated_rows = cur.rowcount
            # Commit the changes to the database
            conn.commit()
            # Close communication with the PostgreSQL database
            cur.close()
            logger.info("UPDATE progress to FI: {}".format(file_id))
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
        finally:
            if conn is not None:
                conn.close()

        return updated_rows

    def run_module(self, is_test=False):
        """어댑터에 연결된 SR 모듈을 실행함
        """
        if not is_test:
            if self.srm is None:
                logger.error("SR Module doesn't exist")
                return
        self._run_mq()


def main():
    adapter = SRDefaultWebAdapter(None)
    logger.info("SR Module on")
    adapter.run_module(is_test=True)
    

if __name__ == "__main__":
    main()