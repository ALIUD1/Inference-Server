import redis
import struct
import uuid
from PIL import Image
import io
import torch
from torchvision import models
import time

print("model loaded")
#loading resnet18 and setting it from training to evaluation mode
resnet18 = models.resnet18(weights = models.ResNet18_Weights.DEFAULT)
preprocess = models.ResNet18_Weights.DEFAULT.transforms()
resnet18.eval()
torch.set_num_threads(1)
print(torch.get_num_threads())
#redis functions

r = redis.Redis(host = 'localhost', port = 6379, db = 0)

def pop_from_queue():
    while True:
        payload = r.blpop("jobs", timeout = 1)
        wait_time = 0.2
        if payload is None:
            continue
        else:
            start = time.perf_counter()
            counter = 1
            job_ids = [payload[1]]
            while time.perf_counter() - start < wait_time and counter < 8:
                job = r.lpop("jobs")
                if job is None:
                    continue
                else:
                    job_ids.append(job)
                    counter += 1
            batch = []
        for job_id in job_ids:
            image_bytes = r.get(job_id)
            r.delete(job_id)
            batch.append((job_id,image_bytes))
        work(resnet18, batch)
        

def push_response_to_queue(id, val):
    paylaod = struct.pack("<16sq", id, val)
    r.rpush("response", paylaod)

#worker functions
def work(model, batch):
    tensors = []
    ids = []
    for job_id, image_bytes in batch:
        img = io.BytesIO(image_bytes)
        img = Image.open(img).convert("RGB")
        img_tensor = preprocess(img)
        #img_tensor = img_tensor.unsqueeze(0) stack eliminates the need for it 
        tensors.append(img_tensor)
        ids.append(job_id)
    
    full_tensor = torch.stack(tensors)
    #print(img_tensor.shape)
    with torch.no_grad():
        predictions = model(full_tensor)
    for i, job_id in enumerate(ids):
        prediction = predictions[i]
        predicted = prediction.argmax().item()
        push_response_to_queue(job_id, predicted)


if __name__ == "__main__":
    pop_from_queue()

