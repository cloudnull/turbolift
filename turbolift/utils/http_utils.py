# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import errno
import httplib
import socket
import traceback
import urllib
import urlparse

import turbolift.utils.basic_utils as basic
import turbolift.utils.report_utils as report

from turbolift import ARGS


def set_headers(headers):
    """Set the headers used in the Cloud Files Request.

    :return headers:
    """

    # Set the headers if some custom ones were specified
    if ARGS.get('base_headers'):
        headers.update(ARGS.get('base_headers'))

    return headers


def container_headers(headers):
    """Return updated Container Headers."""

    return headers.update(ARGS.get('container_headers'))


def response_get(conn, retry, resp_only=False):
    """Get the response information and return it.

    :param conn:
    :param retry:
    :param ret_read:
    :param mcr:
    """

    try:
        # Get response
        resp = conn.getresponse()
    except socket.error as exp:
        report.reporter(
            msg='Socket Error %s' % exp,
            lvl='error',
            prt=True
        )
        retry()
    except httplib.BadStatusLine as exp:
        report.reporter(
            msg='BAD STATUS-LINE ON METHOD MESSAGE %s' % exp,
            lvl='error',
            prt=True
        )
        retry()
    except httplib.ResponseNotReady as exp:
        report.reporter(
            msg='RESPONSE NOT READY MESSAGE %s' % exp,
            lvl='error',
            prt=True
        )
        retry()
    except Exception as exp:
        report.reporter(
            msg=('Failure, System will retry. DATA: %s %s %s\nTB:%s'
                 % (exp, conn, retry, traceback.format_exc())),
            lvl='error',
            prt=True
        )
        retry()
    else:
        if resp_only is True:
            return resp
        else:
            return resp, resp.read()


def open_connection(url):
    """Open an Http Connection and return the connection object.

    :param url:
    :return conn:
    """

    try:
        if url.scheme == 'https':
            conn = httplib.HTTPSConnection(url.netloc)
        else:
            conn = httplib.HTTPConnection(url.netloc)
    except httplib.InvalidURL as exc:
        msg = 'ERROR: Making connection to %s\nREASON:\t %s' % (url, exc)
        raise httplib.CannotSendRequest(msg)
    else:
        if ARGS.get('debug'):
            conn.set_debuglevel(1)
        return conn


def parse_url(url, auth=False):
    """Return a clean URL. Remove the prefix for the Auth URL if Found.

    :param url:
    :return aurl:
    """

    if all([auth is True, 'tokens' not in url]):
            url = urlparse.urljoin(url, 'tokens')

    if url.startswith(('http', 'https', '//')):
        if url.startswith('//'):
            return urlparse.urlparse(url, scheme='http')
        else:
            return urlparse.urlparse(url)
    else:
        return urlparse.urlparse('http://%s' % url)


def prep_payload(auth, container, source, args):
    """Create payload dictionary.

    :param auth:
    :param container:
    :param source:
    :return (dict, dict): payload and headers
    """

    # Unpack the values from Authentication
    token, tenant, user, inet, enet, cnet, aurl, acfep = auth

    # Get the headers ready
    headers = set_headers({'X-Auth-Token': token})

    if args.get('internal'):
        url = inet
    else:
        url = enet

    # Set the upload Payload
    return {'c_name': container,
            'source': source,
            'tenant': tenant,
            'headers': headers,
            'user': user,
            'cnet': cnet,
            'aurl': aurl,
            'url': url,
            'acfep': acfep}


def quoter(url, cont=None, ufile=None):
    """Return a Quoted URL.

    :param url:
    :param cont:
    :param ufile:
    :return:
    """

    url = basic.ustr(obj=url)
    if cont is not None:
        cont = basic.ustr(obj=cont)
    if ufile is not None:
        ufile = basic.ustr(obj=ufile)

    if ufile is not None and cont is not None:
        return urllib.quote(
            '%s/%s/%s' % (url, cont, ufile)
        )
    elif cont is not None:
        return urllib.quote(
            '%s/%s' % (url, cont)
        )
    else:
        return urllib.quote(
            '%s' % url
        )


def cdn_toggle(headers):
    """Set headers to Enable or Disable the CDN."""

    enable_or_disable = ARGS.get('enabled', ARGS.get('disable', False))
    return headers.update({'X-CDN-Enabled': enable_or_disable,
                           'X-TTL': ARGS.get('cdn_ttl'),
                           'X-Log-Retention': ARGS.get('cdn_logs')})
