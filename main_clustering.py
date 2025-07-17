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
choice = "class" # [base_case, class]

if choice == "base_case":
    config = Config()
    input_processing = Input_processing(config)
    output_writer = Output_Writer(input_processing.results, input_processing.data, input_processing.data_non_attributes, input_processing.time, input_processing.ssd, config)
    


####################################################################################################################
################################################# OVERWRITE CONFIG #################################################
####################################################################################################################
elif choice == 'class':
    algorithms = ['kmeans', 'kmedoids', 'substitution']
    extreme_scenarios = [{'Prelievo': ['Replacing_max', 'Replacing_min']}]
    # extreme_scenarios = [{}] # , {"Electrical_demand": ['Adding_max'], "Thermal_demand": ['Adding_max']}, {"Electrical_demand": ['Replacing_max'], "Thermal_demand": ['Replacing_max']}]
    
    conversion_extreme_scenarios = {
        "{}": 'null',
        '{\'Electrical_demand\': [\'Adding_max\'], \'Thermal_demand\': [\'Adding_max\']}': 'adding',
        '{\'Electrical_demand\': [\'Replacing_max\'], \'Thermal_demand\': [\'Replacing_max\']}': 'replacing',
        '{\'Prelievo\': [\'Adding_max\', \'Adding_min\']}': 'adding',
        '{\'Prelievo\': [\'Replacing_max\', \'Replacing_min\']}': 'replacing',
        }
    
    conversion_algorithms = {
        "kmeans": "kmns",
        "kmedoids": "kmed",
        "substitution": "sub",
        "average": "av"
        }
      
    
    for algorithm in algorithms:
        for extreme_scenario in extreme_scenarios:
            config = Config()
            config.algorithms = [algorithm]
            config.extreme_scenario = extreme_scenario
            config.output_name_folder = f"{conversion_algorithms[algorithm]}_{conversion_extreme_scenarios[str(extreme_scenario)]}"
            print(config.output_name_folder)
            
            input_processing = Input_processing(config)
            output_writer = Output_Writer(input_processing.results, input_processing.data, input_processing.data_non_attributes, input_processing.time, input_processing.ssd, config)

        