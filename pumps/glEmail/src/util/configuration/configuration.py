
import configparser
from os.path import dirname
from os.path import join
from os.path import realpath
from os.path import sep
import os


def configFilePath():
        root = sep.join(dirname(realpath(__file__)).split(sep)[:-3])
        configpath = root + sep + "conf" + sep
        filename = root.split(sep)[-1] + ".conf"
        #configfilepath = join(configpath, filename)
        configfilepath =  os.path.dirname(os.path.abspath(__file__)) + "/../../../conf/voissemail.conf"
        return configfilepath


class Configuration(object):

    @staticmethod
    def section(section):
        configparser = ConfigParser()
        configparser.read(configFilePath())
        return dict(configparser.items(section))
