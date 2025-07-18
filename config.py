# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 15:37:11 2024

@author: aless
"""

import logging
from configparser import ConfigParser

# Classe per la configurazione iniziale dei dati di input
        
class Config():
    def __init__(self):
        self.parser = ConfigParser()
        self.parser.read("config/application.ini", encoding="latin-1")
        
        self.init()
        
#%% Section for the workflow of the system
    def init(self):
        self.set_attributes()

#%% Method to dinamically read the parameters in the config file
    def set_attributes(self):
        for section in self.parser.sections():
            for key in self.parser[section]:
                self.attribute_definition(key, self.parse_value(self.parser[section][key]))

#%% Method to understand the type of the parsed value
    def parse_value(self, value):
        try:
            # Try to evaluate the value
            evaluated_value = eval(value)
            # If the evaluated value is not a string, return it
            if not isinstance(evaluated_value, str):
                return evaluated_value
        except:
            # If evaluation fails, return the original string
            pass
        return value

#%% Method to set the attribute of config
    def attribute_definition(self, key, value):
        setattr(self, key, value)