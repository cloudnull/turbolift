# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

import os


__author__ = "Kevin Carter"
__contact__ = "Kevin Carter"
__email__ = "kevin@cloudnull.com"
__copyright__ = "2014 All Rights Reserved"
__license__ = "GPLv3+"
__date__ = "2014-03-15"
__version__ = "3.0.0"
__status__ = "Production"
__appname__ = "turbolift"
__description__ = 'OpenStack Swift - Rackspace CloudFiles - Management tool'
__url__ = 'https://github.com/cloudnull/turbolift.git'

__srv_types__ = [
    'object-store'
]

__cdn_types__ = [
    'rax:object-cdn',
    'CDN'
]

# The Version and Information for the application
VINFO = (
    'Turbolift %(version)s, developed by %(author)s, Licenced Under'
    ' %(license)s, FYI : %(copyright)s' % {
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'copyright': __copyright__
    }
)

ARGUMENTS = {
    'shared_args': {
        'container': {
            'commands': [
                '-c',
                '--container'
            ],
            'help': 'Container name to work with.',
            'metavar': '[NAME]',
            'required': True
        },
        'object': {
            'commands': [
                '-o',
                '--object'
            ],
            'help': 'Object name to work with. One or more object can be set'
                    ' at a time.',
            'nargs': '+',
            'metavar': 'NAME',
            'required': False
        },
        'objects_file': {
            'commands': [
                '-of',
                '--objects-file'
            ],
            'help': 'A file that contains the list of objects to interact'
                    ' with.',
            'metavar': 'NAME',
            'required': False
        },
        'object_headers': {
            'commands': [
                '-OH',
                '--object-headers'
            ],
            'nargs': '+',
            'metavar': 'KEY=VALUE',
            'help': 'These Headers only effect Objects.',
            'required': False,
            'default': None
        },
        'container_headers': {
            'commands': [
                '-CH',
                '--container-headers'
            ],
            'nargs': '+',
            'metavar': 'KEY=VALUE',
            'help': 'These headers only effect Containers.',
            'required': False,
            'default': None
        },
        'sync': {
            'commands': [
                '--sync'
            ],
            'help': 'Sync local and remote file objects.',
            'action': 'store_true',
            'default': False,
            'required': False
        },
        'directory': {
            'commands': [
                '-d',
                '--directory'
            ],
            'help': 'Name of a directory path that you want to Download.',
            'metavar': '[NAME]',
            'required': False
        },
        'pattern_match': {
            'commands': [
                '-m',
                '--pattern-match'
            ],
            'help': 'Filter files by pattern, This is a Regex Search.',
            'metavar': '[REGEX]'
        },
        'timeout': {
            'commands': [
                '--timeout'
            ],
            'help': 'API timeout. default: %(default)s',
            'default': None,
            'type': float,
            'metavar': '[FLOAT]'
        },
        'time_offset': {
            'commands': [
                '--time-offset'
            ],
            'help': 'Filter objects where the last modified time is older'
                    ' than [OFFSET]. Default: %(default)s',
            'default': 'hours',
            'choices': ['weeks', 'days', 'hours'],
            'metavar': '{weeks,days,hours}',
        },
        'time_factor': {
            'commands': [
                '--time-factor'
            ],
            'help': 'If Offset is used this will modify the offset value.'
                    ' The default: %(default)s.',
            'default': 1.0,
            'metavar': '[FLOAT]'
        },
        'max_jobs': {
            'commands': [
                '--max-jobs'
            ],
            'metavar': '[INT]',
            'default': 25000,
            'type': int,
            'help': 'Max number of jobs to process on a single pass.'
        }
    },
    'optional_args': {
        'mutually_exclusive': {
            'user': {
                'text': 'Authentication: Users name',
                'required': True,
                'group': [
                    'user'
                ]
            },
            'credentials': {
                'text': 'Authentication: Credential type',
                'required': True,
                'group': [
                    'apikey',
                    'password',
                    'token'
                ]
            },
            'auth_url': {
                'text': 'Authentication: URL or plugin type',
                'required': True,
                'group': [
                    'auth_url'
                ]
            }
        },
        'groups': {
            'headers': {
                'text': 'Header Options',
                'group': [
                    'base_headers'
                ]
            },
            'logging': {
                'text': 'Logging Options',
                'group': [
                    'log_location',
                    'log_file',
                    'colorized'
                ]
            }
        },
        'apikey': {
            'commands': [
                '-a',
                '--os-apikey'
            ],
            'help': 'Defaults to env[OS_API_KEY]',
            'default': os.environ.get('OS_API_KEY', None),
            'metavar': '[API_KEY]'
        },
        'password': {
            'commands': [
                '-p',
                '--os-password'
            ],
            'help': 'Defaults to env[OS_PASSWORD]',
            'default': os.environ.get('OS_PASSWORD', None),
            'metavar': '[PASSWORD]'
        },
        'user': {
            'commands': [
                '-u',
                '--os-user'
            ],
            'help': 'Defaults to env[OS_USERNAME]',
            'default': os.environ.get('OS_USERNAME', None),
            'metavar': '[USERNAME]'
        },
        'tenant': {
            'commands': [
                '--os-tenant'
            ],
            'help': 'Defaults to env[OS_TENANT_NAME]',
            'default': os.environ.get('OS_TENANT_NAME', None),
            'metavar': '[TENANT]'
        },
        'token': {
            'commands': [
                '--os-token'
            ],
            'help': 'Defaults to env[OS_TOKEN]',
            'default': os.environ.get('OS_TOKEN', None),
            'metavar': '[TOKEN]'
        },
        'region': {
            'commands': [
                '-r',
                '--os-region'
            ],
            'help': 'Defaults to env[OS_REGION_NAME]',
            'default': os.environ.get('OS_REGION_NAME', None),
            'metavar': '[REGION]'
        },
        'auth_url': {
            'commands': [
                '--os-auth-url'
            ],
            'help': 'Defaults to env[OS_AUTH_URL]',
            'default': os.environ.get('OS_AUTH_URL', None),
            'metavar': '[AUTH_URL]'
        },
        'auth_version': {
            'commands': [
                '--os-auth-version'
            ],
            'help': 'Defaults to env[OS_AUTH_VERSION]',
            'default': os.environ.get('OS_AUTH_VERSION', 'v2.0'),
            'metavar': '[VERSION]'
        },
        'version': {
            'commands': [
                '--version'
            ],
            'action': 'version',
            'version': __version__
        },
        'log_location': {
            'commands': [
                '--log-location'
            ],
            'metavar': '[PATH]',
            'default': os.getenv('TURBO_LOGS', os.getenv('HOME')),
            'help': 'Change the log location, Default is Home. Default:'
                    ' %(default)s.'
        },
        'log_file': {
            'commands': [
                '--log-file'
            ],
            'metavar': '[NAME]',
            'default': os.getenv('TURBO_LOGFILE', 'turbolift.log'),
            'help': 'Change the log file Log File is %(default)s.'
        },
        'colorized': {
            'commands': [
                '--colorized'
            ],
            'help': 'Colored output, effects logs and STDOUT.',
            'default': False,
            'action': 'store_true'
        },
        'debug': {
            'commands': [
                '--debug'
            ],
            'help': 'Turn up verbosity to over 9000',
            'default': False,
            'action': 'store_true'
        },
        'quiet': {
            'commands': [
                '--quiet'
            ],
            'help': 'Make %(prog)s Shut the hell up',
            'default': False,
            'action': 'store_true'
        },
        'base_headers': {
            'commands': [
                '-BH',
                '--base-headers'
            ],
            'nargs': '+',
            'metavar': 'KEY=VALUE',
            'help': 'These are the basic headers used for all Turbolift'
                    ' operations. Anything added here will modify ALL'
                    ' Turbolift Operations which leverage the API.',
            'required': False,
            'default': None
        },
        'endpoint_type': {
            'commands': [
                '-e',
                '--os-endpoint-type'
            ],
            'help': 'Set the service endpoint type.',
            'default': os.getenv('OS_ENDPOINT_TYPE', 'publicURL'),
            'required': False
        },
        'cdn_endpoint_type': {
            'commands': [
                '--cdn-endpoint-type'
            ],
            'help': 'Set the service endpoint type for a CDN network.',
            'default': os.getenv('OS_CDN_ENDPOINT_TYPE', 'publicURL'),
            'required': False
        },
        'concurrency': {
            'commands': [
                '-cc',
                '--concurrency'
            ],
            'metavar': '[INT]',
            'type': int,
            'default': os.getenv('TURBO_CONCURRENCY', 50),
            'help': 'This sets the operational concurrency.'
        }
    },
    'subparsed_args': {
        'delete': {
            'help': 'Delete objects or entire containers.',
            'shared_args': [
                'object',
                'objects_file',
                'container',
                'pattern_match',
                'max_jobs'
            ],
            'optional_args': {
                'save_container': {
                    'commands': [
                        '--save-container'
                    ],
                    'help': 'This will allow the container to remain untouched'
                            ' and intact, but only the container.',
                    'default': False,
                    'action': 'store_true'
                }
            }
        },
        'archive': {
            'help': 'Compress files or directories into a single archive',
            'shared_args': [
                'directory',
                'container'
            ],
            'optional_args': {
                'tar_name': {
                    'commands': [
                        '--tar-name'
                    ],
                    'metavar': '[NAME]',
                    'help': 'Name of tarball archive'
                },
                'no_cleanup': {
                    'commands': [
                        '--no-cleanup'
                    ],
                    'action': 'store_true',
                    'help': 'Used to keep the compressed Archive. The archive'
                            ' will be left in the Users Home Folder. Default:'
                            ' %(default)s',
                    'default': False
                },
                'verify': {
                    'commands': [
                        '--verify'
                    ],
                    'action': 'store_true',
                    'help': 'If set this will open a created archive and'
                            ' verify its contents. Used when needing to know'
                            ' without a doubt that all the files that were'
                            ' specified were compressed into the single'
                            ' archive.'
                }
            }
        },
        'clone': {
            'help': 'Clone Objects from one container to another.',
            'shared_args': [
                'timeout',
                'time_offset',
                'time_factor'
            ],
            'optional_args': {
                'source_container': {
                    'commands': [
                        '-sc',
                        '--source-container'
                    ],
                    'metavar': '[CONTAINER]',
                    'help': 'Source Container.',
                    'required': True,
                    'default': None
                },
                'target_container': {
                    'commands': [
                        '-tc',
                        '--target-container'
                    ],
                    'metavar': '[CONTAINER]',
                    'help': 'Target Container.',
                    'required': True,
                    'default': None
                },
                'target_region': {
                    'commands': [
                        '-tr',
                        '--target-region'
                    ],
                    'metavar': '[CONTAINER]',
                    'help': 'Target Region.',
                    'required': True,
                    'default': None
                },
                'target_snet': {
                    'commands': [
                        '--target-snet'
                    ],
                    'action': 'store_true',
                    'help': 'Use Service Net to Stream the Objects. Default:'
                            ' %(default)s',
                    'default': False
                },
                'clone_headers': {
                    'commands': [
                        '--clone-headers'
                    ],
                    'action': 'store_true',
                    'help': 'Query the source object for headers and restore'
                            ' them on the target. Default: %(default)s',
                    'default': False
                },
                'save_newer': {
                    'commands': [
                        '--save-newer'
                    ],
                    'action': 'store_true',
                    'help': 'Check to see if the target "last_modified" time'
                            ' is newer than the source. If "True" upload is'
                            ' skipped.',
                    'default': False
                },
                'add_only': {
                    'commands': [
                        '--add-only'
                    ],
                    'action': 'store_true',
                    'help': 'Clone the object only if it doesn\'t already'
                            ' exist in the target container.',
                    'default': False
                }
            }
        },
        'show': {
            'help': 'List Objects in a container.',
            'shared_args': [
                'object',
                'container'
            ],
            'optional_args': {
                'save_newer': {
                    'commands': [
                        '--cdn-info'
                    ],
                    'action': 'store_true',
                    'help': 'Show Info on the Container for CDN. Default:'
                            ' %(default)s',
                    'default': False
                }
            }
        },
        'list': {
            'help': 'List Objects in a container.',
            'shared_args': [
                'pattern_match',
                'container',
                'max_jobs'
            ],
            'optional_args': {
                'mutually_exclusive': {
                    'list_groups': {
                        'text': 'List operations',
                        'required': True,
                        'group': [
                            'container',
                            'all_containers',
                            'cdn_containers'
                        ]
                    }
                },
                'filter_dlo': {
                    'commands': [
                        '--filter-dlo'
                    ],
                    'action': 'store_true',
                    'help': 'Filter all Dynamic Large Objects that were'
                            ' created by turbolift.',
                    'default': False
                },
                'filter': {
                    'commands': [
                        '--filter'
                    ],
                    'help': 'String filter on all returned objects names.',
                    'default': None,
                    'metavar': '[STRING]'
                },
                'all_containers': {
                    'commands': [
                        '--all-containers'
                    ],
                    'action': 'store_true',
                    'help': 'List all containers.',
                    'default': False
                },
                'cdn_containers': {
                    'commands': [
                        '--cdn-containers'
                    ],
                    'action': 'store_true',
                    'help': 'List all CDN enabled containers.',
                    'default': False
                },
                'fields': {
                    'commands': [
                        '--fields'
                    ],
                    'help': 'Set the return fields on an object list. Default:'
                            ' %(default)s',
                    'nargs': '+',
                    'metavar': '[NAME]'
                },
                'sort_by': {
                    'commands': [
                        '--sort-by'
                    ],
                    'help': 'Set the returned field to sort the returned'
                            ' output.',
                    'default': None,
                    'metavar': '[NAME]'
                }
            }
        },
        'update': {
            'help': 'List Objects in a container.',
            'shared_args': [
                'container',
                'object',
                'container_headers',
                'object_headers'
            ],
            'optional_args': {
                'mutually_exclusive': {
                    'header_options': {
                        'text': 'Header Options',
                        'required': False,
                        'group': [
                            'object_headers',
                            'container_headers'
                        ]
                    }
                }
            }
        },
        'cdn': {
            'help': 'List Objects in a container.',
            'shared_args': [
                'container',
                'object'
            ],
            'optional_args': {
                'mutually_exclusive': {
                    'cdn_enabled': {
                        'text': 'Enable or Disable the CDN',
                        'required': False,
                        'group': [
                            'cdn_enabled',
                            'cdn_disabled'
                        ]
                    },
                    'cdn_log_enabled': {
                        'text': 'Enable or Disable the CDN logging',
                        'required': False,
                        'group': [
                            'cdn_logs_enabled',
                            'cdn_logs_disabled'
                        ]
                    }
                },
                'groups': {
                    'cdn': {
                        'text': 'CDN Options',
                        'group': [
                            'cdn_ttl'
                        ]
                    }
                },
                'purge': {
                    'commands': [
                        '--purge'
                    ],
                    'help': 'Purge a specific Object from the CDN, This can be'
                            ' used multiple times.',
                    'nargs': '+',
                    'metavar': 'NAME',
                    'required': False
                },
                'cdn_enabled': {
                    'commands': [
                        '--cdn-enabled'
                    ],
                    'help': 'Enable the CDN for a Container',
                    'default': False,
                    'action': 'store_true'
                },
                'cdn_disabled': {
                    'commands': [
                        '--cdn-disabled'
                    ],
                    'help': 'Disable the CDN for a Container',
                    'default': False,
                    'action': 'store_true'
                },
                'cdn_ttl': {
                    'commands': [
                        '--cdn-ttl'
                    ],
                    'help': 'Set the TTL on a CDN Enabled Container. Default:'
                            ' %(default)s',
                    'default': 259200,
                    'type': int,
                    'metavar': '[TTL]'
                },
                'cdn_logs_enabled': {
                    'commands': [
                        '--cdn-logs-enabled'
                    ],
                    'help': 'Enable CDN logging.',
                    'default': False,
                    'action': 'store_true'
                },
                'cdn_logs_disabled': {
                    'commands': [
                        '--cdn-logs-disabled'
                    ],
                    'help': 'Disabled CDN logging.',
                    'default': False,
                    'action': 'store_true'
                }
            }
        },
        'download': {
            'help': 'Downloads everything from a given container creating a'
                    ' target Directory if it does not exist.',
            'shared_args': [
                'timeout',
                'time_offset',
                'time_factor',
                'pattern_match',
                'container',
                'object',
                'directory',
                'sync',
                'max_jobs'
            ],
            'optional_args': {
                'groups': {
                    'list_groups': {
                        'text': 'Download arguments',
                        'required': True,
                        'group': [
                            'container',
                            'object'
                        ]
                    }
                },
                'restore_perms': {
                    'commands': [
                        '--restore-perms'
                    ],
                    'help': 'If The object has permissions saved as metadata'
                            ' restore those permissions on the local object',
                    'default': False,
                    'action': 'store_true'
                }
            }
        },
        'upload': {
            'help': 'Upload files objects to SWIFT.',
            'shared_args': [
                'pattern_match',
                'container',
                'directory',
                'object',
                'sync',
                'max_jobs',
                'object_headers'
            ],
            'optional_args': {
                'groups': {
                    'upload': {
                        'text': 'Local File Options',
                        'group': [
                            'directory',
                            'object',
                            'restore_perms',
                            'exclude'
                        ]
                    },
                    'dlo': {
                        'text': 'Dynamic Large Object Options',
                        'group': [
                            'chunk_size',
                            'large_object_size'
                        ]
                    }
                },
                'chunk_size': {
                    'commands': [
                        '--chunk-size'
                    ],
                    'help': 'Set the default byte size a object that is larger'
                            ' then "[--large-object-size]" will be chunked'
                            ' this size. Default: %(default)s',
                    'default': 524288000,
                    'type': int,
                    'metavar': '[INT]'
                },
                'large_object_size': {
                    'commands': [
                        '--large-object-size'
                    ],
                    'help': 'Set the default byte size of the large object'
                            ' threshold that is larger then 5GB will be'
                            ' chunked at. Default: %(default)s',
                    'default': 5153960756,
                    'type': int,
                    'metavar': '[INT]'
                },
                'exclude': {
                    'commands': [
                        '--exclude'
                    ],
                    'nargs': '+',
                    'help': 'Exclude a pattern when uploading',
                    'default': list()
                },
                'delete_remote': {
                    'commands': [
                        '--delete-remote'
                    ],
                    'help': 'Compare the REMOTE container and LOCAL file'
                            ' system and if the REMOTE container has objects'
                            ' NOT found in the LOCAL File System, DELETE THE'
                            ' REMOTE OBJECTS.',
                    'default': False,
                    'action': 'store_true'
                },
                'restore_perms': {
                    'commands': [
                        '--save-perms'
                    ],
                    'help': 'Save the UID, GID, and MODE, of a file as meta'
                            ' data on the object.',
                    'default': False,
                    'action': 'store_true'
                },
                'preserve_path': {
                    'commands': [
                        '-p',
                        '--preserve-path'
                    ],
                    'help': 'This will preserve the full path to a file when'
                            ' uploaded to a container.',
                    'default': False,
                    'action': 'store_true'
                }
            }
        }
    }
}

# Authentication plugins.
# Usage, Add any plugin here that will serve as a rapid means to authenticate.
# Syntax is as follows:
# <plugin_name>: {
#     'os_auth_url': <authentication_url>,
#     'args': {
#         'commands': [
#             '--<plugin_name>'
#         ],
#         'choices': [
#             <list_of_choices>
#         ],
#         'help': <help_information>,
#         'default': None,
#         'metavar': '[REGION]'
#     }
# }

# If the subdomain is in the auth url, as is the case with hp, add "%(region)s"
# to the "os_auth_url" value. The region value from the list of choices will be
# used as the string replacement.

__auth_plugins__ = {
    'os_rax_auth': {
        'os_auth_url': 'https://identity.api.rackspacecloud.com/v2.0/tokens',
        'os_prefix': 'RAX-KSKEY:apiKeyCredentials',
        'args': {
            'commands': [
                '--os-rax-auth'
            ],
            'choices': [
                'dfw',
                'ord',
                'iad',
                'syd',
                'hkg'
            ],
            'help': 'Authentication Plugin for Rackspace Cloud'
                    ' env[OS_RAX_AUTH]',
            'default': os.environ.get('OS_RAX_AUTH', None),
            'metavar': '[REGION]'
        }
    },
    'os_rax_auth_lon': {
        'os_auth_url': 'https://lon.identity.api.rackspacecloud.com/'
                       'v2.0/tokens',
        'os_prefix': 'RAX-KSKEY:apiKeyCredentials',
        'args': {
            'commands': [
                '--os-rax-auth-lon'
            ],
            'choices': [
                'lon'
            ],
            'help': 'Authentication Plugin for Rackspace Cloud'
                    ' env[OS_RAX_AUTH_LON]',
            'default': os.environ.get('OS_RAX_AUTH_LON', None),
            'metavar': '[REGION]'
        }
    },
    'os_hp_auth': {
        'os_auth_url': 'https://%(region)s.identity.hpcloudsvc.com:35357/'
                       'v2.0/tokens',
        'os_prefix': 'passwordCredentials',
        'args': {
            'commands': [
                '--os-hp-auth'
            ],
            'choices': [
                'region-b.geo-1',
                'region-a.geo-1'
            ],
            'help': 'Authentication Plugin for HP Cloud'
                    ' env[OS_HP_AUTH]',
            'default': os.environ.get('OS_HP_AUTH', None),
            'metavar': '[REGION]'
        }
    }
}

# Add all plugins to the optional arguments.
_optionals = ARGUMENTS['optional_args']
for name, value in __auth_plugins__.iteritems():
    _optionals.update({name: value['args']})
    # All Authentication plugins are appended to the auth_url exclusive group
    _optionals['mutually_exclusive']['auth_url']['group'].append(name)
