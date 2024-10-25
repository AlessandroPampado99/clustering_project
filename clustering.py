# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 13:44:22 2024

@author: aless
"""

import numpy as np
import pandas as pd


# Packs necessary for clustering
import os
os.environ["OMP_NUM_THREADS"] = '1'
pd.options.mode.chained_assignment = None  # default='warn'
from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids
from sklearn import metrics
from yellowbrick.cluster import SilhouetteVisualizer, KElbowVisualizer
from sklearn.preprocessing import MinMaxScaler

###############################################################################################################
############################################# CLUSTERING ######################################################
###############################################################################################################

class Clustering():
    
    # La classe avrà i seguenti input:
        # n_clusters: intero, numero di clusters
        # data: pandas contenente i vari dati da aggregare
        # kmeans: stringa indicante l'algoritmo kmeans o l'algoritmo di sostituzione (eventualmente da aggiungere k-MILP, etc.)
        # timesteps: intero, numero di timesteps (esempio 24 in un giorno)
        # attributes: numero di attributi nel processo di clustering
        # we
        
#%% Sezione di costruzione della classe
        
    def __init__(self, n_clusters, data, kmeans, timesteps, attributes, weight, n_years, extreme_periods, columns):
        self.n_clusters = n_clusters
        self.n_extreme_periods = 0
        self.weight = weight
        self.timesteps = timesteps
        
        self.init(kmeans, data, extreme_periods, n_years)
        
#%% Sezione di flusso logico della classe
        
    def init(self, kmeans, data, extreme_periods, n_years):
        # Normalizzazione
        data_norm = MinMaxScaler().fit_transform(data)

        # Metodi per l'algoritmo di clustering vero e proprio
        if kmeans == "kmedoids":
            clustering = KMedoids(n_clusters=self.n_clusters, metric='euclidean', method='alternate', init='heuristic', random_state=None).fit(data_norm)
            self.data_with_labels = pd.concat((data, pd.Series(clustering.labels_).rename("Index_clustering")), axis=1)
            self.kmedoids (clustering, data)
        else:
            # Processo di clustering
            clustering = KMeans(n_clusters=self.n_clusters, n_init='auto').fit(data_norm)
            # Salvo i dati iniziali con il rispettivo cluster come attributo
            self.data_with_labels = pd.concat((data, pd.Series(clustering.labels_).rename("Index_clustering")), axis=1)
            
            if kmeans == "kmeans":
                # Salvo i centroidi come attributo
                self.kmeans (clustering, data)
            else:
                self.substitution (clustering, data_norm, data)
        
        # Metodo per gli scenari estremi
        for key, list_values in extreme_periods.items():
            for value in list_values:
                if "Replacing".casefold() in value.casefold():
                    self.extreme_periods_replacing(key, value, kmeans)
                elif "Adding".casefold() in value.casefold():
                    self.extreme_periods_adding(key, value, kmeans, data_norm)
                
        # Metodo per il calcolo del peso dei cluster
        self.weight_definition(n_years)
                
#%% Sezione per la definzione del peso     
    def weight_definition (self, n_years):
        if self.weight == "cluster_frequency":
            # Calcola il peso come numero di elementi per ogni cluster
            weights = np.bincount(self.data_with_labels['Index_clustering']) / n_years
            
            # Correggo i pesi uguali a zero in caso capitassero
            # Trova se ci sono zeri e sostituiscili con 1
            zero_indices = np.where(weights == 0)[0]  # Ottieni gli indici degli zeri
            
            if len(zero_indices) > 0:
                # Se ci sono zeri, sostituisci con 1
                weights[zero_indices] = 0.5
                # Trova l'indice del massimo
                max_index = np.argmax(weights)
                # Sottrai 1 al massimo
                weights[max_index] -= 0.5
            
            self.centres_with_labels = pd.concat((self.centres_with_labels, pd.Series(weights).rename("Weight")), axis=1)

#%% Sezione per la definizione dell'algoritmo
    def kmeans (self, clustering, data):
        self.centres_with_labels = clustering.cluster_centers_
        # De-normalizzazione
        for i, column in enumerate(data):
            self.centres_with_labels[:, i] = self.centres_with_labels[:, i] * (data[column].max() - data[column].min()) + data[column].min()
        
        # Rimetto i nomi delle colonne iniziali per pulizia dei dati di output
        self.centres_with_labels = pd.DataFrame(self.centres_with_labels).set_axis([column for column in data], axis=1)
        # Aggiungo etichetta per sottolineare di quale cluster sono i centroidi
        self.centres_with_labels = pd.concat((self.centres_with_labels, pd.Series([i for i in range(0, self.n_clusters)]).rename("Index_clustering")), axis=1)
        
    def kmedoids (self, clustering, data):
        self.centres_with_labels = clustering.cluster_centers_
        # De-normalizzazione
        for i, column in enumerate(data):
            self.centres_with_labels[:, i] = self.centres_with_labels[:, i] * (data[column].max() - data[column].min()) + data[column].min()
        
        # Rimetto i nomi delle colonne iniziali per pulizia dei dati di output
        self.centres_with_labels = pd.DataFrame(self.centres_with_labels).set_axis([column for column in data], axis=1)
        # Aggiungo etichetta per sottolineare di quale cluster sono i centroidi
        self.centres_with_labels = pd.concat((self.centres_with_labels, pd.Series([i for i in range(0, self.n_clusters)]).rename("Index_clustering"), pd.Series(clustering.medoid_indices_).rename("Index_representative_element")), axis=1)
  
        
    def substitution (self, clustering, data_norm, data):
        # Trovo gli elementi più vicini al centroide e li setto come elementi rappresentativi
        t = pd.DataFrame({"ind_rep_row": np.where(clustering.transform(data_norm) == clustering.transform(data_norm).min(axis=0))[0], "Index_clustering": np.where(clustering.transform(data_norm) == clustering.transform(data_norm).min(axis=0))[1]})
        t = t.drop_duplicates(subset=['Index_clustering'], keep='first') # Per evitare di avere più clusters del dovuto
        self.centres_with_labels = data.iloc[t["ind_rep_row"]].set_index(t["Index_clustering"])
        t = t.set_index("Index_clustering")
        # Aggiungo etichetta per sottolineare di quale cluster sono gli elementi rappresentativi
        self.centres_with_labels = pd.concat((self.centres_with_labels, t["ind_rep_row"].rename("Index_representative_element")), axis=1)
        self.centres_with_labels = self.centres_with_labels.sort_index()
        self.centres_with_labels = pd.concat((self.centres_with_labels.reset_index(drop=True), pd.Series(self.centres_with_labels.index)), axis=1)
       

#%% Sezione per la definizione del criterio per gli scenari estremi

# Metodo per l'individuazione dello scenario estremo
    def extreme_period_definition (self, key, value):
        if "max" in value:
            if self.timesteps == 1:
                # In questo caso prendiamo il massimo singolo, non la somma sul giorno (da integrare se voluto)
                # Cerco la riga dove c'è un elemento pari a quello massimo
                extreme_element = self.data_with_labels.iloc[np.where(self.data_with_labels[key] == self.data_with_labels[key].max())[0][0]]
            else:
                extreme_element_list = list()
                extreme_column_list = list()
                # For per aggiungere per ogni colonna (dell'attributo desiderato) l'elemento massimo
                for column in self.data_with_labels:
                    if key in column:
                        extreme_element_list.append(self.data_with_labels[column].max())
                        extreme_column_list.append(column)
                extreme_element = max(extreme_element_list)
                extreme_column = extreme_column_list[extreme_element_list.index(extreme_element)]
                # Qua non è più la chiave iniziale key ma una delle colonne differenti
                extreme_element = self.data_with_labels.iloc[np.where(self.data_with_labels[extreme_column] == extreme_element)[0][0]]
        elif "min" in value: # analogo al caso massimo
            if self.timesteps == 1:
                # In questo caso prendiamo il massimo singolo, non la somma sul giorno (da integrare se voluto)
                extreme_element = self.data_with_labels.iloc[np.where(self.data_with_labels[key] == self.data_with_labels[key].min())[0][0]]
            else:
                extreme_element_list = list()
                extreme_column_list = list()
                for column in self.data_with_labels:
                    if key in column:
                        extreme_element_list.append(self.data_with_labels[column].min())
                        extreme_column_list.append(column)
                extreme_element = min(extreme_element_list)
                extreme_column = extreme_column_list[extreme_element_list.index(extreme_element)]
                extreme_element = self.data_with_labels.iloc[np.where(self.data_with_labels[extreme_column] == extreme_element)[0][0]]
        return extreme_element
    

# Metodo per il replacing criterion
    def extreme_periods_replacing(self, key, value, kmeans):
        self.n_extreme_periods += 1
        
        extreme_element = self.extreme_period_definition(key, value)

        if kmeans == "kmeans":
            # Sostituisci la riga il cui cluster coincide con quello dell'elemento estremo
            self.centres_with_labels.iloc [np.where(self.centres_with_labels['Index_clustering'] == extreme_element['Index_clustering'])[0][0]] = extreme_element
        elif kmeans == "kmedoids":
            extreme_element = pd.concat((extreme_element, pd.Series(extreme_element.name).set_axis(["Index_representative_element"])))
            self.centres_with_labels.iloc [np.where(self.centres_with_labels['Index_clustering'] == extreme_element['Index_clustering'])[0][0]] = extreme_element
        elif kmeans == "substitution":
            self.centres_with_labels = self.centres_with_labels.set_index("Index_representative_element")
            self.centres_with_labels.iloc [np.where(self.centres_with_labels['Index_clustering'] == extreme_element['Index_clustering'])[0][0]] = extreme_element
            self.centres_with_labels = pd.concat((self.centres_with_labels.reset_index(drop=True), pd.Series(self.centres_with_labels.index)), axis=1)
            # Correggo l'elemento più vicino al centroide (ora è quello estremo, l'indice deve essere il suo)
            self.centres_with_labels["Index_representative_element"][np.where(self.centres_with_labels['Index_clustering'] == extreme_element['Index_clustering'])[0][0]] = extreme_element.name
        

# Metodo per l'adding criterion
    def extreme_periods_adding(self, key, value, kmeans, data_norm):
        self.n_extreme_periods += 1
        self.n_clusters +=1
        
        extreme_element = self.extreme_period_definition(key, value)
        extreme_element['Index_clustering'] = self.n_clusters - 1
        
        if kmeans == "kmeans":
            self.centres_with_labels = pd.concat((self.centres_with_labels, pd.DataFrame(extreme_element).transpose()), axis=0)
            centres = MinMaxScaler().fit_transform(self.centres_with_labels.drop('Index_clustering', axis=1))
        elif kmeans == "kmedoids":
            extreme_element = pd.concat((extreme_element, pd.Series(extreme_element.name).set_axis(["Index_representative_element"])))
            self.centres_with_labels = pd.concat((self.centres_with_labels, pd.DataFrame(extreme_element).transpose()), axis=0)
            centres = MinMaxScaler().fit_transform(self.centres_with_labels.drop(['Index_clustering', 'Index_representative_element'], axis=1))
        elif kmeans == "substitution":
            self.centres_with_labels = self.centres_with_labels.set_index("Index_representative_element")
            # Aggiungo l'elemento estremo
            self.centres_with_labels = pd.concat((self.centres_with_labels, pd.DataFrame(extreme_element).transpose()), axis=0)
            self.centres_with_labels.index.names = ['Index_representative_element']
            # Mi definisco anche il vettore con i soli centri
            centres = MinMaxScaler().fit_transform(self.centres_with_labels.drop('Index_clustering',  axis=1))
            self.centres_with_labels = pd.concat((self.centres_with_labels.reset_index(drop=True), pd.Series(self.centres_with_labels.index)), axis=1)
            
        self.centres_with_labels = self.centres_with_labels.set_index("Index_clustering", drop=False)
        # Da commentare e da pulire le righe in cui vai a concatenare il tutto
        
        for row, element in enumerate(data_norm):
            self.data_with_labels.loc[row, 'Index_clustering'] = np.where(np.sum((data_norm[row] - centres)**2, axis=1)**1/2 == (np.sum((data_norm[row] - centres)**2, axis=1)**1/2).min())[0][0]
        
###############################################################################################################
########################################## AVERAGE PROFILES ###################################################
###############################################################################################################

#%% Class average profiles
class AverageProfiles():
    def __init__(self, parser, data, timesteps, attributes, columns):
        self.parser = parser
        self.data = data
        self.timesteps = timesteps
        self.attributes = attributes
        self.columns = columns
        
        self.init()
        
    def init(self):
        weight = self.weight_definition()
        self.average_profiles_evaluation(weight)
        
        
    def weight_definition(self):
        weight = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return weight
    
    def average_profiles_evaluation(self, weight):
        # Set the date for all the Date (here instead of post-processing)
        Date = pd.date_range(start=self.parser.initial_date, periods=len(self.data), freq='D')
        self.data.index = Date
        
        # I group data based on months
        self.data['month'] = Date.month
        
        # I evaluate the average profiles
        mean_profiles = self.data.groupby('month').mean()
        
        # I evaluate the date for the average profiles
        Date_mean_profiles = pd.date_range(start=self.parser.initial_date, periods=len(mean_profiles), freq='ME')
        mean_profiles.index = Date_mean_profiles
        
        # I add the column weight
        mean_profiles['weight'] = weight
        
        # I set the average profiles as centres_with_labels
        self.centres_with_labels = mean_profiles
        
        