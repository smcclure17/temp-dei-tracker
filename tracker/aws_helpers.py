import asyncio
import io
import base64
import aioboto3
from PIL import Image
from botocore.exceptions import NoCredentialsError

async def compress_png_async(png_bytes, quality=80):
    """
    Compress a PNG image asynchronously.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, compress_png, png_bytes, quality)

def compress_png(png_bytes, quality=80):
    """
    Compress a PNG image by reducing its quality.
    """
    with Image.open(io.BytesIO(png_bytes)) as img:
        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True, quality=quality)
        return output.getvalue()

async def upload_png_to_s3_async(png: str | bytes, bucket_name, object_name, region="us-east-1"):
    if isinstance(png, str):
        png = base64.b64decode(png)

    session = aioboto3.Session()
    async with session.client("s3", region_name=region) as s3_client:
        try:
            compressed_png = await compress_png_async(png)

            # Upload asynchronously
            await s3_client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=compressed_png,
                ContentType="image/png",
            )
            print(f"File uploaded successfully to {bucket_name}/{object_name}")
            return f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"
        except NoCredentialsError:
            print("Credentials not available.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None