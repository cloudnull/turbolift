# =============================================================================
# Copyright [2015] [Kevin Carter]
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
__copyright__ = "2015 All Rights Reserved"
__license__ = "GPLv3+"
__date__ = "2015-07-04"
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
            'help': 'Object name(s) to work with. One or more object can be'
                    ' set at a time.',
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
                    ' with. The file MUST contain only one object per line.',
            'metavar': '[FILE]',
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
                '-s',  # This is for legacy and will be removed in the future
                '-d',
                '--directory'
            ],
            'help': 'Directory path to interact with.',
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
            'default': None,
            'choices': ['weeks', 'days', 'hours'],
            'metavar': '{weeks,days,hours}',
        },
        'time_factor': {
            'commands': [
                '--time-factor'
            ],
            'help': 'If Offset is used this will modify the offset value.'
                    ' The default: %(default)s.',
            'default': None,
            'type': float,
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
        },
        'download_chunk_size': {
            'commands': [
                '--download-chunk-size'
            ],
            'help': 'The size of the write chunks when downloading'
                    ' files.',
            'default': 2048,
            'type': int,
            'metavar': '[INT]'
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
        'os_auth_version': {
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
                    ' %(default)s. defaults to env[TURBO_LOGS]'
        },
        'log_file': {
            'commands': [
                '--log-file'
            ],
            'metavar': '[NAME]',
            'default': os.getenv('TURBO_LOGFILE', 'turbolift.log'),
            'help': 'Change the log file Log File is %(default)s.'
                    ' defaults to env[TURBO_LOGFILE]'
        },
        'colorized': {
            'commands': [
                '--colorized'
            ],
            'help': 'Colored output, effects logs and STDOUT. This will only'
                    ' colorize the log messages and items using the `print`'
                    ' function',
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
            'help': 'Set the service endpoint type. defaults to'
                    ' env[OS_ENDPOINT_TYPE]',
            'default': os.getenv('OS_ENDPOINT_TYPE', 'publicURL'),
            'required': False
        },
        'cdn_endpoint_type': {
            'commands': [
                '--cdn-endpoint-type'
            ],
            'help': 'Set the service endpoint type for a CDN network.'
                    ' defaults to env[OS_CDN_ENDPOINT_TYPE]',
            'default': os.getenv('OS_CDN_ENDPOINT_TYPE', 'publicURL'),
            'required': False
        },
        'force_internal_url': {
            'commands': [
                '-I',
                '--internal'
            ],
            'help': 'Forces the use of the "internalURL". Defaults to'
                    ' env[TURBO_INTERNAL]',
            'default': bool(os.getenv('TURBO_INTERNAL', False)),
            'action': 'store_true'
        },
        'concurrency': {
            'commands': [
                '-cc',
                '--concurrency'
            ],
            'metavar': '[INT]',
            'type': int,
            'default': os.getenv('TURBO_CONCURRENCY', 50),
            'help': 'This sets the operational concurrency. Defaults to'
                    ' env[TURBO_CONCURRENCY]'
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
                'mutually_exclusive': {
                    'list_groups': {
                        'text': 'Optional user defined object lists',
                        'required': False,
                        'group': [
                            'object',
                            'objects_file'
                        ]
                    }
                },
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
                'object',
                'directory',
                'container',
                'chunk_size',
                'large_object_size'
            ],
            'optional_args': {
                'tar_name': {
                    'commands': [
                        '--tar-name'
                    ],
                    'metavar': '[FILE_NAME]',
                    'help': 'Name of tarball archive. Use the full path to'
                            ' where you would like to save the archive. If you'
                            ' do not provide a full path the local working'
                            ' directory will be used.'
                },
                'add_timestamp': {
                    'commands': [
                        '--add-timestamp'
                    ],
                    'action': 'store_true',
                    'help': 'If set the system will append a timestamp to the'
                            ' archive name.',
                    'default': False
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
                'time_factor',
                'download_chunk_size',
                'container'
            ],
            'optional_args': {
                'mutually_exclusive': {
                    'source': {
                        'text': 'Source Options',
                        'group': [
                            'source_container',
                            'container'
                        ]
                    }
                },
                'groups': {
                    'target': {
                        'text': 'Target Options',
                        'group': [
                            'target_container',
                            'target_region',
                            'target_endpoint_type',
                            'target_auth_url',
                            'target_user',
                            'target_password',
                            'target_apikey'
                        ]
                    }
                },
                'source_container': {
                    'commands': [
                        '-sc',
                        '--source-container'
                    ],
                    'help': 'Source Container. DEPRECATED please use'
                            ' `--container` instead',
                    'required': True,
                    'default': None
                },
                'target_container': {
                    'commands': [
                        '-tc',
                        '--target-container'
                    ],
                    'help': 'Target Container.',
                    'required': True,
                    'default': None
                },
                'target_region': {
                    'commands': [
                        '-tr',
                        '--target-region'
                    ],
                    'help': 'Target Region.',
                    'required': True,
                    'default': None
                },
                'target_endpoint_type': {
                    'commands': [
                        '-te',
                        '--target-endpoint-type'
                    ],
                    'help': 'Set the service endpoint type for the target.',
                    'default': 'publicURL',
                    'required': False
                },
                'target_auth_url': {
                    'commands': [
                        '-ta',
                        '--target-auth-url'
                    ],
                    'help': 'Set the auth url for the target. If left blank'
                            ' this will default to the primary auth url',
                    'default': None,
                    'required': False
                },
                'target_user': {
                    'commands': [
                        '-tu',
                        '--target-user'
                    ],
                    'help': 'Set the user for the target. If left blank'
                            ' this will default to the primary user',
                    'default': None,
                    'required': False
                },
                'target_password': {
                    'commands': [
                        '-tp',
                        '--target-password'
                    ],
                    'help': 'Set the password for the target. If left blank'
                            ' this will default to the primary password',
                    'default': None,
                    'required': False
                },
                'target_apikey': {
                    'commands': [
                        '-tk',
                        '--target-apikey'
                    ],
                    'help': 'Set the apikey for the target. If left blank'
                            ' this will default to the primary apikey',
                    'default': None,
                    'required': False
                },
                'add_only': {
                    'commands': [
                        '--add-only'
                    ],
                    'action': 'store_true',
                    'help': 'Clone the object only if it doesn\'t already'
                            ' exist in the target container.',
                    'default': False
                },
                'workspace': {
                    'commands': [
                        '--workspace'
                    ],
                    'help': 'Set the local path that will be used for'
                            ' workspace as the clone operation is happening.'
                            ' If unset a secure temp directory will be used.',
                    'default': None,
                    'required': False
                },
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
                    },
                    'cdn_web_enabled': {
                        'text': 'Enable or Disable the CDN logging',
                        'required': False,
                        'group': [
                            'cdn_web_enabled',
                            'cdn_web_disabled'
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
                },
                'cdn_web_enabled': {
                    'commands': [
                        '--cdn-web-enabled'
                    ],
                    'help': 'Enable CDN web listing.',
                    'default': False,
                    'action': 'store_true'
                },
                'cdn_web_disabled': {
                    'commands': [
                        '--cdn-web-disabled'
                    ],
                    'help': 'Disabled CDN web listing.',
                    'default': False,
                    'action': 'store_true'
                },
                'cdn_web_error_content': {
                    'commands': [
                        '--cdn-web-error-content'
                    ],
                    'help': 'Create HTML error content for the CDN to serve',
                    'default': None,
                    'type': str,
                    'metavar': '[STR]'
                },
                'cdn_web_dir_type': {
                    'commands': [
                        '--cdn-web-dir-type'
                    ],
                    'help': 'Set the default content type used within a'
                            ' container.',
                    'default': None,
                    'type': str,
                    'metavar': '[STR]'
                },
                'cdn_web_css_object': {
                    'commands': [
                        '--cdn-web-css-object'
                    ],
                    'help': 'Object within a container to be used for css',
                    'default': None,
                    'type': str,
                    'metavar': '[STR]'
                },
                'cdn_web_index_object': {
                    'commands': [
                        '--cdn-web-index-object'
                    ],
                    'help': 'Object within a container to be used for index',
                    'default': None,
                    'type': str,
                    'metavar': '[STR]'
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
                'max_jobs',
                'download_chunk_size'
            ],
            'optional_args': {
                'groups': {
                    'list_groups': {
                        'text': 'Download arguments',
                        'group': [
                            'container',
                            'object',
                            'directory'
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
                'object_headers',
                'chunk_size',
                'large_object_size'
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
                'exclude': {
                    'commands': [
                        '--exclude'
                    ],
                    'nargs': '+',
                    'help': 'Exclude a pattern when uploading'
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


def auth_plugins(auth_plugins=None):
    """Authentication plugins.

    Usage, Add any plugin here that will serve as a rapid means to
    authenticate to an OpenStack environment.

    Syntax is as follows:
    >>> __auth_plugins__ = {
    ...     'new_plugin_name': {
    ...         'os_auth_url': 'https://localhost:5000/v2.0/tokens',
    ...         'os_prefix': {
    ...             'os_apikey': 'apiKeyCredentials',
    ...             'os_password': 'passwordCredentials'
    ...         },
    ...         'args': {
    ...             'commands': [
    ...                 '--new-plugin-name-auth'
    ...             ],
    ...             'choices': [
    ...                 'RegionOne'
    ...             ],
    ...             'help': 'Authentication plugin for New Plugin Name',
    ...             'default': os.environ.get('OS_NEW_PLUGIN_AUTH', None),
    ...             'metavar': '[REGION]'
    ...         }
    ...     }
    ... }

    If the subdomain is in the auth url, as is the case with hp, add
    "%(region)s" to the "os_auth_url" value. The region value from the list of
    choices will be used as the string replacement. Note that if the
    `os_prefix` key is added the system will override the authentication body
    prefix with the string provided. At this time the choices are os_apikey,
    os_password, os_token. All key entries are optional and should one not be
    specified with a credential type a `NotImplementedError` will be raised.

    :param auth_plugins: Additional plugins to add in
    :type auth_plugins: ``dict``
    :returns: ``dict``
    """

    __auth_plugins__ = {
        'os_rax_auth': {
            'os_auth_url': 'https://identity.api.rackspacecloud.com/v2.0/'
                           'tokens',
            'os_prefix': {
                'os_apikey': 'RAX-KSKEY:apiKeyCredentials',
                'os_password': 'passwordCredentials'
            },
            'args': {
                'commands': [
                    '--os-rax-auth'
                ],
                'choices': [
                    'dfw',
                    'ord',
                    'iad',
                    'syd',
                    'hkg',
                    'lon'
                ],
                'help': 'Authentication Plugin for Rackspace Cloud'
                        ' env[OS_RAX_AUTH]',
                'default': os.environ.get('OS_RAX_AUTH', None),
                'metavar': '[REGION]'
            }
        },
        'rax_auth_v1': {
            'os_auth_version': 'v1.0',
            'os_auth_url': 'https://identity.api.rackspacecloud.com/v1.0',
            'args': {
                'commands': [
                    '--rax-auth-v1'
                ],
                'action': 'store_true',
                'help': 'Authentication Plugin for Rackspace Cloud V1'
            }
        },
        'os_rax_auth_lon': {
            'os_auth_url': 'https://lon.identity.api.rackspacecloud.com/'
                           'v2.0/tokens',
            'os_prefix': {
                'os_apikey': 'RAX-KSKEY:apiKeyCredentials',
                'os_password': 'passwordCredentials'
            },
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
            'os_prefix': {
                'os_password': 'passwordCredentials'
            },
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
    if auth_plugins:
        __auth_plugins__.update(auth_plugins)

    return __auth_plugins__

# Add all plugins to the optional arguments.
_optionals = ARGUMENTS['optional_args']
for name, value in auth_plugins().items():
    _optionals.update({name: value['args']})
    # All Authentication plugins are appended to the auth_url exclusive group
    _optionals['mutually_exclusive']['auth_url']['group'].append(name)
