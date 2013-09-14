# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================
from turbolift.clouderator import actions
from turbolift import methods
from turbolift import utils
from turbolift.worker import ARGS
from turbolift.worker import LOG


class list(object):
    """Setup and run the list Method."""

    def __init__(self, auth):
        self.auth = auth
        self.go = None
        self.action = None

    def start(self):
        """Return a list of objects from the API for a container."""

        def _list(payload, go, last_obj):
            """Retrieve a long list of all files in a container.

            :return final_list, list_count, last_obj:
            """

            if ARGS.get('all_containers') is None:
                return go.object_lister(url=payload['url'],
                                        container=payload['c_name'],
                                        last_obj=last_obj)
            else:
                return go.container_lister(url=payload['url'],
                                           last_obj=last_obj)

        # Package up the Payload
        payload = utils.prep_payload(auth=self.auth,
                                     container=ARGS.get('container'),
                                     source=None,
                                     args=ARGS)

        # Prep Actions.
        self.go = actions.cloud_actions(payload=payload)

        LOG.info('API Access for a list of Objects in %s', payload['c_name'])
        LOG.debug('PAYLOAD\t: "%s"', payload)

        last_obj = None
        with methods.spinner():
            objects, list_count, last_obj = _list(payload=payload,
                                                  go=self.go,
                                                  last_obj=last_obj)
            if ARGS.get('filter') is not None:
                objects = [obj for obj in objects
                           if ARGS.get('filter') in obj.get('name')]

            # Count the number of objects returned.
            obj_count = len(objects)
            if objects is False:
                utils.reporter(msg='Nothing found.')
            elif objects is not None:
                num_files = len(objects)
                if num_files < 1:
                    utils.reporter(msg='Nothing found.')
                else:
                    for obj in objects:
                        obj['bytes'] = int(obj.get('bytes') / 1024)
                        utils.reporter(
                            msg='SIZE: %(bytes)s KB\t- NAME: %(name)s' % obj
                        )
                    utils.reporter(msg='I found "%d" Item(s).' % obj_count)
            else:
                utils.reporter(msg='Nothing found.')
