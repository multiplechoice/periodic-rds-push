import datetime
import os

import boto3
import dateutil.parser
import dateutil.tz

from make_table import ScrapedJob, session_scope

SQS_QUEUE = os.environ.get('SQS_QUEUE')
SQS_REGION = os.environ.get('SQS_REGION')
RDS_CREDENTIALS = os.environ.get('RDS_CREDENTIALS')


def reformat_sqs_message(message):
    job = {}
    for key, value in message.message_attributes.iteritems():
        job[key] = value['StringValue']
    return job


def main():
    with session_scope(RDS_CREDENTIALS) as session:
        sqs = boto3.resource('sqs', region_name=SQS_REGION)
        queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE)
        for _ in xrange(100):
            messages = queue.receive_messages(MaxNumberOfMessages=10, MessageAttributeNames=['All'])
            if messages:
                for message in messages:
                    # data = reformat_sqs_message(message)
                    # job = ScrapedJob(url=data['url'], created_at=dateutil.parser.parse(data['posted']), data=data)
                    job = ScrapedJob.from_dict(reformat_sqs_message(message))

                    query = session.query(ScrapedJob).filter(ScrapedJob.url == job.url)
                    matched_job = query.one_or_none()
                    if matched_job is None:
                        # it's a new job, since it hasn't been seen before
                        session.add(job)
                    else:
                        if job.created_at.tzinfo is None:
                            job.created_at = job.created_at.replace(tzinfo=dateutil.tz.tzutc())

                        if job.created_at < matched_job.created_at:
                            # new record has an older timestamp
                            matched_job.created_at = job.created_at
                            # modifying the existing record will cause it to be marked as dirty
                            # so when the session is committed it will emit an UPDATE for the row

                # completed message handling
                queue.delete_messages(Entries=[
                    {'Id': m.message_id, 'ReceiptHandle': m.receipt_handle} for m in messages])
