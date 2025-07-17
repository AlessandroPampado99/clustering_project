# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 10:57:36 2024

@author: aless
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
import matplotlib.pyplot as plt

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -10s %(funcName) '
              '-10s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("Clustering").setLevel(logging.WARNING)


class Output_Writer:
    
    def __init__(self, results, data, data_non_attributes, time, ssd, config):
        self.results = results
        self.data = data
        self.data_non_attributes = data_non_attributes
        self.nome_colonne = config.nome_colonne
        self.nome_colonne_non_attributi = config.nome_colonne_non_attributi
        self.algorithms = config.algorithms
        self.n_clusters = config.n_clusters
        self.date = config.date
        self.date_fake_kmeans = config.date_fake_kmeans
        self.initial_date = config.initial_date
        self.output_name = config.output_name
        self.time = time
        self.ssd = ssd
        self.attributes = config.attributes
        self.timesteps = config.timesteps
        self.plot_bool = config.plot
        self.extreme_scenario = config.extreme_scenario
        self.output_name_folder = config.output_name_folder
        
        self.init()

#%% Sezione di flusso logico per la classe
    def init(self):
        # Creo la cartella generale dei risultati (se non esiste)
        output_path = r"./output/" 
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Creo la cartella dei risultati specifici
        # Genero la data odierna con ora annessa
        now = datetime.now() # current date and time
        now = str(now.strftime("%m-%d-%Y_%H-%M-%S"))
        
        if self.output_name_folder != str():
            output_path = r"./output/" + self.output_name_folder
        else:
            output_path = r"./output/" + now
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        if self.plot_bool:
            self.plot(output_path)
            
        # Aggiungo gli attributi richiesti tramite data iniziale
        if not self.data_non_attributes.empty:
            self.add_attributes()
        
        # Stampo per ogni foglio i vari dati
        if self.date:
            self.add_date()
            
        # Stampo i risultati
        self.print_data(output_path)
        
        self.print_results(output_path)
        
        self.print_data_with_labels(output_path)
        
        
        
#%% Sezione per gestire le date come indici dei dataframe
    def add_date(self): 
        # Numero di periodi desiderato, escludendo i 29 febbraio
        num_periods = len(self.data)

        # Stimiamo un numero maggiore di date per includere i 29 febbraio
        extra_days = int(num_periods * 0.003)  # circa un giorno in più ogni 400, per compensare i 29 febbraio
        date_range = pd.date_range(self.initial_date, periods=num_periods + extra_days, freq="D", name="Date")

        # Filtriamo per rimuovere i 29 febbraio
        date_range_no_leap = date_range[~((date_range.month == 2) & (date_range.day == 29))]

        # Prendiamo solo i primi `num_periods` giorni
        date_range_no_leap = date_range_no_leap[:num_periods]
        
        Date = [str(date_range_no_leap.tolist()[i]).split(" ")[0] for i in range (0, len(date_range_no_leap))] # Elimino l'ora dalla data
        self.data.index = Date
        
        if self.nome_colonne_non_attributi != str():
            self.data_non_attributes.index = Date
        
        for algorithm, list_results in self.results.items(): # Spacchetto i risultati per algoritmo
            for n_days, object_clustering in list_results.items(): # Spacchetto ogni caso con n giorno
                if algorithm not in  ["kmeans", "average"]: # Se avessi il kmeans non potrei trovare la data
                    for i, element in object_clustering.centres_with_labels.iterrows(): # Spacchetto i medoids/elementi vicini al centroide
                        # Associo la data corretta sostituendo l'indice con la data corrispondente al giorno (trovato tramite la colonna apposita Index_%)
                        # Valido sia per kmedoids che substitution
                        new_index = self.data.iloc[int(element['Index_representative_element'])].name 
                        object_clustering.centres_with_labels = object_clustering.centres_with_labels.rename(index={i:new_index})
                    object_clustering.centres_with_labels = object_clustering.centres_with_labels.drop('Index_representative_element', axis=1)
                elif self.date_fake_kmeans:
                    new_date = pd.date_range(self.initial_date, periods=len(object_clustering.centres_with_labels), freq="D", name="Date")
                    object_clustering.centres_with_labels.index = new_date

                    
                                    
                

#%% Sezione per il print dei risultati
    # Metodo per printare i dati iniziali
    def print_data(self, output_path):
        vecchio_now = datetime.now()
        # Stampo tutti i dati (attributi e non)
        data_total = pd.concat((self.data, self.data_non_attributes), axis=1)
        intro = pd.DataFrame(["Segue il Dataset dei dati iniziali"])
        with pd.ExcelWriter(output_path + "/" + self.output_name, engine="openpyxl") as writer:
            intro.to_excel(writer, sheet_name= "Data", header=False, index=False) # Stampo l'intro nella prima pagina
        with pd.ExcelWriter(output_path + "/" + self.output_name, mode = "a",  engine="openpyxl", if_sheet_exists="overlay") as writer:
            # Apro in modalità append e con overlay, in modo da scrivere sopra ad uno stesso foglio e non sovrascrivere
            data_total.to_excel(writer, sheet_name = "Data", float_format="%.4f", startrow = 1)  
        LOGGER.info(f"Stampati i dati in {datetime.now()-vecchio_now}s")
     
    # Metodo per printare i risultati
    def print_results(self, output_path):
        self.time = pd.DataFrame.from_dict(self.time, orient='index', columns=["computational time"])
        self.ssd = pd.DataFrame.from_dict(self.ssd, orient='index', columns=["SSD"])
        with pd.ExcelWriter(output_path + "/" + self.output_name, mode = "a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            self.time.to_excel(writer, sheet_name= "computational_time")
            self.ssd.to_excel(writer, sheet_name= "SSD")
        
        index = dict()
        vecchio_now = datetime.now()
        with pd.ExcelWriter(output_path + "/" + self.output_name, mode = "a", engine="openpyxl", if_sheet_exists="overlay") as writer:                
            for algorithm, list_results in self.results.items():
                for n_days, object_clustering in list_results.items():
                    vecchio_now = datetime.now()
                    if algorithm == self.algorithms[0]: # Se ho il primo algoritmo, stampo l'intro come prima riga
                        index[n_days] = -1
                    index[n_days] = index[n_days] + 1
                    object_clustering.centres_with_labels.to_excel(writer, sheet_name=n_days, float_format="%4f", startrow=index[n_days])
                    index[n_days] = index[n_days] + len(object_clustering.centres_with_labels) + 2
                    
                    LOGGER.info(f"Stampati i risultati di {algorithm} con {n_days} clusters in {datetime.now() - vecchio_now}")
      
        
    def print_data_with_labels(self, output_path):
        """
        Prints data_with_labels + data_non_attributes for each algorithm and n_days 
        into a new Excel file with same sheet logic as print_results.
        """
        index = dict()
        output_file = self.output_name.replace(".xlsx", "_data_total.xlsx")
        output_full_path = os.path.join(output_path, output_file)
    
        for algorithm, list_results in self.results.items():
            for n_days, object_clustering in list_results.items():
    
                if algorithm == self.algorithms[0]:
                    index[n_days] = -1
                index[n_days] = index[n_days] + 1
    
                df_with_labels = pd.concat(
                    (object_clustering.data_with_labels, self.data_non_attributes), axis=1
                )
    
                # Scegli il mode
                file_exists = os.path.exists(output_full_path)
                mode = "a" if file_exists else "w"
    
                # Usa ExcelWriter in modo compatibile
                if mode == "a":
                    writer = pd.ExcelWriter(output_full_path, mode=mode, engine="openpyxl", if_sheet_exists="overlay")
                else:
                    writer = pd.ExcelWriter(output_full_path, mode=mode, engine="openpyxl")
    
                with writer:
                    df_with_labels.to_excel(writer, sheet_name=n_days, float_format="%.4f", startrow=index[n_days])
                    index[n_days] += len(df_with_labels) + 2





    
#%% Sezione per la generazione dei grafici
    # Metodo per plottare i grafici
    def plot(self, output_path):
        index_algorithm = 0
        for algorithm, list_results in self.results.items(): # Spacchetto i risultati per algoritmo
            index_algorithm += 1
            index_days = 0
            for n_days, object_clustering in list_results.items(): # Spacchetto ogni caso con n giorno
                for i in range (0, int(self.attributes)):
                    subset = object_clustering.centres_with_labels.iloc[:, i*self.timesteps : i*self.timesteps+self.timesteps].transpose()
                    subset.columns = ["cluster_" + str(int(i)) for i in subset.columns]
                    
                    subset_numpy = np.array(subset)

                    fig = plt.figure(index_days*self.attributes + i)
                    plt.subplot(len(self.results.keys()),1,index_algorithm)
                    plt.gca().set_title(str(algorithm))
                    for profile in range(0, len(subset_numpy[0])):
                        if profile >= (object_clustering.n_clusters - object_clustering.n_extreme_periods): # and subset.index[0].split("_0")[0] in self.extreme_scenario
                            plt.plot(subset_numpy[:,profile], linewidth=2, color="r")
                        else:
                            plt.plot(subset_numpy[:,profile], linewidth=1, color="k", alpha=0.8)

                        
                    plt.ylabel(subset.index[0].split("_0")[0].replace("_"," "))
                    fig.tight_layout()
                    
                    if index_algorithm == len(self.results.keys()):
                        plt.xlabel("timesteps")
                        
                        output_name = subset.index[0].replace("_0", "").replace("_", " ")
                        output_path_plot = output_path + "/" + output_name
                        if not os.path.exists(output_path_plot):
                            os.makedirs(output_path_plot)
                        
                        plt.savefig(output_path_plot + '/profiles of ' + output_name + ' for ' + n_days)
                index_days += 1
                    
#%% Aggiungo ulteriori attributi non presenti nel clustering
    def add_attributes(self):
        for algorithm, list_results in self.results.items(): # Spacchetto i risultati per algoritmo
            for n_days, object_clustering in list_results.items(): # Spacchetto ogni caso con n giorno
               if algorithm != "kmeans": # Se avessi il kmeans non potrei trovare la data
                   df_non_attributes = self.data_non_attributes.iloc[object_clustering.centres_with_labels['Index_representative_element']]
                   df_non_attributes = df_non_attributes.set_index (object_clustering.centres_with_labels.index)
                   object_clustering.centres_with_labels = pd.concat((object_clustering.centres_with_labels, df_non_attributes), axis=1)