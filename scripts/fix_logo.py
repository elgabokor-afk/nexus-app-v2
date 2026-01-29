from PIL import Image
import os

def remove_black_background(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # If pixel is essentially black (allowing for slight noise), make it transparent
        if item[0] < 15 and item[1] < 15 and item[2] < 15:
            new_data.append((255, 255, 255, 0)) # Transparent
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved transparent logo to {output_path}")

# Use the generated logo path
original_logo = r"C:\Users\NPC2\.gemini\antigravity\brain\0bb435d3-2b93-42d7-afb4-1b827f556fa8\nexus_ai_crypto_minimalist_1769640465156.png"
target_path = r"c:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2\public\logo.png"

remove_black_background(original_logo, target_path)
