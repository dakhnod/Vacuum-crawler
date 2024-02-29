from PIL import Image, ImageDraw
import json
import time
import math
import io

def convert_map_data_to_png(map_data):
    dimensions = map_data['size']
    pixel_size = map_data['pixelSize']

    image_x_min = map_data['layers'][0]['dimensions']['x']['min']
    image_y_min = map_data['layers'][0]['dimensions']['y']['min']
    image_x_max = map_data['layers'][0]['dimensions']['x']['max']
    image_y_max = map_data['layers'][0]['dimensions']['y']['max']

    for layer in map_data['layers'][1:]:
        image_x_min = min(image_x_min, layer['dimensions']['x']['min'])
        image_y_min = min(image_y_min, layer['dimensions']['y']['min'])
        image_x_max = max(image_x_max, layer['dimensions']['x']['max'])
        image_y_max = max(image_y_max, layer['dimensions']['y']['max'])

    image_size_x = image_x_max - image_x_min
    image_size_y = image_y_max - image_y_min

    # image_size_x = dimensions['x']
    # image_size_y = dimensions['y']

    image = Image.new('RGBA', (image_size_x + 1, image_size_y + 1))

    for layer in map_data['layers']:
        pixels = layer['compressedPixels']
        index = 0
        while index < len(pixels):
            x = pixels[index] - image_x_min
            y = pixels[index + 1] - image_y_min
            count = pixels[index + 2]
            index += 3
            for i in range(count):
                try:
                    image.putpixel((x + i, y), (0, 0, 255))
                except Exception as e:
                    pass

    draw = ImageDraw.ImageDraw(image)

    radius = image_size_x / 120

    for entity in map_data['entities']:
        points = entity['points']
        entity_type = entity['type']
        color = {
            'robot_position': (255, 0, 0),
            'charger_location': (0, 255, 0),
            'path': (0, 0, 0)
        }.get(entity_type)
        if color is None:
            continue

        for i in range(len(entity['points'])):
            entity['points'][i] /= pixel_size

        for i in range(0, len(entity['points']), 2):
            entity['points'][i] -= image_x_min

        for i in range(1, len(entity['points']), 2):
            entity['points'][i] -= image_y_min

        if entity_type == 'path':
            draw.line(entity['points'], color, 1)
            continue

        draw.ellipse([
        (
            points[0] - radius,
            points[1] - radius,
        ), (
            points[0] + radius,
            points[1] + radius,
        )], color)

    output = io.BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()

    pixels = map_data['image']['pixels']

    for floor_pixel in pixels['floor']:
        image.putpixel((floor_pixel[0], floor_pixel[1]), (0, 0, 255))

    for obstacle_pixel in pixels['obstacle_strong']:
        image.putpixel((obstacle_pixel[0], obstacle_pixel[1]), (255, 255, 255))

    draw = ImageDraw.ImageDraw(image)

    divisor = 50
    subtractorX = map_data['image']['position']['left']
    subtractorY = map_data['image']['position']['top']

    pos_charger = (
        math.floor(map_data['charger'][0] / 50 - subtractorX),
        math.floor(map_data['charger'][1] / 50 - subtractorY)
    )

    pos_robot = (
        math.floor(map_data['robot'][0] / 50 - subtractorX),
        math.floor(map_data['robot'][1] / 50 - subtractorY)
    )

    radius = dimensions['width'] / 30 / 2

    draw.ellipse([
        (
            pos_charger[0] - radius,
            pos_charger[1] - radius,
        ), (
            pos_charger[0] + radius,
            pos_charger[1] + radius,
        )], (0, 255, 0))

    draw.ellipse([
        (
            pos_robot[0] - radius,
            pos_robot[1] - radius,
        ), (
            pos_robot[0] + radius,
            pos_robot[1] + radius,
        )], (255, 0, 0))

    path_points = map_data['path']['points']
    last_point = (path_points[0][0] / divisor - subtractorX, path_points[0][1] / divisor - subtractorY)
    for i in range(1, len(path_points)):
        point = (path_points[i][0] / divisor - subtractorX, path_points[i][1] / divisor - subtractorY)
        draw.line([last_point, point], (255, 255, 255), 1)
        last_point = point

    output = io.BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()
