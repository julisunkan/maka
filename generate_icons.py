
from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
os.makedirs('static/icons', exist_ok=True)

# Icon sizes
sizes = [72, 96, 128, 144, 152, 192, 384, 512]
maskable_sizes = [192, 512]

def create_icon(size, filename, maskable=False):
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create gradient background (blue theme)
    for y in range(size):
        r = int(13 + (66 - 13) * y / size)
        g = int(110 + (133 - 110) * y / size)
        b = int(253 + (253 - 253) * y / size)
        draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b))
    
    # Add play circle icon
    if maskable:
        # Maskable icons need safe zone (80% of canvas)
        padding = size * 0.1
        icon_size = size * 0.8
    else:
        padding = size * 0.15
        icon_size = size * 0.7
    
    # Draw circle
    circle_center = size // 2
    circle_radius = icon_size // 2
    draw.ellipse(
        [circle_center - circle_radius, circle_center - circle_radius,
         circle_center + circle_radius, circle_center + circle_radius],
        fill='white', outline='white', width=int(size * 0.02)
    )
    
    # Draw play triangle
    triangle_size = icon_size * 0.4
    triangle_offset_x = circle_center + triangle_size * 0.15
    triangle_offset_y = circle_center
    
    triangle_points = [
        (triangle_offset_x - triangle_size * 0.3, triangle_offset_y - triangle_size * 0.5),
        (triangle_offset_x - triangle_size * 0.3, triangle_offset_y + triangle_size * 0.5),
        (triangle_offset_x + triangle_size * 0.4, triangle_offset_y)
    ]
    draw.polygon(triangle_points, fill='#0d6efd')
    
    # Save icon
    img.save(f'static/icons/{filename}', 'PNG', optimize=True)
    print(f'Created {filename}')

# Generate regular icons
for size in sizes:
    create_icon(size, f'icon-{size}x{size}.png')

# Generate maskable icons
for size in maskable_sizes:
    create_icon(size, f'maskable-icon-{size}x{size}.png', maskable=True)

print('All icons generated successfully!')
