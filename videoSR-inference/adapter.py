#! /usr/bin/env python

import sys, pika, psycopg2, smtplib
import json, logging, logging.config, os, time
from email.mime.text import MIMEText
from email.header import Header
from pika.exceptions import AMQPError
# from inf_prosr import Infmodule_proSR

########## adapter settings #############
PROJECT_DIR = "/home/wraithkim/videoSRWeb/" #FIXME: test(+ logger path)

##### logger config
with open(PROJECT_DIR + 'videoSR-inference/logging.json', 'r') as f:
    logConfig = json.load(f)

logging.config.dictConfig(logConfig)

logger = logging.getLogger("sr_adapter")

##### uncaught exception handling
# 이 프로그램에서 발생한 처리되지 않은 예외를 로그로 기록함.
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

##### project config
with open(PROJECT_DIR + 'config.json', 'r') as f:
    projectConfig = json.load(f)

conn_string = "host='{hostname}' dbname='{dbname}' user='{username}' password='{password}'".format(
            hostname="localhost",
            dbname=projectConfig['DATABASE']['NAME'],
            username=projectConfig['DATABASE']['USER'],
            password=projectConfig['DATABASE']['PASSWORD']
        )

smtp_host = projectConfig['MAIL']['SMTP_HOST']
smtp_port = projectConfig['MAIL']['SMTP_PORT']
smtp_email = projectConfig['MAIL']['EMAIL']
smtp_pw = projectConfig['MAIL']['PASSWORD']
############ adapter settings end ##################

class SRDefaultWebAdapter:
    """SR모듈을 웹서버와 연결하기 위한 어댑터 클래스
    """

    def __init__(self, srm_scale2, srm_scale4):
        self.srm_scale2 = srm_scale2
        self.srm_scale4 = srm_scale4

    def _run_mq(self):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = connection.channel()
    
            # 어느 큐에 연결할지 선언함
            # 만약 선언한 큐가 존재하지 않으면 rabbitMQ에 자동으로 생성함.
            channel.queue_declare(queue='sr_queue', durable=True)
            # 이미 메세지를 처리 중인 worker에게는 메세지를 전달하지 않음(공평한 작업 분배)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(self._callback_mq, queue='sr_queue')
    
            logger.debug("Waiting for request.")
            channel.start_consuming()
        except KeyboardInterrupt:
            # Gracefully close the connection
            connection.close()
        except AMQPError as e:
            logger.error(e)
            connection.close()

    def _callback_mq(self, ch, method, properties, body):

        #### SR 모듈에서 발생한 에러는 심각한 것이므로 관리자가 해결해야 함. 따라서 예외처리하지 않고 로그로만 남김.

        ### 메세지 처리
        logger.info("Received %r" % body)
        # list[0] = 파일의 pk, list[1] = 확대 배율
        decoded_body = body.decode('utf-8')
        file_info_list = decoded_body.split(" ")
        file_id = int(file_info_list[0])
        scale_factor = int(file_info_list[1])
        (user_email, file_path) = self._read_file_info(file_id)
        file_path = os.path.join(PROJECT_DIR, "media", file_path)
        (dirname, basename) = os.path.split(file_path)
        logger.debug("email: {} dirname: {} basename: {}".format(user_email, dirname, basename))
        time.sleep(10) # FIXME: Test용 코드
        self._update_state(file_id, "IP")
        if scale_factor == 2:
            logger.info("SR x2 start file: {} {}".format(file_id, file_path))
            # self.srm_scale2.sr_video(file_path, dirname)
        if scale_factor == 4:
            logger.info("SR x4 start file: {} {}".format(file_id, file_path))
            # self.srm_scale4.sr_video(file_path, dirname)
        time.sleep(15) # FIXME: Test용 코드

        self._update_state(file_id, "FI")
        self._send_mail(user_email)
        logger.info("file id {} Done".format(file_id))
        ### 메세지 처리 끝

        # 반드시 큐에도 ack를 보내야 큐에서도 메세지가 사라짐
        # (그렇지 않으면 큐에 이 작업이 다시 들어감)
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def _read_file_info(self, file_id):
        sql = """ SELECT email, uploaded_file
                        FROM dashboard_uploadedfile 
                        INNER JOIN auth_user
                        ON (dashboard_uploadedfile = auth_user.id)
                        WHERE id = %s"""
        conn = None
        row = None
        try: 
            conn = psycopg2.connect(conn_string)
            cur = conn.cursor()
            cur.execute(sql, (file_id))
            row = cur.fetchone()
            if row is not None:
                logger.info("SELECT file {} of user {}: {}".format(file_id, row[0], row[1]))

            cur.close()
        except psycopg2.DatabaseError as error:
            logger.error(error)
        finally:
            if conn is not None:
                conn.close()
        return row

    def _update_state(self, file_id, status):
        sql = """ UPDATE dashboard_uploadedfile
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
        except psycopg2.DatabaseError as error:
            logger.error(error)
        finally:
            if conn is not None:
                conn.close()

        return updated_rows

    def _send_mail(to):
        # 메시지 내용 작성
        content = '화질 개선 작업이 완료되었습니다\n'\
                + '본 사이트에 접속하시어 결과물 확인을 부탁드립니다.\n\n'\
                + '감사합니다\n\n'

        msg = MIMEText(content.encode('utf-8'), 'plain', 'utf-8')
        msg['Subject'] = Header('[화질구지] 작업완료 확인 메일', 'utf-8')
        msg['From'] = smtp_email
        msg['To'] = to
        try: 
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                smtp.login(smtp_email, smtp_pw)
                smtp.sendmail(smtp_email, [to], msg.as_string())
        except smtplib.SMTPExcption as e:
            logger.error(e)

    def run_module(self):
        """어댑터에 연결된 SR 모듈을 실행함
        """
        if self.srm_scale2 is None or self.srm_scale4 is None:
            logger.error("SR Module doesn't exist")
            return
        self._run_mq()


def main():
    # FIXME: Test 코드
    # srm_scale2 = Infmodule_proSR(model_path=PROJECT_DIR+"videoSR-inference/model/proSR/proSR_x2.pth", is_CUDA=True)
    # srm_scale4 = Infmodule_proSR(model_path=PROJECT_DIR+"videoSR-inference/model/proSR/proSR_x4.pth", is_CUDA=True)
    adapter = SRDefaultWebAdapter("Dummy_srm", "Dummy_srm")
    logger.info("SR Module on")
    adapter.run_module()

if __name__ == "__main__":
    main()
