import asyncio
import base64
import cv2
import json
import js
import numpy as np
from pyodide.http import pyfetch


def get_coords():
    map = js.getMap()  # retrieve map from js
    latLng = map.getCenter()
    lon = latLng.lng
    lat = latLng.lat
    zoom = map.getZoom()
    return (lon, lat, zoom)


def get_map_dims():
    # retrieve from DOM, in js
    width = min(js.document.getElementById("map").clientWidth, 1280)
    height = min(js.document.getElementById("map").clientHeight, 1280)
    return (width, height)


async def click_corner(event):
    lon, lat, zoom = get_coords()
    width, height = get_map_dims()
    points = await click_py("corner", lon, lat, zoom, width, height)
    js.updateCorners(points)  # send points to js


async def click_edge(event):
    lon, lat, zoom = get_coords()
    width, height = get_map_dims()
    data_url = await click_py("edge", lon, lat, zoom, width, height)
    js.updateImage(data_url)  # send edges to js


async def click_contour(event):
    lon, lat, zoom = get_coords()
    width, height = get_map_dims()
    data_url = await click_py("contour", lon, lat, zoom, width, height)
    js.updateImage(data_url)  # send contours to js


def readb64(encoded_data):
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def bytes_to_data_url(img_bytes):
    return base64.b64encode(img_bytes).decode("ascii")


async def get_static_image_py(
    lon,
    lat,
    zoom,
    access_token=js.getToken(),  # retrieve access token from js
    bearing=0,
    pitch=0,
    username="mapbox",
    style_id="satellite-v9",
    overlay="",
    width=300,
    height=200,
    scale="",
):
    url = f"https://api.mapbox.com/styles/v1/{username}/{style_id}/static/{overlay}{lon},{lat},{zoom},{bearing},{pitch}/{width}x{height}{scale}?access_token={access_token}"
    response = await pyfetch(url=url, method="GET")
    return bytes_to_data_url(await response.bytes())


def array_to_geojson(arr):
    features = []
    for i in arr:
        features.append(
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Point",
                    "coordinates": [int(i[0][0]), int(i[0][1])],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


async def click_py(detection_type, lon, lat, zoom, width, height):
    static_img = await get_static_image_py(lon, lat, zoom, width=width, height=height)
    rgb_img = readb64(static_img)
    if detection_type == "corner":
        gray_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
        corners = cv2.goodFeaturesToTrack(
            gray_img, maxCorners=0, qualityLevel=0.05, minDistance=10
        )
        corners = np.uint32(corners)
        points = array_to_geojson(corners)
        return json.dumps(points)
    elif detection_type == "edge":
        blurred_img = cv2.blur(rgb_img, ksize=(3, 3))
        edges = cv2.Canny(image=blurred_img, threshold1=127, threshold2=127)
        _, buffer = cv2.imencode(".jpg", edges)
        data_url = bytes_to_data_url(buffer)
        return f"data:image/jpg;base64,{data_url}"
    elif detection_type == "contour":
        gray_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
        contour_image = np.zeros(gray_img.shape)
        _, thresh = cv2.threshold(gray_img, 127, 255, 0)
        contours_draw, _ = cv2.findContours(
            thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE
        )
        for c in contours_draw:
            cv2.drawContours(contour_image, [c], -1, (255, 255, 0), -1)
        _, buffer = cv2.imencode(".jpg", contour_image)
        data_url = bytes_to_data_url(buffer)
        return f"data:image/jpg;base64,{data_url}"
