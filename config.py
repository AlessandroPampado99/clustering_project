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
        self.parser.read("./config/application.ini")
        
        self.nome_csv = self.parser.get("INPUT", "nome_csv")
        self.nome_excel = self.parser.get("INPUT", "nome_excel")
        self.path = self.parser.get("INPUT", "path")
        self.nome_sheet = self.parser.get("INPUT", "nome_sheet")
        
        self.nome_colonne = eval(self.parser.get("INPUT", "nome_colonne"))
        if "[" in self.parser.get("INPUT", "nome_colonne_da_eliminare"):
            self.nome_colonne_da_eliminare = eval(self.parser.get("INPUT", "nome_colonne_da_eliminare")) 
        else:
            self.nome_colonne_da_eliminare = self.parser.get("INPUT", "nome_colonne_da_eliminare") 
        
        if "[" in self.parser.get("INPUT", "nome_colonne_non_attributi"):
            self.nome_colonne_non_attributi = eval(self.parser.get("INPUT", "nome_colonne_non_attributi")) 
        else:
            self.nome_colonne_non_attributi = self.parser.get("INPUT", "nome_colonne_non_attributi") 
        
        self.timesteps = eval(self.parser.get("CLUSTERING", "timesteps"))
        self.attributes = eval(self.parser.get("CLUSTERING", "attributes"))
        
        self.algorithms = eval(self.parser.get("CLUSTERING", "algoritmo"))
        self.n_clusters = eval(self.parser.get("CLUSTERING", "n_clusters_list"))
        
        self.extreme_scenario = eval(self.parser.get("CLUSTERING", "extreme_scenario"))
        self.weight = (self.parser.get("CLUSTERING", "weight"))
        
        self.date = eval(self.parser.get("OUTPUT", "date"))
        self.initial_date = self.parser.get("OUTPUT","initial_date")
        self.output_name = self.parser.get("OUTPUT","output_name")
        self.plot = eval(self.parser.get("OUTPUT", "plot"))