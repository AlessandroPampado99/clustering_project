# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 15:47:49 2024

@author: aless
"""

from clustering import Clustering
from clustering import AverageProfiles
import pandas as pd
import numpy as np
import logging
from datetime import datetime

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -10s %(funcName) '
              '-10s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("Clustering").setLevel(logging.WARNING)

class Input_processing():
    def __init__(self, parser):
        # Attributo contenente le informazioni necessarie per la configurazione
        self.parser = parser
        
        # Dizionario con i risultati, già divisi per algoritmo utilizzato
        self.results = dict()
        for algorithm in self.parser.algorithms:
            self.results[algorithm] = dict()
        self.time = dict()
        
        self.init()
        
    def init(self):

        # Metodo per il caricamento del file e pulizia del dataset
        self.input_reader()
        self.timesteps_preprocessing()
        self.clustering_process()
        
        
    def input_reader(self):
        if self.parser.nome_excel == str():
            if self.parser.nome_sheet == str():
                self.data = pd.read_csv(self.parser.path + "/" + self.parser.nome_csv)
            else:
                self.data = pd.read_csv(self.parser.path + self.parser.nome_csv)
                LOGGER.warning('Il nome del foglio non dovrebbe essere un parametro, perché read_csv non lo supporta')
        elif self.parser.nome_csv == str():
            if self.parser.nome_sheet == str():
                self.data = pd.read_excel(self.parser.path + self.parser.nome_excel)
            else:
                self.data = pd.read_excel(self.parser.path + "/" + self.parser.nome_excel, sheet_name=self.parser.nome_sheet)
        else:
            LOGGER.warning('Definire correttamente il nome del file e il formato')
            
            
        if self.parser.nome_colonne != list():
            self.data.columns = self.parser.nome_colonne
        if self.parser.nome_colonne_non_attributi != str():
            self.data_non_attributes = self.data[self.parser.nome_colonne_non_attributi]
        else:
            self.data_non_attributes = pd.DataFrame()
        if self.parser.nome_colonne_da_eliminare != str():
            self.data = self.data.drop(self.parser.nome_colonne_da_eliminare, axis=1)

        else:
            self.data_non_attributes = str()
            LOGGER.info('Tutti gli elementi di interesse sono attributi di clustering')
        
        # To delete rows with nan elements
        self.data = self.data.dropna()
    
     
    def timesteps_preprocessing(self):
        if self.parser.timesteps == 1:
            pass
        else:
            # In caso di timesteps != 1, bisogna riorganizzare il DataFrame con nuove colonne, nominate come colonna_i con i tra 0 e timesteps
            # Ciclo for per eliminare le colonne superflue dall'attributo contenente le colonne
            for colonna in self.parser.nome_colonne_da_eliminare:
                self.parser.nome_colonne.remove(colonna)
            self.parser.nome_colonne = [j + "_" + str(i) for j in self.parser.nome_colonne for i in range(0, self.parser.timesteps)]
            nome_colonne_non_attributi = [j + "_" + str(i) for j in self.parser.nome_colonne_non_attributi for i in range(0, self.parser.timesteps)]
            # data_reshaped servirà da base al nuovo DataFrame, ha infatti il numero di righe corretto
                # Ogni colonna contiene tutti i timesteps per ogni attributo
            data_reshaped = np.zeros((int(len(self.data)/(self.parser.timesteps)), 1))
            for column in self.data:
                column_reshaped = np.reshape(np.array(self.data[column]), (int(len(self.data)/(self.parser.timesteps)),self.parser.timesteps), order="C")
                data_reshaped = np.concatenate((data_reshaped,column_reshaped), axis=1)
            self.data = pd.DataFrame(data_reshaped[:,1:])
            self.data.columns = self.parser.nome_colonne
            
            if self.parser.nome_colonne_non_attributi != str():
                # Analogamente per i non-attributi
                data_reshaped = np.zeros((int(len(self.data_non_attributes)/(self.parser.timesteps)), 1))
                for column in self.data_non_attributes:
                    column_reshaped = np.reshape(np.array(self.data_non_attributes[column]), (int(len(self.data_non_attributes)/(self.parser.timesteps)),self.parser.timesteps), order="C")
                    data_reshaped = np.concatenate((data_reshaped,column_reshaped), axis=1)
                self.data_non_attributes = pd.DataFrame(data_reshaped[:,1:])
                self.data_non_attributes.columns = nome_colonne_non_attributi
            
    
    def clustering_process(self):
        # Ciclo for per i diversi algoritmi
        for algoritmo in self.parser.algorithms:
            if algoritmo.lower() == 'average':
                beginning = datetime.now()
                self.results['average']['12_clusters'] = AverageProfiles(self.parser, self.data, self.parser.timesteps, self.parser.attributes, self.parser.nome_colonne)
                end = datetime.now()
                self.time['average_12_clusters'] = str(end-beginning)
                LOGGER.info(f"{algoritmo} completato in {str(end-beginning)}s")
            else:
                # ciclo for per il numero di giorni rappresentativi
                for n in range(self.parser.n_clusters[0], self.parser.n_clusters[-1]+1):
                    beginning = datetime.now() 
                    # ciclo per i diversi giorni rappresentativi (da implementare una funzionalità per far variare i criteria, nel caso)
                    self.results[algoritmo][str(n) + "_clusters"]  = Clustering(n, self.data, algoritmo, self.parser.timesteps, self.parser.attributes, self.parser.weight, self.parser.n_years, self.parser.extreme_scenario, self.parser.nome_colonne)
                    end = datetime.now()
                    self.time[algoritmo + "_" + str(n) + "_clusters"] = str(end-beginning)            
                    LOGGER.info(f"{algoritmo} con {n} clusters completato in {str(end-beginning)}s")
             
        
            
       
            
        
        