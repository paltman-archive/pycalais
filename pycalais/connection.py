#!/usr/bin/python

# Copyright (c) 2008 Patrick Altman http://paltman.com/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from uuid import uuid4
import os
import urllib, httplib
from xml.dom.minidom import parseString

class EnvironmentVariableNotFoundError(Exception):
    pass
    
    
class CommunicationError(Exception):
    pass
    

class ContentTypes(object):
    TEXT = 'text/txt'
    HTML = 'text/html'
    XML = 'text/xml'
    
    
class CalaisConnection(object):
    server = 'api.opencalais.com'
    port = 80
    path = '/enlighten/calais.asmx/Enlighten'
    
    def __init__(self, api_key=None, user_identifier=None):
        if api_key:
            self.api_key = api_key
        else:
            if "CALAIS_API_KEY" not in os.environ:
                raise EnvironmentVariableNotFoundError(
                    "CALAIS_API_KEY environment variable not set!")
            
            self.api_key = os.environ["CALAIS_API_KEY"]
        
        if user_identifier:
            self.user_id = user_identifier
        else:
            self.user_id = str(uuid4())
            
    
    def enlighten(self, content, 
                        allow_search=False, 
                        allow_distribution=False,
                        content_type=ContentTypes.TEXT):
        
        external_id = str(uuid4())
        output_format = 'xml/rdf'
        submitter = self.user_id
        
        params_xml = """
        <c:params xmlns:c="http://s.opencalais.com/1/pred/" 
                  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <c:processingDirectives c:contentType="%(content_type)s" 
                                    c:outputFormat="%(output_format)s">
            </c:processingDirectives>
            <c:userDirectives c:allowDistribution="%(allow_distribution)s" 
                              c:allowSearch="%(allow_search)s" 
                              c:externalID="%(external_id)s" 
                              c:submitter="%(submitter)s">
            </c:userDirectives>
            <c:externalMetadata></c:externalMetadata>
        </c:params>
        """ % {'content_type':content_type, 
               'output_format':output_format, 
               'allow_search':allow_search, 
               'allow_distribution':allow_distribution, 
               'external_id':external_id, 
               'submitter':submitter}
        
        data = urllib.urlencode({
            'licenseID':self.api_key, 
            'content':content, 
            'paramsXML':params_xml
        })
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        conn = httplib.HTTPConnection("%s:%s" % (self.server, self.port))
        conn.request("POST", self.path, data, headers)
        response = conn.getresponse()
        
        if response.status != 200:
            status = response.status
            reason = response.reason
            conn.close()
            raise CommunicationError("%s %s" % (status, reason))
            
        rdf_raw = urllib.unquote_plus(response.read())
        conn.close()
        doc = parseString(rdf_raw)
        
        return parseString(doc.childNodes[0].childNodes[0].nodeValue)
        