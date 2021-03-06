'''
input: outputs from ancillary module and primary module of weak set
output: full label of weak set
Self-correction module refines predictions generated by the ancillary model and the current primary model for the weak set.
'''
import torch
import torch.nn as nn
import torch.nn.functional as F

class selfcorrModel(nn.Module):
    def __init__(self, args, alpha):
        super(selfcorrModel, self).__init__()
        
        self.method = args.self_correction_method
        self.alpha = alpha
        
        self.comb1 = nn.Sequential(
            nn.Linear(in_features=2,out_features=1),
            nn.ReLU())
        self.comb2 = nn.Sequential(
            nn.Linear(in_features=2,out_features=1),
            nn.ReLU())
        
    def forward(self, prim_pred, ancl_pred, prim_duration, ancl_duration):
        #prim/ancl_pred: batch_size*max_len*n_classes
        #prim/ancl_duration: batch_size*(max_len+1)
        if self.method == 'linear':
            self_corr_label = []
            for i in range(prim_pred.shape[1]):
                self_corr_label.append(F.softmax(torch.pow(prim_pred[:, i, :], 1/(self.alpha+1))*torch.pow(ancl_pred[:, i, :], self.alpha/(self.alpha+1)), 1))
            self_corr_duration = torch.pow(prim_duration, 1/(self.alpha+1))*torch.pow(ancl_duration, self.alpha/(self.alpha+1)) if torch.min(ancl_duration) > 1e-3 and torch.min(prim_duration) > 1e-3 else ancl_duration
            #this is to avoid exploding gradient if one element is too small, however,after the first epoches, duration should be big enough (at least bigger than 1) so that it will not damage the result. 
            return torch.stack(self_corr_label, 1), self_corr_duration #batch_size*max_len*n_classes, batch_size*(max_len+1)
        
        else: #auto
            self_corr_label = []
            for i in range(prim_pred.shape[1]):
                self_corr_label.append(F.softmax(self.comb1(torch.stack((prim_pred[:, i, :], ancl_pred[:, i, :]), 1).permute(0, 2, 1)).squeeze(), 1))
            self_corr_duration = self.comb2(torch.stack((prim_duration, ancl_duration), 2)).squeeze()
            return torch.stack(self_corr_label, 1), self_corr_duration #batch_size*max_len*n_classes, batch_size*(max_len+1)
