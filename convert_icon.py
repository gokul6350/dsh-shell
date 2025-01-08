from PIL import Image

# Open the PNG image
img = Image.open('logo.png')

# Convert and save as ICO
img.save('logo.ico', format='ICO') 