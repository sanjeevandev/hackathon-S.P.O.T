import torch
import torchvision.models as models
import torchvision.transforms as transforms
import time
import numpy as np

device = torch.device("cpu")
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.to(device)

dummy_inputs = torch.randn(64, 3, 224, 224, device=device)
dummy_labels = torch.randint(0, 2, (64,), device=device)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = torch.nn.CrossEntropyLoss()

start = time.time()
for _ in range(5):
    optimizer.zero_grad()
    outputs = model(dummy_inputs)
    loss = criterion(outputs, dummy_labels)
    loss.backward()
    optimizer.step()

elapsed = time.time() - start
print(f"5 mini-batches of 64 images took {elapsed:.2f}s (Rate: {320/elapsed:.1f} img/s)")
