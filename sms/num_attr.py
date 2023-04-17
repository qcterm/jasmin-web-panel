"tag carrier via number prefix"

import requests, json

hlr_lookup_url = "https://api.some-provider.com/hlr/lookup"
number = routable.pdu.params['destination_addr'].decode('utf-8')
data = json.dumps({'number': number})
#r = requests.post(hlr_lookup_url, data, auth=('user', '*****'))


# check carrier via phone number prefix

#CM
cm_prefix = ['130', '131', '132', '133', '134', '135', '136', '137', '138', '139', '140', '141', '142', '143',
              '144', '145', '146', '147', '148', '149', '150']
#CU
cu_prefix = ['151', '152', '153', '154', '155', '156', '157', '158', '159', '160', '161', '162', '163', '164',
               '165', '166', '167', '168', '169', '170']
#CT
ct_prefix = ['171', '172', '173', '174', '175', '176', '177', '178', '179', '180', '181', '182', '183', '184',
              '185', '186', '187', '188', '189', '190', '191', '192', '193', '194', '195', '196', '197', '198', ]

prefix = number[2:5]

if prefix in cm_prefix:
    routable.addTag('CARRIER-%s' % 'CM')
elif prefix in cu_prefix:
    routable.addTag('CARRIER-%s' % 'CU')
elif prefix in ct_prefix:
    routable.addTag('CARRIER-%s' % 'CT')
else:
    routable.addTag('CARRIER-%s' % 'NONE')