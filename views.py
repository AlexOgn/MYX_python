import os
from flask import Blueprint, request, send_file
from PIL import Image
from exif import Image as exif_image

views = Blueprint("views", "views")

UPLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)) + "\\upload")

def file_exists(filename):
    return os.path.exists(UPLOAD + "\\" + filename)

def to_decimal(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees

    return decimal_degrees

def get_gps(filename):
    with open(UPLOAD + "\\" + filename, 'rb') as image_file:
        image = exif_image(image_file)

    return {
        "lat": to_decimal(image.gps_latitude, image.gps_latitude_ref),
        "lon": to_decimal(image.gps_longitude, image.gps_longitude_ref)
    }

def get_box(point1, point2):
    return {
        "top": point1['lat'] if point1['lat'] > point2['lat'] else point2['lat'],
        "bottom": point1['lat'] if point1['lat'] < point2['lat'] else point2['lat'],
        "right": point1['lon'] if point1['lon'] > point2['lon'] else point2['lon'],
        "left": point1['lon'] if point1['lon'] < point2['lon'] else point2['lon'],
    }

def is_in_box(box, point):
    return (point['lat'] >= box['bottom'] and point['lat'] <= box['top']
    and point['lon'] >= box['left'] and point['lon'] <= box['right'])

@views.route("/uploadImage", methods=["POST"])
def uploadImage():
    if 'image' not in request.files:
        return {"error": "No file given"}, 400

    file = request.files['image']

    if file.filename == '':
        return {"error": "No selected file"}, 400

    if file:
        file.save(os.path.join(UPLOAD, file.filename))

    return {"status": 200}, 200
    
@views.route("/getImage", methods=["GET"])
def getImage():
    imageName = request.args.get("image")

    if not file_exists(imageName):
        return {"status": "Not Found"}, 404

    return send_file(UPLOAD + "\\" + imageName), 200

@views.route("/getThumbnail", methods=["GET"])
def getThumbnail():
    imageName = request.args.get("image")

    if file_exists("_" + imageName):
        return send_file(UPLOAD + "\\_" + imageName)
    
    if not file_exists(imageName):
        return {"error": "Not Found"}, 404
    
    image = Image.open(UPLOAD + "\\" + imageName)
    new_image = image.resize((256, 256))
    new_image.save(UPLOAD + "\\_" + imageName)

    return send_file(UPLOAD + "\\_" + imageName)

@views.route("/deleteImage", methods=["DELETE"])
def deleteImage():
    imageName = request.args.get("image")

    if file_exists("_" + imageName):
        os.remove(UPLOAD + "\\_" + imageName)
    
    if file_exists(imageName):
        os.remove(UPLOAD + "\\" + imageName)

    return {"status": 200}, 200

@views.route("/box", methods=["GET"])
def box():
    point1 = {"lat": float(request.args.get("lat1")), "lon": float(request.args.get("lon1"))}
    point2 = {"lat": float(request.args.get("lat2")), "lon": float(request.args.get("lon2"))}
    
    box = get_box(point1, point2)

    files = os.listdir(UPLOAD)
    return_files = []
    for file in files:
        if file.startswith("_"):
            continue

        gps = get_gps(file)

        if is_in_box(box, gps):
            return_files.append(file)


    return return_files, 200
