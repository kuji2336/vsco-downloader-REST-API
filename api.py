#!/usr/bin/env python3
"""
VSCO Downloader REST API
A simple API to extract raw image and video paths from VSCO posts.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List
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
