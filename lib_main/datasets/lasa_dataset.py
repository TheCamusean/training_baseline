import os, sys, time
import json

import matplotlib.pyplot as plt
import numpy as np
import scipy.io as spio
import torch
from lib_main.datasets.generic_dataset import VDataset
from lib_main import visualization as vis

directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..','data')) + '/LASA_dataset/'
directory_s2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..','data')) + '/LASA_S2_dataset/'


class LASA():
    def __init__(self, filename='Sshape', PLOT=False):
        ## Define Variables and Load trajectories ##
        self.filename = filename
        self.dim = 2
        self.dt = 0.01

        mat = spio.loadmat(directory + filename + '.mat', squeeze_me=True)
        self.trajs_real=[]
        for demo_i in mat['demos']:
            x = demo_i[0]
            y = demo_i[1]
            tr_i = np.stack((x,y))
            self.trajs_real.append(tr_i.T)
        self.trajs_np = np.asarray(self.trajs_real)

        self.n_trajs = self.trajs_np.shape[0]
        self.trj_length = self.trajs_np.shape[1]

        ## Normalize trajectories ##
        self.trajs_normal, self.min_trjs, self.max_trjs, self.goal = self.normalize(self.trajs_np)
        self.init_position = self.trajs_normal[:,0,:]

        ## Build Train Dataset
        r = np.linalg.norm(self.trajs_normal, axis=-1)
        r_max = np.max(r)
        self.alpha = (np.pi-0.1)/r_max
        self.train_data = []
        for i in range(self.trajs_normal.shape[0]):
            self.train_data.append(self.alpha*self.trajs_normal[i, ...])
        self.dataset = VDataset(trajs=self.train_data, dt = self.dt)

        ## VISUALIZE ##
        if PLOT:
            fig, ax = plt.subplots()
            vis.visualize_trajectories(self.train_data[0], ax=ax)
            plt.show()

    def normalize(self, trjs):
        min_trjs = np.min(trjs)
        max_trjs = np.max(trjs)

        trjs_normalized = (trjs - min_trjs)/(max_trjs - min_trjs)
        goal = np.mean(trjs_normalized[:,-1,:], 0)
        trjs_normalized_centered = trjs_normalized - goal
        return trjs_normalized_centered, min_trjs, max_trjs, goal

    def unormalize(self, trjs):
        trjs_uncentered = trjs + self.goal
        trjs_unnormalized_uncentered = trjs_uncentered * ((self.max_trjs - self.min_trjs)) + self.min_trjs
        return trjs_unnormalized_uncentered


if __name__ == "__main__":
    from torch.utils.data import DataLoader

    ##### S2_models ####
    filename = 'CShape'
    device = torch.device('cpu')

    lasa = LASA(filename, PLOT=True)
    train_dataloader = DataLoader(lasa.dataset, batch_size=5, shuffle=True)

    for x,y in train_dataloader:
        print(x)
