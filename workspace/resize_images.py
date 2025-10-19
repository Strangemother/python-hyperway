#!/usr/bin/env python3
"""
Resize images in docs/images to maximum 1000px wide while maintaining aspect ratio.
"""
from pathlib import Path
from PIL import Image


def resize_image(image_path: Path, max_width: int = 1000, backup: bool = True):
    """
    Resize an image to max_width while maintaining aspect ratio.
    
    Args:
        image_path: Path to the image file
        max_width: Maximum width in pixels (default: 1000)
        backup: Create a backup of the original (default: True)
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Skip if already smaller than max_width
            if width <= max_width:
                print(f"✓ Skipping {image_path.name} ({width}x{height}) - already within limit")
                return
            
            # Calculate new dimensions
            aspect_ratio = height / width
            new_width = max_width
            new_height = int(new_width * aspect_ratio)
            
            print(f"↻ Resizing {image_path.name}: {width}x{height} → {new_width}x{new_height}")
            
            # Create backup if requested
            if backup:
                backup_path = image_path.with_suffix(f'.original{image_path.suffix}')
                if not backup_path.exists():
                    img.save(backup_path)
                    print(f"  ✓ Backup saved to {backup_path.name}")
            
            # Resize using high-quality Lanczos resampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save the resized image
            resized_img.save(image_path, optimize=True, quality=95)
            print(f"  ✓ Resized and saved")
            
    except Exception as e:
        print(f"✗ Error processing {image_path.name}: {e}")


def main():
    """Main function to resize all images in docs/images."""
    images_dir = Path(__file__).parent / "docs" / "images"
    
    if not images_dir.exists():
        print(f"Error: Directory {images_dir} does not exist")
        return
    
    # Find all PNG images
    image_files = sorted(images_dir.glob("*.png"))
    
    if not image_files:
        print(f"No PNG images found in {images_dir}")
        return
    
    print(f"Found {len(image_files)} PNG images in {images_dir}")
    print(f"Processing with max width: 1000px\n")
    
    for image_file in image_files:
        resize_image(image_file, max_width=1000, backup=True)
    
    print(f"\n✓ Done! Processed {len(image_files)} images")


if __name__ == "__main__":
    main()
