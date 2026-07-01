import base64


class ImageEncoder:
    @classmethod
    def encode(cls, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")
