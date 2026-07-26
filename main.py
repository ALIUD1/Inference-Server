from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import torch
from torchvision import models
from PIL import Image
import io
import time

print("model loaded")
#loading resnet18 and setting it from training to evaluation mode
resnet18 = models.resnet18(weights = models.ResNet18_Weights.DEFAULT)
preprocess = models.ResNet18_Weights.DEFAULT.transforms()
resnet18.eval()

pending_jobs = {} 



@asynccontextmanager
async def lifespan(app: FastAPI):
    reader = asyncio.create_task(response_reader())
    yield
    

app = FastAPI(lifespan = lifespan)

@app.post("/")
async def predict_img(file: UploadFile):
    start = time.perf_counter()
    content = await file.read()
    img = io.BytesIO(content)
    category_num = test_resnet(resnet18, img)
    end = time.perf_counter()
    return {
        "Category_Number": category_num,
        "Server_Rate": end - start,
            }


if __name__ == "__main__":
    #test_resnet(resnet18)
    print("hello world")
    test_batching(resnet18,"pgiff.webp")


"""

#opens petergriffin image, turns into tensor, gives extra dimension since resnet18 needs 4 and then runs model and predicted number 652 (military uniform)
def test_resnet(resnet18, full_image):
    img = Image.open(full_image).convert("RGB")
    img_tensor = preprocess(img)
    img_tensor = img_tensor.unsqueeze(0)
    print(img_tensor.shape)
    with torch.no_grad():
        predictions = resnet18(img_tensor)

    predicted = predictions.argmax(dim=1).item()
    return predicted
#img.show()

def test_batching(resnet18, full_image):
    img = Image.open(full_image).convert("RGB")
    img_tensor = preprocess(img)
    warmup = resnet18(img_tensor.unsqueeze(0))
    for i in [1,2,4,8,16,32]:
        full_tensor = torch.stack([img_tensor]*i)
        print(full_tensor.shape)
        with torch.no_grad():
            diff = float('inf')
            for perf_counter in range(10):
                start = time.perf_counter() 
                predictions = resnet18(full_tensor)
                end = time.perf_counter()
                diff = min(end-start,diff)
            print(f"Time taken for batch {i} = {diff}, time taken for each image = {(diff)/i} \n")

""""
