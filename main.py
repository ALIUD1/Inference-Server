from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import torch
from torchvision import models
from PIL import Image
import io

#loading resnet18 and setting it from training to evaluation mode
resnet18 = models.resnet18(weights = models.ResNet18_Weights.DEFAULT)
preprocess = models.ResNet18_Weights.DEFAULT.transforms()
resnet18.eval()


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

app = FastAPI()

@app.post("/")
async def predict_img(file: UploadFile):
    content = await file.read()
    img = io.BytesIO(content)

    
    return {"Category Number": test_resnet(resnet18, img)}


if __name__ == "__main__":
    #test_resnet(resnet18)
    print("hello world")