# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from lxml.etree import tostring
import requests
from lxml import html
import re

# This WILL be reported to Stackdriver Error Reporting
from flask import abort
import yaml
import json

# [START functions_helloworld_http]
# [START functions_http_content]
from flask import escape

# [END functions_helloworld_http]
# [END functions_http_content]

import logging

import http.client as http_client

http_client.HTTPConnection.debuglevel = 2
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


# Salutelazio portal request parameter got via curl
RICERCA_MEDICI_Q = {
    "p_l_id": ["16262"],
    "p_p_lifecycle": ["0"],
    "p_t_lifecycle": ["0"],
    "p_p_state": ["normal"],
    "p_p_mode": ["view"],
    "p_p_col_id": ["column-1"],
    "p_p_col_pos": ["2"],
    "p_p_col_count": ["4"],
    "p_p_isolated": ["1"],
    "currentURL": ["/ricerca-medici"],
    "portletAjaxable": ["1"],
}


def problem(status=500, title="Interal Server Error", type="about:blank", detail=None, **kwargs):
    abort(status, json.dumps(dict(
        status=status,
        title=title,
        type=type,
        detail=detail,
        **kwargs
    )))

def _parse_generic(d):
    logging.warning("Parsing doctors: %r", d)
    # remove enclosing braces and trailing ","
    d = d.strip("{},")

    # get all fields
    fields = re.findall("([a-zA-Z]+)=", d)

    # create a regexp matching all fields
    # beware that this is a dynamic regexp which
    # is not suitable for production!
    re_fields = "|".join(fields)
    re_parse = f"(, )?({re_fields})="

    # Strip the first two items
    d_list = re.split(re_parse, d)[2:]
    data = [x for x in d_list if x != ", "]
    return dict(data[i : i + 2] for i in range(0, len(data) - 2, 2))


def _validate_parameters(request, mandatory_or, available=None):
    available = available or []
    available += mandatory_or

    if not any(x in mandatory_or for x in request.args):
        msg = f"At least one of the following parameter is required: {mandatory_or}"
        logging.error(RuntimeError(msg))
        problem(status=400, title=msg, args=request.path)

    for x in request.args:
        if x not in available:
            msg = f"Parameter not supported: {x}"
            logging.error(RuntimeError(msg))
            problem(status=400, title=msg, args=request.path)
        if not request.args[x].isalnum() or not request.args[x].isascii():
            msg = f"Only alphanumeric ascii characters are allowed for: {x}"
            logging.error(RuntimeError(msg))
            problem(status=400, title=msg, args=request.path)


# [START functions_orari_get]
def orari_get(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    request_args = request.args

    _validate_parameters(request, ["taxCode"])

    taxCode = request_args["taxCode"]

    # set operation id
    q = dict(
        RICERCA_MEDICI_Q,
        p_p_id=["genericlist_WAR_laitumsportlet_INSTANCE_zCFf5bBop3s7"],
    )
    q.update(
        {"_genericlist_WAR_laitumsportlet_INSTANCE_zCFf5bBop3s7_taxCode": [taxCode]}
    )

    res_salutelazio = requests.get(
        "https://www.salutelazio.it/ricerca-medici", params=q
    )
    e = html.fromstring(res_salutelazio.content)

    accept = request.headers.get('accept')
    if accept == "text/plain":
        ps = e.findall(".//p")
        for p in ps:
            print(p.text)
        tabs = e.findall(".//table")
        ret = ""
        for t in tabs:
            text = tostring(t)
            if b"Orari" not in text:
                continue
            ret += text
    else:
        input_field = e.findall(
            './/input[@name="_genericlist_WAR_laitumsportlet_INSTANCE_zCFf5bBop3s7_ambulatoriesSearchContainerPrimaryKeys"]'
        )
        if not input_field:
            abort(404, {"title": "Not found"})
        ambulatories = re.findall("{.*?},?", input_field[0].value)
        ret = {}
        ret["ambulatories"] = [_parse_generic(x) for x in ambulatories]
        ret = yaml.dump(ret)

    return ret
# [END functions_orari_get]


# [START functions_medici_get]
def medici_get(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    request_args = request.args

    _validate_parameters(
        request, ["surname", "zip"], ["asl", "name", "zip", "type", "delta"]
    )

    q = dict(
        RICERCA_MEDICI_Q,
        p_p_id=["genericlist_WAR_laitumsportlet_INSTANCE_gIo787T487Lc"],
    )

    q = dict(
        q,
        **{
            f"_genericlist_WAR_laitumsportlet_INSTANCE_gIo787T487Lc_{p}": request_args[
                p
            ]
            for p in request_args
        },
    )

    res_salutelazio = requests.get(
        "https://www.salutelazio.it/ricerca-medici", params=q
    )
    e = html.fromstring(res_salutelazio.content)

    # HTML response contains the following field with a json-like response.
    input_field = e.findall(
        './/input[@name="_genericlist_WAR_laitumsportlet_INSTANCE_gIo787T487Lc_doctorsSearchContainerPrimaryKeys"]'
    )
    if not input_field:
        problem(status=500, title="Internal Server Error", detail="Target html tag not found. Should at least be empty.", args=request.path)

    doctors = re.findall("{.*?},?", input_field[0].value)
    print(doctors)
    ret = {}
    ret["doctors"] = [_parse_generic(d) for d in doctors]
    ret = yaml.dump(ret)

    return ret
# [END functions_medici_get]


def salutelazio_get(request):
    medico = [x for x in request.path.strip("/ ").split("/") if x]

    if not medico:
        return medici_get(request)

    if len(medico) == 1:
        problem(status=404, title="Not Found", detail="Not Implemented", args=request.path)

    if len(medico) == 2 and medico[1] == 'orari':
        request.args = {"taxCode": medico[0]}
        return orari_get(request)

    return {
        '/salutelazio': 'Search a doctor. Valid keys: taxCode, surname, zip.',
        '/salutelazio/{taxCode}': 'Not implemented.',
        '/salutelazio/{taxCode}/orari': 'Info for a doctor office hours.'
    }

