import Redis
import struct
import uuid
from PIL import Image
import io

print("model loaded")
#loading resnet18 and setting it from training to evaluation mode
resnet18 = models.resnet18(weights = models.ResNet18_Weights.DEFAULT)
preprocess = models.ResNet18_Weights.DEFAULT.transforms()
resnet18.eval()

#redis functions

r = redis.Redis(host = 'localhost', port = 6379, db = 0)

def pop_from_queue():
    while True:
        payload = r.blpop("jobs", timeout = 1)[1]
        if payload is None:
            continue
        job_id = payload[1]
        image_bytes = r.get(job_id)
        r.delete(job_id)
        work(resnet18, image_bytes, job_id)
        

def push_response_to_queue(id, val):
    paylaod = struct.pack("<16sq", id, val)
    r.rpush("response", paylaod)

#worker functions
def work(model, image_bytes,job_id):
    img = io.BytesIO(content)
    img_tensor = preprocess(img)
    img_tensor = img_tensor.unsqueeze(0)
    print(img_tensor.shape)
    with torch.no_grad():
        predictions = resnet18(img_tensor)

    predicted = predictions.argmax(dim=1).item()
    push_response_to_queue(job_id, predicted)


if __name__ == "__main__":
    print(r.ping())
    add_to_queue(b"hello world")


def get_job():
    while True:
