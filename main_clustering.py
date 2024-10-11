# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 14:19:50 2024

@author: aless
"""


import logging


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -10s %(funcName) '
              '-10s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("Clustering").setLevel(logging.WARNING)
        
from input_processing import Input_processing
from config import Config
from output_writer import Output_Writer

# Aggiungi la possibilità di cambiare autonomamente la frequenza

config = Config()
input_processing = Input_processing(config)
output_writer = Output_Writer(input_processing.results, input_processing.data, input_processing.data_non_attributes, input_processing.time, config)
