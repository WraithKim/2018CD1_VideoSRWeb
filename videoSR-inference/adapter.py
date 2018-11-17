#! /usr/bin/env python

import sys, pika, psycopg2
import json, logging, logging.config, time
# from inf_prosr import Infmodule_proSR

PROJECT_DIR = "/home/wraithkim/videoSRWeb/"

# logger config
with open(PROJECT_DIR + 'videosr/videoSR-inference/logging.json', 'r') as f:
    logConfig = json.load(f)

logging.config.dictConfig(logConfig)

logger = logging.getLogger("sr_adapter")

# 이 프로그램에서 발생한 처리되지 않은 예외를 로그로 기록함.
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# db config
with open(PROJECT_DIR + 'config.json', 'r') as f:
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

    def __init__(self, srm_scale2, srm_scale4):
        self.srm_scale2 = srm_scale2
        self.srm_scale4 = srm_scale4

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

        #### SR 모듈에서 발생한 에러는 심각한 것이므로 관리자가 해결해야 함. 따라서 예외처리하지 않고 로그로만 남김.

        ### 메세지 처리
        logger.info("Received %r" % body)
        # list[0] = file_id, list[1] = 처리할 파일 경로, list[2] = 처리 후 결과물 dir, list[3] = scale factor
        decoded_body = body.decode('utf-8')
        file_info_list = decoded_body.split(" ")
        file_id = int(file_info_list[0])
        scale_factor = int(file_info_list[3])

        time.sleep(10) # FIXME: Test용 코드
        self._update_state(file_id, "IP")
        if scale_factor == 2:
            logger.info("SR x2 start file: {}".format(file_id))
            # self.srm_scale2.sr_video_nosr(file_info_list[1], file_info_list[2])
        if scale_factor == 4:
            logger.info("SR x4 start file: {}".format(file_id))
            # self.srm_scale4.sr_video_nosr(file_info_list[1], file_info_list[2])
        time.sleep(30) # FIXME: Test용 코드

        self._update_state(file_id, "FI")
        logger.info("file id {} Done".format(file_id))
        ### 메세지 처리 끝

        # 반드시 큐에도 ack를 보내야 큐에서도 메세지가 사라짐
        # (그렇지 않으면 큐에 이 작업이 다시 들어감)
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def _update_state(self, file_id, status):
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
            cur.execute(sql, (status, file_id))
            # get the number of updated rows
            updated_rows = cur.rowcount
            # Commit the changes to the database
            conn.commit()
            # Close communication with the PostgreSQL database
            cur.close()
            logger.info("UPDATE progress to {}: {}".format(status, file_id))
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
            if self.srm_scale2 is None or self.srm_scale4 is None:
                logger.error("SR Module doesn't exist")
                return
        self._run_mq()


def main():
    # srm_scale2 = Infmodule_proSR(model_path=PROJECT_DIR+"model/proSR/proSR_x2.pth", is_CUDA=False)
    # srm_scale4 = Infmodule_proSR(model_path=PROJECT_DIR+"model/proSR/proSR_x4.pth", is_CUDA=False)
    srm_scale2 = None
    srm_scale4 = None
    adapter = SRDefaultWebAdapter(srm_scale2, srm_scale4)
    logger.info("SR Module on")
    adapter.run_module(is_test=True)

if __name__ == "__main__":
    main()
