# -*- coding: utf-8 -*-

from datetime import datetime
import requests
from lxml import etree, objectify


def get_current_mail_status(bar_code, login, password):
    url = u'http://tracking.russianpost.ru/rtm34?wsdl'
    headers = {
        u"Accept-Encoding": u"gzip,deflate",
        u"Content-Type": u"application/soap+xml;charset=UTF-8",
        u"User-Agent": u"Apache-HttpClient/4.1.1 (java 1.5)"
    }

    data = u"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:oper="http://russianpost.org/operationhistory" xmlns:data="http://russianpost.org/operationhistory/data" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                   <soap:Header/>
                   <soap:Body>
                      <oper:getOperationHistory>
                         <!--Optional:-->
                         <data:OperationHistoryRequest>
                            <data:Barcode>%s</data:Barcode>
                            <data:MessageType>0</data:MessageType>
                            <!--Optional:-->
                            <data:Language>RUS</data:Language>
                         </data:OperationHistoryRequest>
                         <!--Optional:-->
                         <data:AuthorizationHeader soapenv:mustUnderstand="1">
                            <data:login>%s</data:login>
                            <data:password>%s</data:password>
                         </data:AuthorizationHeader>
                      </oper:getOperationHistory>
                   </soap:Body>
                </soap:Envelope>""" % (bar_code, login, password)

    response = requests.post(url, data=data, headers=headers)
    if response.status_code != 200:
        return

    last_status = {}
    root = etree.fromstring(response.content)
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'):
            continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    objectify.deannotate(root, cleanup_namespaces=True)
    tags = root.xpath('//OperationHistoryData/historyRecord')
    for tag in tags:
        oper_type_id = None
        oper_type_descr = None
        date_val = None
        address_descr = None

        oper_tags = tag.xpath('./OperationParameters/OperType/Id')
        for otag in oper_tags:
            oper_type_id = otag.text
            break

        oper_tags = tag.xpath('./OperationParameters/OperType/Name')
        for otag in oper_tags:
            oper_type_descr = otag.text
            break

        operdate_tags = tag.xpath('./OperationParameters/OperDate')
        for otag in operdate_tags:
            date_val = datetime.strptime(otag.text[:19], "%Y-%m-%dT%H:%M:%S")
            break

        address_tags = tag.xpath('./AddressParameters/OperationAddress/Description')
        for atag in address_tags:
            address_descr = atag.text
            break

        if oper_type_id is not None and oper_type_descr is not None and date_val is not None and address_tags is not None:
            last_status = {
                'operation': oper_type_id,
                'op_name': oper_type_descr,
                'dt': date_val,
                'address': address_descr
            }

    return last_status or None
