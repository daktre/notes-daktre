---
title: Combine images into one PDF
category: Images
tags:
  - code-tutor
  - macos
  - terminal
tools:
  - python3
  - pip
  - venv
  - nano
level: beginner
draft: false
review: published
created: 2026-11-07
---
### Scenario
Converting multiple downloaded images into a single PDF document natively on macOS without needing third-party GUI software.

### The code
```python
from PIL import Image

image_files = [
    "input_image_1.jpeg",
    "input_image_2.jpeg",
    "input_image_3.jpeg"
]
output_pdf = "output_document.pdf"

first_image = Image.open(image_files[0]).convert("RGB")
additional_images = [Image.open(f).convert("RGB") for f in image_files[1:]]

first_image.save(
    output_pdf,
    save_all=True,
    append_images=additional_images
)
print(f"Success! Created {output_pdf}")
