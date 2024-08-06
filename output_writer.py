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


class Output_Writer:
    
    def __init__(self, results, data, data_non_attributes, time, config):
        self.results = results
        self.data = data
        self.data_non_attributes = data_non_attributes
        self.nome_colonne = config.nome_colonne
        self.nome_colonne_non_attributi = config.nome_colonne_non_attributi
        self.algorithms = config.algorithms
        self.n_clusters = config.n_clusters
        self.date = config.date
        self.initial_date = config.initial_date
        self.output_name = config.output_name
        self.time = time
        self.attributes = config.attributes
        self.timesteps = config.timesteps
        self.plot_bool = config.plot
        self.extreme_scenario = config.extreme_scenario
        
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
        output_path = r"./output/" + now
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        if self.plot_bool:
            self.plot(output_path)
            
        # Aggiungo gli attributi richiesti tramite data iniziale
        self.add_attributes()
        
        # Stampo per ogni foglio i vari dati
        if self.date:
            self.add_date()
            
        
        # Stampo i risultati
        self.print_data(now)
        self.print_results(now)
        
        
#%% Sezione per gestire le date come indici dei dataframe
    def add_date(self): 
        Date = pd.date_range(self.initial_date, periods=len(self.data), freq="D", name="Date") # scelgo la data iniziale e la frequenza
        Date = [str(Date.tolist()[i]).split(" ")[0] for i in range (0, len(Date))] # Elimino l'ora dalla data
        self.data.index = Date
        
        if self.nome_colonne_non_attributi != str():
            self.data_non_attributes.index = Date
        
        for algorithm, list_results in self.results.items(): # Spacchetto i risultati per algoritmo
            for n_days, object_clustering in list_results.items(): # Spacchetto ogni caso con n giorno
                if algorithm != "kmeans": # Se avessi il kmeans non potrei trovare la data
                    for i, element in object_clustering.centres_with_labels.iterrows(): # Spacchetto i medoids/elementi vicini al centroide
                        # Associo la data corretta sostituendo l'indice con la data corrispondente al giorno (trovato tramite la colonna apposita Index_%)
                        # Valido sia per kmedoids che substitution
                        new_index = self.data.iloc[int(element['Index_representative_element'])].name 
                        object_clustering.centres_with_labels = object_clustering.centres_with_labels.rename(index={i:new_index})
                        

                    object_clustering.centres_with_labels = object_clustering.centres_with_labels.drop('Index_representative_element', axis=1)
                    


#%% Sezione per il print dei risultati
    # Metodo per printare i dati iniziali
    def print_data(self, now):
        intro = pd.DataFrame(["Segue il Dataset dei dati iniziali"])
        with pd.ExcelWriter("./output/" + now + "/" + self.output_name, engine="openpyxl") as writer:
            intro.to_excel(writer, sheet_name= "Data", header=False, index=False) # Stampo l'intro nella prima pagina
        with pd.ExcelWriter("./output/" + now + "/" + self.output_name, mode = "a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            # Apro in modalità append e con overlay, in modo da scrivere sopra ad uno stesso foglio e non sovrascrivere
            self.data.to_excel(writer, sheet_name = "Data", float_format="%.4f", startrow = 1)  
     
    # Metodo per printare i risultati
    def print_results(self, now):
        index = dict()
        with pd.ExcelWriter("./output/" + now + "/" + self.output_name, mode = "a", engine="openpyxl", if_sheet_exists="overlay") as writer:                
            for algorithm, list_results in self.results.items():
                for n_days, object_clustering in list_results.items():
                    if algorithm == self.algorithms[0]: # Se ho il primo algoritmo, stampo l'intro come prima riga
                        intro = pd.DataFrame(["Seguono i clusters per gli algoritmi, in ordine, " + "-".join(self.algorithms)])
                        intro.to_excel(writer, sheet_name= n_days, header=False, index=False)
                        index[n_days] = 2
                    intro = pd.DataFrame(["Algoritmo " + algorithm])
                    intro.to_excel(writer, sheet_name= n_days, header=False, index=False, startrow=index[n_days])
                    index[n_days] = index[n_days] + 1
                    object_clustering.centres_with_labels.to_excel(writer, sheet_name=n_days, float_format="%4f", startrow=index[n_days])
                    index[n_days] = index[n_days] + len(object_clustering.centres_with_labels) + 2
         
        self.time = pd.DataFrame.from_dict(self.time, orient='index', columns=["computational time"])
        with pd.ExcelWriter("./output/" + now + "/" + self.output_name, mode = "a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            self.time.to_excel(writer, sheet_name= "computational_time")
    
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