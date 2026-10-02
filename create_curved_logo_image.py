from PIL import Image, ImageDraw, ImageFont
import math

# Configuration
TEXT = "UNIVERSITY OF SINDH, JAMSHORO"
LOGO_PATH = "thesis_images/uni logo.jpg"
OUTPUT_PATH = "thesis_images/header_logo_curved.png"
FONT_SIZE = 40  # Adjust based on image resolution
RADIUS = 300    # Radius of the arc
CENTER_X = 400  # Center X for the Arc
CENTER_Y = 320  # Center Y for the Arc (below the baseline)
ANGLE_SPREAD = 140 # Total angle for text in degrees

def create_curved_text_image():
    # Load Logo
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
    except FileNotFoundError:
        print(f"Error: {LOGO_PATH} not found.")
        return

    # Resize logo if needed (e.g. to width ~ 200px)
    target_logo_width = 250
    w_percent = (target_logo_width / float(logo.size[0]))
    h_size = int((float(logo.size[1]) * float(w_percent)))
    logo = logo.resize((target_logo_width, h_size), Image.Resampling.LANCZOS)

    # Canvas Size
    width = 800
    height = 400 # Adjusted height
    
    # Create base image (transparent background)
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Load Font
    try:
        # Try to load Times New Roman Bold
        font = ImageFont.truetype("timesbd.ttf", FONT_SIZE) 
    except IOError:
        try:
             font = ImageFont.truetype("calibrib.ttf", FONT_SIZE) # Fallback
        except IOError:
             font = ImageFont.load_default()
             print("Warning: Using default font.")

    # Calculate Arc Text Positions
    # Center of arc is (CENTER_X, CENTER_Y). Text is placed above this center.
    # Angles: 270 is straight up (12 o'clock). 
    # We want text centered around 270 (top).
    # Spread is ANGLE_SPREAD. So from (270 - spread/2) to (270 + spread/2)
    # Wait, usually arc text is plotted: center (cx, cy) is below the text baseline.
    # Radius R goes up to the baseline.
    
    start_angle = 270 - (ANGLE_SPREAD / 2)
    # end_angle = 270 + (ANGLE_SPREAD / 2)
    
    # We need to map characters to angles
    # Simple explicit char placement
    num_chars = len(TEXT)
    if num_chars > 0:
        angle_step = ANGLE_SPREAD / (num_chars - 1)
    
    # Draw Text
    for i, char in enumerate(TEXT):
        # Angle for this char (in degrees, convert to radians)
        angle_deg = start_angle + (i * angle_step)
        angle_rad = math.radians(angle_deg)
        
        # Position: 
        # x = cx + R * cos(angle)
        # y = cy + R * sin(angle)
        # BUT standard math 0 is Right (3 o'clock), 90 is Bottom (6 o'clock) if y increases down?
        # In PIL coordinate system: (0,0) top-left.
        # Math: 0 is East. 270 is South (-90 is South). Wait.
        # Let's say center is (400, 350).
        # We want top arc. So angles are around -90 (270).
        # x = cx + R * cos(angle)
        # y = cy + R * sin(angle)
        
        # Adjust angle: input is "clock position" where 0 is up? No.
        # Let's use standard trig: 0 is Right. -90 is Up.
        # Spread is creating an arc like a frown (Top of circle).
        # Angles should range from approx -160 to -20 (centered on -90).
        
        # Re-calc angles
        mid_angle = -90
        total_spread = 100 # degrees
        start_a = mid_angle - (total_spread / 2)
        step_a = total_spread / (num_chars - 1)
        
        theta_deg = start_a + (i * step_a)
        theta = math.radians(theta_deg)
        
        # Position on circle
        x = CENTER_X + RADIUS * math.cos(theta)
        y = CENTER_Y + RADIUS * math.sin(theta)
        
        # Rotation fo char
        # Tangent to circle is perpendicular to radius.
        # Adding 90 degrees to the theta.
        # PIL rotate is counter-clockwise?
        # We need to rotate the char image.
        
        char_img = Image.new('RGBA', (FONT_SIZE*2, FONT_SIZE*2), (255,255,255,0))
        char_draw = ImageDraw.Draw(char_img)
        
        # Draw char centered in temp image
        # Using specific anchor 'mm' (middle middle) if supported, else arithmetic
        try:
             char_draw.text((FONT_SIZE, FONT_SIZE), char, font=font, fill="black", anchor="mm")
        except:
             char_draw.text((FONT_SIZE, FONT_SIZE), char, font=font, fill="black")
        
        # Rotate
        # Angle to upright is -90 - theta_deg?
        # Text at top (-90) should be upright (0 rotation).
        # Text at left (-180) should rotate -90?
        rotation = -(theta_deg + 90) 
        
        rotated_char = char_img.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=1)
        
        # Paste into main image
        # Center of pasted image at (x,y)
        w_r, h_r = rotated_char.size
        img.paste(rotated_char, (int(x - w_r/2), int(y - h_r/2)), rotated_char)

    # Paste Logo
    # Center logo horizontally below the arc
    # If Center Y of arc (origin) is 320, logo top should be around 110?
    # No, radius is 300. Top of arc is at y = 320 - 300 = 20.
    # Text is around y=20.
    # Logo should be below text. y ~ 60?
    
    logo_x = int((width - logo.size[0]) / 2)
    logo_y = 90 # Manually tuned
    img.paste(logo, (logo_x, logo_y), logo)

    # Save
    img.save(OUTPUT_PATH)
    print(f"Saved {OUTPUT_PATH}")

if __name__ == "__main__":
    create_curved_text_image()
