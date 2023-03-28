
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.python import log

from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate

import txamqp.spec

import pickle
import logging
import logging.config, traceback

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('billing')


class CDRPRocess(object):
    def __init__(self):
        pass


    def process_req(self, msg):
        props = msg.content.properties
        pdu = pickle.loads(msg.content.body)

        msg_id = props['message-id']
        msg_status = 'PENDING'

        #logger.info('msg content: %s' % msg.content)
        smpp_conn = msg.routing_key[10:]
        source_addr = pdu.params['source_addr']
        destination_addr = pdu.params['destination_addr']
        content = pdu.params['short_message']

        logger.info('submit_sm: msg_id:%s from:%s to:%s content:%s smpp:%s' % (msg_id, source_addr, destination_addr, content, smpp_conn))

    def process_resp(self, msg):
        props = msg.content.properties
        pdu = pickle.loads(msg.content.body)
        #logger.info('msg content: %s' % msg.content)
        msg_id = props['message-id']
        remote_msg_id = pdu.params['message_id']
        # logger.info('pdu msg_id:%s' % remote_msg_id)
        msg_status = 'PENDING'

        pdt_status_str = '%s' % pdu.status
        pdu_status = pdt_status_str.split('.')[1]

        if pdu_status[:5] == 'ESME_':
            if pdu_status == 'ESME_ROK':
                msg_status = 'ACCEPTD'
            else:
                msg_status = 'UNDELIV'
        else:
            logger.error('do not support status:%s' % pdu_status)

        logger.info('submit_sm_resp: msg_id: %s remote_msg_id:%s status:%s, ' % (msg_id, remote_msg_id, msg_status))

    def process_deliver_sm(self, msg):
        #logger.info('receive deliver sm')
        remote_msg_id = msg.content.properties['message-id']
        #logger.info('content:%s' % msg.content)
        pdu_cid = msg.content.properties['headers']['cid']
        #pdu_dlr_id = msg.content.properties['headers']['dlr_id']
        #pdu_dlr_ddate = msg.content.properties['headers']['dlr_ddate']
        #pdu_dlr_sdate = msg.content.properties['headers']['dlr_sdate']
        #pdu_dlr_sub = msg.content.properties['headers']['dlr_sub']
        pdu_dlr_err = msg.content.properties['headers']['dlr_err']
        #pdu_dlr_text = msg.content.properties['headers']['dlr_text']
        #pdu_dlr_dlvrd = msg.content.properties['headers']['dlr_dlvrd']
        pdu_dlr_status = msg.content.body

        if isinstance(pdu_dlr_status, bytes):
            pdu_dlr_status = pdu_dlr_status.decode()

        logger.info('deliver_sm remote_msg_id:%s status:%s error:%s smpp:%s' % (remote_msg_id, pdu_dlr_status, pdu_dlr_err, pdu_cid))




    @inlineCallbacks
    def gotConnection(self, conn, username, password):
        print("Connected to broker.")
        yield conn.authenticate(username, password)

        print("Authenticated. Ready to receive messages")
        chan = yield conn.channel(1)
        yield chan.channel_open()

        QUEUE_NAME = 'cdr_service'
        CONSUMER_TAG = 'cdr'

        yield chan.queue_declare(queue=QUEUE_NAME)

        # Bind to submit.sm.* and submit.sm.resp.* routes
        yield chan.queue_bind(queue=QUEUE_NAME, exchange="messaging", routing_key='submit.sm.*')
        yield chan.queue_bind(queue=QUEUE_NAME, exchange="messaging", routing_key='submit.sm.resp.*')
        yield chan.queue_bind(queue=QUEUE_NAME, exchange="messaging", routing_key='dlr.deliver_sm')

        yield chan.basic_consume(queue=QUEUE_NAME, no_ack=True, consumer_tag=CONSUMER_TAG)
        queue = yield conn.queue(CONSUMER_TAG)

        # Wait for messages
        # This can be done through a callback ...
        cnt = 0
        while True:
            #logger.info('start get message #%s' % cnt)
            msg = yield queue.get()
            cnt = cnt+1
            #logger.info('key:' + msg.routing_key)
            if msg.routing_key[:15] == 'submit.sm.resp.':
                self.process_resp(msg)
            elif msg.routing_key[:10] == 'submit.sm.':
                self.process_req(msg)
            elif msg.routing_key == 'dlr.deliver_sm':
                self.process_deliver_sm(msg)
            else:
                logger.error('unknown route')

        # A clean way to tear down and stop
        yield chan.basic_cancel("someTag")
        yield chan.channel_close()
        chan0 = yield conn.channel(0)
        yield chan0.connection_close()

        reactor.stop()


if __name__ == "__main__":
    """
    This example will connect to RabbitMQ broker and consume from two route keys:
      - submit.sm.*: All messages sent through SMPP Connectors
      - submit.sm.resp.*: More relevant than SubmitSM because it contains the sending status

    Note:
      - Messages consumed from submit.sm.resp.* are not verbose enough, they contain only message-id and status
      - Message content can be obtained from submit.sm.*, the message-id will be the same when consuming from submit.sm.resp.*,
        it is used for mapping.
      - Billing information is contained in messages consumed from submit.sm.*
      - This is a proof of concept, saying anyone can consume from any topic in Jasmin's exchange hack a
        third party business, more information here: http://docs.jasminsms.com/en/latest/messaging/index.html
    """
    process = CDRPRocess()

    host = '45.61.136.49'
    port = 5672
    vhost = '/'
    username = 'admin1'
    password = 'password'
    spec_file = 'amqp0-9-1.xml'

    spec = txamqp.spec.load(spec_file)

    # Connect and authenticate
    d = ClientCreator(reactor,
    	AMQClient,
    	delegate=TwistedDelegate(),
    	vhost=vhost,
        spec=spec).connectTCP(host, port)
    d.addCallback(process.gotConnection, username, password)

    def whoops(err):
        if reactor.running:
            log.err(err)
            reactor.stop()

    d.addErrback(whoops)

    reactor.run()