import io
import json
import urlparse
from collections import defaultdict, Counter
from operator import methodcaller

import dateutil.parser
from backports import csv


class DBRow(object):
    def __init__(self, *args):
        # input comes from the CSV reader
        self.uuid, url, created_at, last_modified, data = args
        parsed_url = urlparse.urlparse(url)
        if parsed_url.query:
            # remove the ?searchId=1496354542.7818&page=3 query params from the URL
            self._url = parsed_url._replace(query='').geturl()
        else:
            self._url = parsed_url.geturl()

        self.created_at = dateutil.parser.parse(created_at)
        self.last_modified = dateutil.parser.parse(last_modified)
        if isinstance(data, dict):
            self.data = data
        else:
            self.data = json.loads(data, encoding='utf-8')

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value
        self.data['url'] = value

    def output(self):
        # fmt = u'{self.uuid}\t{self.url}\t{created_at}\t{last_modified}\t{data}'
        # return fmt.format(
        #     self=self,
        #     created_at=self.created_at.isoformat(),
        #     last_modified=self.last_modified.isoformat(),
        #     data=self.data
        # )
        return [self.uuid, self.url, self.created_at.isoformat(), self.last_modified.isoformat(),
                json.dumps(self.data, encoding='utf8')]


def read_csv(filename):
    with io.open(filename, newline='', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=u'\t', quoting=csv.QUOTE_MINIMAL):
            yield row


def write_csv(filename, rows):
    with io.open(filename, 'w', newline='', encoding='utf-8') as f:
        for row in rows:
            f.write(u'\t'.join(row))
            f.write(u'\n')
            # writer = csv.writer(f, delimiter=u'\t', quoting=csv.QUOTE_NONE, escapechar=u'|')
            # writer.writerows(rows)


def main(input_file):
    data = defaultdict(list)
    for row in read_csv(input_file):
        dbrow = DBRow(*row)
        data[dbrow.url].append(dbrow)

    rows = []
    mc = methodcaller('isoformat')
    for key, values in data.iteritems():
        dates = Counter(map(mc, [r.created_at for r in values]))
        if len(dates) > 1:
            date = dates.most_common(1)[0][0]
        else:
            date = dates.elements().next()
        src = values[0]
        row = DBRow(src.uuid, src.url, date, src.last_modified.isoformat(), src.data)
        row.url = src.url  # update urls in all places
        rows.append(row.output())

    write_csv('visir_fixed.csv', rows)


if __name__ == '__main__':
    main('visir.csv')
