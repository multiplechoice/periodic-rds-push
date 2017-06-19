import json
import urlparse
from cStringIO import StringIO
from itertools import izip_longest
from uuid import uuid4

import boto3

region = 'eu-central-1'
queue_name = 'incoming-jobs'
bucket_name = 'lambda-multiplechoice-workplace'


def runner():
    queue = get_queue()
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix='scrapinghub/'):
        if 'Contents' in result:
            for item in result['Contents']:
                key = item['Key']
                if key == 'scrapinghub/':
                    continue

                file_like_object = StringIO()
                # download the key from s3
                print '->', key
                s3.download_fileobj(bucket_name, key, file_like_object)
                # read the lines, and parse them for sqs
                jobs = json.loads(file_like_object.getvalue())
                for batch in grouper(jobs, 10):
                    items = filter(lambda x: x is not None, batch)
                    items = map(translate_item_to_message, items)
                    queue.send_messages(Entries=items)

                print '<-', key
                s3.delete_object(Bucket=bucket_name, Key=key)


def guess_spider_from_url(url):
    parsed = urlparse.urlparse(url)
    if parsed.netloc == 'www.mbl.is':
        return 'mbl'
    elif parsed.netloc == 'www.tvinna.is':
        return 'tvinna'
    elif parsed.netloc == 'job.visir.is':
        return 'visir'
    else:
        raise RuntimeError('Unknown url %r' % url)


def translate_item_to_message(item):
    """
    Loop through the items as they are emitted from the Scrapy spider
    Args:
        item (dict): Scrapy item dict
    Returns:
        dict: reformatted item valid for use in the `send_messages`_ function.
        See also the AWS `documentation`_.
    .. _send_messages:
        https://boto3.readthedocs.io/en/latest/reference/services/sqs.html#SQS.Queue.send_messages
    .. _documentation:
        https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessageBatchRequestEntry.html
    """
    message = {'Id': str(uuid4()), 'MessageBody': 'ScrapyItem', 'MessageAttributes': {}}
    for key, value in item.iteritems():
        if value is None:
            continue
        if key == 'views':
            continue
        message['MessageAttributes'][key] = {'StringValue': value, 'DataType': 'String'}

    if 'spider' not in item:
        value = guess_spider_from_url(item['url'])
        message['MessageAttributes']['spider'] = {'StringValue': value, 'DataType': 'String'}

    if not message['MessageAttributes']:
        del message['MessageAttributes']

    return message


# https://docs.python.org/2/library/itertools.html#recipes
def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def get_queue():
    sqs = boto3.resource('sqs', region_name=region)
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue
