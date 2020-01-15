import numpy as np
import torch

result = np.load('test_result.pkl',allow_pickle=True)
id_lb,target = np.load('../../data/NTU-RGB-D/xsub/val_hi_label.pkl',allow_pickle=True)
list_result = list(result.keys())
list_target = []
for i in range(len(list_result)):
    # print(list_result[i],'##',id_lb[i])
    res = torch.tensor(result[list_result[i]])
    _, target_res = torch.max(res,0)
    # print(target_res.item(),'##',target[i])
    list_target.append(target_res.item())
# print(list_target)
saver = (target,list_target)
np.savetxt('res.csv',saver,delimiter=',',fmt='%i')
