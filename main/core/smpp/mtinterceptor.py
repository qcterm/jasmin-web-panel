from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError

from collections import OrderedDict

from ..tools import set_ikeys, split_cols
from ..exceptions import (JasminSyntaxError, JasminError,
						UnknownError, MissingKeyError,
						MutipleValuesRequiredKeyError, ObjectNotFoundError)

import logging

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

logger = logging.getLogger(__name__)

class MTInterceptor(object):
    "MTInterceptor Class"
    lookup_field = 'order'

    def __init__(self, telnet):
        self.telnet = telnet

    def _list(self):
        "List MTInterceptor as python dict"
        self.telnet.sendline('mtinterceptor -l')
        self.telnet.expect([r'(.+)\n' + STANDARD_PROMPT])
        result = str(self.telnet.match.group(0)).strip().replace("\\r", '').split("\\n")
        if len(result) < 3:
            return {'mtinterceptors': []}
        results = [l.replace(', ', ',').replace('(!)', '')
            for l in result[2:-2] if l]
        mtinterceptors = split_cols(results)
        return {
            'mtinterceptors':
                [
                    {
                        'order': i[0].strip().lstrip('#'),
                        'type': i[1],
                        'script': i[2],
                        'filters': [c.strip() for c in ' '.join(i[3:]).split(',')
						            ] if len(i) > 3 else []
                    } for i in mtinterceptors
                ]
        }
    def list(self):
        "List Filters. No parameters"
        return self._list()

    def get_mtinterceptor(self, order):
        "Return data for one filter as Python dict"
        mtinterceptors = self._list()['mtinterceptors']
        try:
            return {'mtinterceptor':
                next((m for m in mtinterceptors if m['order'] == order), None)
            }
        except StopIteration:
            raise ObjectNotFoundError('No MTInterceptor with order: %s' % order)

    def retrieve(self, order):
        "Details for one mtinterceptor by order (integer)"
        return self.get_mtinterceptor(order)

    def create(self, data):
        """Create MTInterceptor.
        Required parameters: type, parameters
        ---
        # YAML
        omit_serializer: true
        parameters:
        - name: type
          description: One of TransparentFilter, ConnectorFilter, UserFilter, GroupFilter, SourceAddrFilter, DestinationAddrFilter, ShortMessageFilter, DateIntervalFilter, TimeIntervalFilter, TagFilter, EvalPyFilter
          required: true
          type: string
          paramType: form
        - name: fid
          description: Filter id, used to identify filter
          required: true
          type: string
          paramType: form
        - name: parameter
          description: Parameter
          required: false
          type: string
          paramType: form
        """
        try:
            ftype, order, script = data['type'], data['order'], data['parameter']
        except IndexError:
            raise MissingKeyError('Missing parameter: type or parameter required')
        ftype = ftype.lower()
        self.telnet.sendline('filter -a')
        self.telnet.expect(r'Adding a new Filter(.+)\n' + INTERACTIVE_PROMPT)
        ikeys = OrderedDict({'type': ftype, 'script': script})

        try:
            parameter = data['parameter']
        except MultiValueDictKeyError:
            raise MissingKeyError('%s filter requires parameter' % ftype)
        if ftype == 'defaultinterceptor':
            ikeys['script'] = parameter
        #print(ikeys)
        set_ikeys(self.telnet, ikeys)
        self.telnet.sendline('persist')
        self.telnet.expect(r'.*' + STANDARD_PROMPT)
        return {'mtinterceptor': self.get_mtinterceptor(order)}

    def simple_filter_action(self, action, order, return_filter=True):
        self.telnet.sendline('mtinterceptor -%s %s' % (action, order))
        matched_index = self.telnet.expect([
            r'.+Successfully(.+)' + STANDARD_PROMPT,
            r'.+Unknown Filter: (.+)' + STANDARD_PROMPT,
            r'.+(.*)' + STANDARD_PROMPT,
        ])
        if matched_index == 0:
            self.telnet.sendline('persist')
            if return_filter:
                self.telnet.expect(r'.*' + STANDARD_PROMPT)
                return {'mtinterceptor': self.get_mtinterceptor(order)}
            else:
                return {'order': order}
        elif matched_index == 1:
            raise UnknownError(detail='No mtinterceptor:' +  order)
        else:
            raise JasminError(self.telnet.match.group(1))

    def destroy(self, order):
        """Delete a filter. One parameter required, the filter identifier (a string)

        HTTP codes indicate result as follows

        - 200: successful deletion
        - 404: nonexistent filter
        - 400: other error
        """
        return self.simple_filter_action('r', order, return_filter=False)