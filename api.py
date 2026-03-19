#!/usr/bin/env python3
"""
VSCO Downloader REST API
A simple API to extract raw image and video paths from VSCO posts.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, HttpUrl
from typing import List
from urllib.parse import urlparse
from curl_cffi import requests as cffi_requests
from vsco import get_links

app = FastAPI(
    title="VSCO Downloader API",
    description="Extract raw image and video paths from VSCO posts",
    version="2.0.1",
)


class VscoUrlRequest(BaseModel):
    url: HttpUrl
    get_video_thumbnails: bool = True


class VscoUrlResponse(BaseModel):
    urls: List[str]


@app.get("/")
def root():
    return {"message": "VSCO Downloader API", "version": "2.0.1"}


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers/proxies."""
    return {"status": "ok", "version": "2.0.1"}


@app.post("/extract", response_model=VscoUrlResponse)
def extract_urls(request: VscoUrlRequest):
    """
    Extract direct image/video URLs from a VSCO post URL.
    
    - **url**: The VSCO post URL
    - **get_video_thumbnails**: Whether to include video thumbnails (default: True)
    
    Returns a list of direct media URLs.
    """
    try:
        urls = get_links(str(request.url), get_video_thumbnails=request.get_video_thumbnails)
        if not urls:
            raise HTTPException(status_code=404, detail="No media URLs found or failed to extract")
        return VscoUrlResponse(urls=urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting URLs: {str(e)}")


@app.get("/extract")
def extract_urls_get(url: str, get_video_thumbnails: bool = True):
    """
    Extract direct image/video URLs from a VSCO post URL (GET method).
    
    - **url**: The VSCO post URL (query parameter)
    - **get_video_thumbnails**: Whether to include video thumbnails (default: True)
    
    Returns a list of direct media URLs.
    """
    try:
        urls = get_links(url, get_video_thumbnails=get_video_thumbnails)
        if not urls:
            raise HTTPException(status_code=404, detail="No media URLs found or failed to extract")
        return VscoUrlResponse(urls=urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting URLs: {str(e)}")


IMAGE_REQUEST_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
    "Referer": "https://vsco.co/",
}

ALLOWED_IMAGE_HOSTS = [
    "im.vsco.co",
    "img.vsco.co",
    "image-aws-us-west-2.vsco.co",
    "image.vsco.co",
]


@app.get("/download")
def download_image(url: str):
    """
    Download/proxy an image from VSCO's CDN using curl_cffi to bypass Cloudflare.
    
    - **url**: The direct VSCO image URL (e.g., https://im.vsco.co/...)
    
    Returns the raw image bytes with appropriate content type.
    """
    try:
        parsed = urlparse(url)
        if parsed.hostname not in ALLOWED_IMAGE_HOSTS:
            raise HTTPException(status_code=400, detail="Only VSCO image URLs are allowed")
        
        headers = {**IMAGE_REQUEST_HEADER, "Host": parsed.hostname}
        response = cffi_requests.get(url, headers=headers, impersonate="chrome131", allow_redirects=True)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch image: HTTP {response.status_code}"
            )
        
        content_type = response.headers.get("content-type", "image/jpeg")
        
        # Determine filename from URL path
        path_parts = parsed.path.rstrip("/").split("/")
        filename = path_parts[-1] if path_parts else "vsco_image.jpg"
        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            ext = content_type.split("/")[-1].replace("jpeg", "jpg") if "/" in content_type else "jpg"
            filename = f"{filename}.{ext}"
        
        return Response(
            content=response.content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "public, max-age=31536000, immutable",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading image: {str(e)}")
