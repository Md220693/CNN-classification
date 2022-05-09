# -*- coding: utf-8 -*-
"""CNN_Classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1K_zajfv2sk_QEAUjm-MMnMRre_UjN5ml
"""

#Loading Dataset from Googledrive
from google.colab import drive 
drive.mount('/content/gdrive')

# Now extracting directries from zipfile
from zipfile import ZipFile
file_name="/content/gdrive/MyDrive/Places/places.zip"
with ZipFile(file_name,'r') as zip:
  zip.extractall()
  print('Done')

import os
dest_dir = "./places"
os.listdir(dest_dir)

#Load libraries
import os
import numpy as np
import torch
import glob
import torch.nn as nn
from torchvision.transforms import transforms
from torch.utils.data import DataLoader
from torch.optim import Adam
from torch.autograd import Variable
import torchvision
import pathlib

#Transforms
transforms=  transforms.Compose([
    transforms.Resize((64,64)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),  #0-255 to 0-1, numpy to tensors
    transforms.Normalize([0.5,0.5,0.5], # 0-1 to [-1,1] , formula (x-mean)/std
                        [0.5,0.5,0.5])
])

# datasets
#Path for training and testing directory
train_path='/content/places/seg_train'
test_path='/content/places/seg_test' 
train_set=torchvision.datasets.ImageFolder(train_path,transform=transforms)
test_set=torchvision.datasets.ImageFolder(test_path,transform=transforms)

train_loader=DataLoader(
    torchvision.datasets.ImageFolder(train_path,transform=transforms),
    batch_size=64, shuffle=True
)
test_loader=DataLoader(
    torchvision.datasets.ImageFolder(test_path,transform=transforms),
    batch_size=32, shuffle=True
)

#categories
root=pathlib.Path(train_path)
classes=sorted([j.name.split('/')[-1] for j in root.iterdir()])

print(classes)

#checking for device
device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

class Net(nn.Module):
    def __init__(self,num_classes=6):
        super(Net,self).__init__()
        
        #Output size after convolution filter
        #((w-f+2P)/s) +1
        
        #Input shape= (256,3,150,150)
        
        self.conv1=nn.Conv2d(in_channels=3,out_channels=12,kernel_size=3,stride=1,padding=1)
        nn.Flatten()
        #Shape= (256,12,150,150)
        self.bn1=nn.BatchNorm2d(num_features=12)
        #Shape= (256,12,150,150)
        self.relu1=nn.ReLU()
        #Shape= (256,12,150,150)
        
        self.pool=nn.MaxPool2d(kernel_size=2)
        #Reduce the image size be factor 2
        #Shape= (256,12,75,75)
        
        
        self.conv2=nn.Conv2d(in_channels=12,out_channels=20,kernel_size=3,stride=1,padding=1)
        nn.Flatten()
        #Shape= (256,20,75,75)
        self.relu2=nn.ReLU()
        #Shape= (256,20,75,75)
        
        
        
        self.conv3=nn.Conv2d(in_channels=20,out_channels=32,kernel_size=3,stride=1,padding=1)
        nn.Flatten()
        #Shape= (256,32,32,32)
        self.bn3=nn.BatchNorm2d(num_features=32)
        #Shape= (256,32,32,32)
        self.relu3=nn.ReLU()
        #Shape= (256,32,32,32)

        #Classification:
        nn.Conv2d(in_channels=32,out_channels=6,kernel_size=2,stride=1,padding=0)
        
        #Fully Connected layer:
        self.fc=nn.Linear(in_features=32 * 32 * 32,out_features=num_classes)
        
        
        
        #Feed forwad function
        
    def forward(self,input):
        output=self.conv1(input)
        output=self.bn1(output)
        output=self.relu1(output)
            
        output=self.pool(output)
            
        output=self.conv2(output)
        output=self.relu2(output)
            
        output=self.conv3(output)
        output=self.bn3(output)
        output=self.relu3(output)

 #Above output will be in matrix form, with shape (256,32,75,75)
            
        output=output.view(-1,32*32*32)
            
            
        output=self.fc(output)
            
        return output


#def get_num_correct(preds, labels):
 #       return preds.argmax(dim=1).eq(labels).sum().item()

model=Net(num_classes=6).to(device)

#Optmizer and loss function
optimizer=Adam(model.parameters(),lr=0.001,weight_decay=0.0001)
loss_function=nn.CrossEntropyLoss()
criterion = loss_function

#calculating the size of training and testing images
train_count=len(glob.glob(train_path+'/**/*.jpg'))
test_count=len(glob.glob(test_path+'/**/*.jpg'))
print(train_count,test_count)

#Model training and saving best model

best_accuracy=0.0
num_epochs=10
for epoch in range(num_epochs):
    
    #Evaluation and training on training dataset
    model.train()
    train_accuracy=0.0
    train_loss=0.0
    
    for i, (images,labels) in enumerate(train_loader):
        if torch.cuda.is_available():
            images=Variable(images.cuda())
            labels=Variable(labels.cuda())
            
        optimizer.zero_grad()
        
        outputs=model(images)
        loss=loss_function(outputs,labels)
        loss.backward()
        optimizer.step()
        
        
        train_loss+= loss.cpu().data*images.size(0)
        _,prediction=torch.max(outputs.data,1)
        
        train_accuracy+=int(torch.sum(prediction==labels.data))
        
    train_accuracy=train_accuracy/train_count
    train_loss=train_loss/train_count
    
    
    # Evaluation on testing dataset
    model.eval()
    
    test_accuracy=0.0
    for i, (images,labels) in enumerate(test_loader):
        if torch.cuda.is_available():
            images=Variable(images.cuda())
            labels=Variable(labels.cuda())
            
        outputs=model(images)
        _,prediction=torch.max(outputs.data,1)
        test_accuracy+=int(torch.sum(prediction==labels.data))
    
    test_accuracy=test_accuracy/test_count
    
    
    print('Epoch: '+str(epoch)+' Train Loss: '+str(train_loss)+' Train Accuracy: '+str(train_accuracy)+' Test Accuracy: '+str(test_accuracy))
    
    #Save the best model
    if test_accuracy>best_accuracy:
        torch.save(model.state_dict(),'best_checkpoint.model')
        best_accuracy=test_accuracy

"""**Prediction Analysis:**"""

checkpoint=torch.load('best_checkpoint.model')
model=Net(num_classes=6)
model.load_state_dict(checkpoint)
model.eval()

#prediction function
def prediction(img_path,transformer):
    
    image=Image.open(img_path)
    
    image_tensor=transformer(image).float()
    
    
    image_tensor=image_tensor.unsqueeze_(0)
    
    if torch.cuda.is_available():
        image_tensor.cuda()
        
    input=Variable(image_tensor)
    
    
    output=model(input)
    
    index=output.data.numpy().argmax()
    
    pred=classes[index]
    
    return pred

pred_path='/content/places/seg_pred'
images_path=glob.glob(pred_path+'/*.jpg')

from torchvision.transforms import transforms
#Transforms
transformer=transforms.Compose([
    transforms.Resize((64,64)),
    transforms.ToTensor(),  #0-255 to 0-1, numpy to tensors
    transforms.Normalize([0.5,0.5,0.5], # 0-1 to [-1,1] , formula (x-mean)/std
                        [0.5,0.5,0.5])
])

from PIL import Image
pred_dict={}

for i in images_path:
    pred_dict[i[i.rfind('/')+1:]]=prediction(i,transformer)

pred_dict