# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
import httplib
import traceback
import urllib
import urlparse

import requests

import turbolift.utils.basic_utils as basic
import turbolift.utils.report_utils as report

from turbolift import ARGS
from turbolift.logger import logger


LOG = logger.getLogger('turbolift')


# Enable Debug Mode if its set
if ARGS is not None and ARGS.get('debug'):
    httplib.HTTPConnection.debuglevel = 1


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


def parse_url(url, auth=False):
    """Return a clean URL. Remove the prefix for the Auth URL if Found.

    :param url:
    :return aurl:
    """

    if ARGS.get('auth_version') != 'v1.0':
        if all([auth is True, 'tokens' not in url]):
            url = urlparse.urljoin(url, 'tokens')
    else:
        if all([auth is True, 'v1.0' not in url]):
            url = urlparse.urljoin(url, 'v1.0')

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

    if container is not None and '/' in container:
        raise SystemExit(
            report.reporter(
                msg='Containers may not have a "/" in them.',
                lvl='error'
            )
        )

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


def post_request(url, headers, body=None, rpath=None):
    """Perform HTTP(s) POST request based on Provided Params.

    :param url:
    :param rpath:
    :param headers:
    :param body:
    :return resp:
    """

    try:
        if rpath is not None:
            _url = urlparse.urljoin(urlparse.urlunparse(url), rpath)
        else:
            _url = urlparse.urlunparse(url)

        kwargs = {'timeout': ARGS.get('timeout', 60)}
        resp = requests.post(_url, data=body, headers=headers, **kwargs)
    except Exception as exp:
        LOG.error('Not able to perform Request ERROR: %s', exp)
        raise AttributeError("Failure to perform Authentication %s ERROR:\n%s"
                             % (exp, traceback.format_exc()))
    else:
        return resp


def head_request(url, headers, rpath):
    try:
        _url = urlparse.urljoin(urlparse.urlunparse(url), rpath)

        kwargs = {'timeout': ARGS.get('timeout')}
        resp = requests.head(_url, headers=headers, **kwargs)
        report.reporter(
            msg='INFO: %s %s %s' % (resp.status_code,
                                    resp.reason,
                                    resp.request),
            prt=False
        )
    except Exception as exp:
        report.reporter(
            'Not able to perform Request ERROR: %s' % exp,
            lvl='error',
            log=True
        )
    else:
        return resp


def put_request(url, headers, rpath, body=None):
    try:
        _url = urlparse.urljoin(urlparse.urlunparse(url), rpath)

        kwargs = {'timeout': ARGS.get('timeout')}
        resp = requests.put(_url, data=body, headers=headers, **kwargs)
        report.reporter(
            msg='INFO: %s %s %s' % (resp.status_code,
                                    resp.reason,
                                    resp.request),
            prt=False
        )
    except Exception as exp:
        LOG.error('Not able to perform Request ERROR: %s', exp)
    else:
        return resp


def delete_request(url, headers, rpath):
    try:
        _url = urlparse.urljoin(urlparse.urlunparse(url), rpath)

        kwargs = {'timeout': ARGS.get('timeout')}
        resp = requests.delete(_url, headers=headers, **kwargs)
        report.reporter(
            msg='INFO: %s %s %s' % (resp.status_code,
                                    resp.reason,
                                    resp.request),
            prt=False
        )
    except Exception as exp:
        LOG.error('Not able to perform Request ERROR: %s', exp)
    else:
        return resp


def get_request(url, headers, rpath, stream=False):
    try:
        _url = urlparse.urljoin(urlparse.urlunparse(url), rpath)

        kwargs = {'timeout': ARGS.get('timeout')}
        resp = requests.get(_url, headers=headers, stream=stream, **kwargs)
        report.reporter(
            msg='INFO: %s %s %s' % (resp.status_code,
                                    resp.reason,
                                    resp.request),
            prt=False
        )
    except Exception as exp:
        LOG.error('Not able to perform Request ERROR: %s', exp)
    else:
        return resp
