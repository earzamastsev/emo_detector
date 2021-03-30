from facenet_pytorch import MTCNN, extract_face
import torch
from torchvision import transforms as T

class EmoDetector:
    def __init__(self, device="cpu"):
        self.device = device
        self.model = torch.load('models/resnet34_ft_albu_imb_4.pth', map_location=torch.device(device))
        self.model = self.model.module
        self.model.to(device)
        self.mtcnn = MTCNN(select_largest=True, margin=5, post_process=False, device=device)
        self.transform = T.Compose([
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        self.class_names = ['anger',
                       'contempt',
                       'disgust',
                       'fear',
                       'happy',
                       'neutral',
                       'sad',
                       'surprise',
                       'uncertain']

    def _image_preprocessing(self, img):
        return self.transform(img / 255)

    def _get_face(self, img):
        bbox = self.mtcnn.detect(img)[0]
        if bbox is None:
            return {"status": "error",
                    "description": "No face detected"}
        else:
            bbox = bbox[0].astype(int).tolist()
            face_image = extract_face(img, bbox, image_size=224)
            return { "status": "ok",
                    "face": face_image,
                    "bbox": bbox }

    def predict(self, img):
        result = {}
        face_data = self._get_face(img)
        if face_data["status"] == "ok":
            face = self._image_preprocessing(face_data['face'])
            face = face.to(self.device)
            _, preds = self.model(face.unsqueeze(0)).max(1)
            result["emotion"] = self.class_names[preds]
            result["bbox"] = face_data["bbox"]
            result["status"] = "ok"
            return result
        else:
            result["status"] = "error"
            result["description"] = face_data["description"]
            return result
