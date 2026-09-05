import fontforge
import sys

def trim_font(input_path, output_path):
    font = fontforge.open(input_path)
    
    for glyph in list(font.glyphs()):
        if not (32 <= glyph.unicode <= 126):
            font.removeGlyph(glyph)
            

    font.generate(output_path, bitmap_type='pcf')
    print(f"Successfully trimmed font saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fontforge -script trim_font.py <input.pcf> <output.pcf>")
        sys.exit(1)
        
    trim_font(sys.argv[1], sys.argv[2])
    
    