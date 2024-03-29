#! /usr/bin/env python

import argparse
import sys
import logging
from logging import config
from ndexutil.config import NDExUtilConfig

from datetime import datetime

import ndexnetworktrim

#from ndex2.client import Ndex2
import ndex2

logger = logging.getLogger(__name__)

TSV2NICECXMODULE = 'ndexutil.tsv.tsv2nicecx2'

LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"

def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('--profile', help='Profile in configuration '
                                          'file to use to load '
                                          'NDEx credentials which means'
                                          'configuration under [XXX] will be'
                                          'used '
                                          '(default '
                                          'ndexnetworktrim)',
                        default='ndexnetworktrim')
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')

    parser.add_argument('--conf', help='Configuration file to load '
                                       '(default ~/' +
                                       NDExUtilConfig.CONFIG_FILE)
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module and'
                             'in ' + TSV2NICECXMODULE + '. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default no '
                             'logging)')

    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' +
                                 ndexnetworktrim.__version__))


    parser.add_argument('--uuid', help='UUID of network to be trimmed', required=True)

    parser.add_argument('--edge_attr', help='Edge attribute to filter on', required=True)

    parser.add_argument('--value', help='Value of edge attribute used as cut-off ', required=True)


    return parser.parse_args(args)


def _setup_logging(args):
    """
    Sets up logging based on parsed command line arguments.
    If args.logconf is set use that configuration otherwise look
    at args.verbose and set logging for this module and the one
    in ndexutil specified by TSV2NICECXMODULE constant
    :param args: parsed command line arguments from argparse
    :raises AttributeError: If args is None or args.logconf is None
    :return: None
    """

    if args.logconf is None:
        level = (50 - (10 * args.verbose))
        logging.basicConfig(format=LOG_FORMAT,
                            level=level)
        logging.getLogger(TSV2NICECXMODULE).setLevel(level)
        logger.setLevel(level)
        return

    # logconf was set use that file
    logging.config.fileConfig(args.logconf,
                              disable_existing_loggers=False)


class NDExNetworkTrimmer(object):
    """
    Class to load content
    """
    def __init__(self, args):
        """

        :param args:
        """
        self._conf_file = args.conf
        self._profile = args.profile
        self._user = None
        self._pass = None
        self._server = None

        self._ndex = None
        self._network = None

        self._uuid = args.uuid
        self._edge_attr = args.edge_attr
        self._value = args.value

        self._is_value_numeric = False


        try:
            int(self._value)
            self._is_value_numeric = True
        except ValueError:
            try:
                float(self._value)
                self._is_value_numeric = True
            except ValueError:
                pass


    def _get_user_agent(self):
        """
        :return:
        """
        return 'ndexnetworktrimmer/' + ndexnetworktrim.__version__


    def _parse_config(self):
            """
            Parses config
            :return:
            """
            ncon = NDExUtilConfig(conf_file=self._conf_file)
            con = ncon.get_config()
            self._user = con.get(self._profile, NDExUtilConfig.USER)
            self._pass = con.get(self._profile, NDExUtilConfig.PASSWORD)
            self._server = con.get(self._profile, NDExUtilConfig.SERVER)

            if not self._user:
                raise Exception('user is not specified in configuration file')

            if not self._pass:
                raise Exception('password is not specified in configuration file')

            if not self._server:
                raise Exception('server is not specified in configuration file')

            return 0


    def _get_network_from_server(self):
        """
        """

        self._network = ndex2.create_nice_cx_from_server(
            server=self._server, uuid=self._uuid, username=self._user, password=self._pass)

        return 0


    def _check_if_edge_attribute_complies(self, edge_attributes):

        if not edge_attributes:
            return False

        if self._is_value_numeric:
            for attribute in edge_attributes:
                if attribute['n'] == self._edge_attr and attribute['v'] >= self._value:
                    return True
        else:
            for attribute in edge_attributes:
                if attribute['n'] == self._edge_attr and attribute['v'] == self._value:
                    return True

        return False



    def _trim_edges(self):

        edges_to_del = []

        for key in self._network.edges.keys():
            edge_attribute_id = self._network.edges[key]['@id']
            edge_attributes = self._network.edgeAttributes[edge_attribute_id]

            if not self._check_if_edge_attribute_complies(edge_attributes):
                edges_to_del.append(key)

        for key in edges_to_del:
            edge_attribute_id = self._network.edges[key]['@id']
            del self._network.edges[key]
            del self._network.edgeAttributes[edge_attribute_id]


    def _get_filter_expression_as_string(self):
        if self._is_value_numeric:
             filter_as_str = self._edge_attr + ' >= ' + self._value
        else:
             filter_as_str = self._edge_attr + ' = ' + self._value

        return filter_as_str


    def _set_new_network_name(self):

        #number_of_edges = len(self._network.edges)
        #if number_of_edges > 0:
        #    ratio = str( float(format(1.0 * len(self._network.nodes) / len(self._network.edges), '.3f' ) ) )
        #else:
        #    ratio = 'n/a'

        network_name = self._network.get_name() + ' ( ' + self._get_filter_expression_as_string() + ' )'

        self._network.set_name(network_name)


    def _get_URL_of_parent_network(self):

        url = self._server if self._server.startswith('http') else 'http://' + self._server

        url = url + '/#/network/' +  self._uuid

        return url


    def _set_network_attributes(self):

        parent_network_name =  self._network.get_network_attribute('name')['v']

        #self._set_new_network_name()

        self._network.set_network_attribute(name='prov:wasGeneratedBy', values=self._get_user_agent())

        self._network.set_network_attribute(name='prov:wasDerivedFrom', values=self._get_URL_of_parent_network())

        description = self._network.get_network_attribute('description')['v']

        description = '<p><b>This network is a filtered version of the <a href="' \
            + self._get_URL_of_parent_network() + '" target="_blank">' + parent_network_name + '</a></b>' \
            + ' database in which all edges correspond to associations with a ' + self._get_filter_expression_as_string() + '.</p>' \
            + description

        self._network.set_network_attribute(name='description', values=description)




    def _remove_orphan_nodes(self):

        nodes_with_edges = set()
        orphan_node_ids = set()

        # get all nodes that are connected to edgesre
        for key, value in self._network.edges.items():
            nodes_with_edges.add(value['s'])
            nodes_with_edges.add(value['t'])

        # get all nodes that are not connected to edges (get all orphan nodes)
        for key, value in self._network.nodes.items():
            if value['@id'] not in nodes_with_edges:
                orphan_node_ids.add(value['@id'])

        print ('edges: {}  nodes with edges: {}  orphan nodes: {}'.format(len(self._network.edges), len(nodes_with_edges), len(orphan_node_ids)) )

        # remove all orphan nodes and their attributes
        for orphan_node_id in orphan_node_ids:
            node_attribute_id = self._network.nodes[orphan_node_id]['@id']
            del self._network.nodes[node_attribute_id]
            del self._network.nodeAttributes[node_attribute_id]



    def run(self):
        """
        Runs content loading for NDEx Network Trimmer
        :param theargs:
        :return:
        """
        self._parse_config()

        self._get_network_from_server()

        self._trim_edges()

        self._remove_orphan_nodes()

        self._set_network_attributes()


        self._network.upload_to(self._server, self._user, self._pass)


        return 0

def main(args):
    """
    Main entry point for program
    :param args:
    :return:
    """
    desc = """
    Version {version}

    Loads NDEx Network Trimmer data into NDEx (http://ndexbio.org).

    To connect to NDEx server a configuration file must be passed
    into --conf parameter. If --conf is unset the configuration
    the path ~/{confname} is examined.

    The configuration file should be formatted as follows:

    [<value in --profile (default ncipid)>]

    {user} = <NDEx username>
    {password} = <NDEx password>
    {server} = <NDEx server(omit http) ie public.ndexbio.org>


    """.format(confname=NDExUtilConfig.CONFIG_FILE,
               user=NDExUtilConfig.USER,
               password=NDExUtilConfig.PASSWORD,
               server=NDExUtilConfig.SERVER,
               version=ndexnetworktrim.__version__)
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = ndexnetworktrim.__version__

    try:
        _setup_logging(theargs)
        loader = NDExNetworkTrimmer(theargs)
        return loader.run()
    except Exception as e:
        print('\n{}   {}\n'.format(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), e))
        return 2
    finally:
        logging.shutdown()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
