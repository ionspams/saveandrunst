import streamlit as st
from PIL import Image
import numpy as np
import io

# Function to concatenate images
def concatenate_images(images, direction='horizontal'):
    if direction == 'horizontal':
        # Find the maximum height
        max_height = max(image.height for image in images)
        # Calculate the total width
        total_width = sum(image.width for image in images)
        # Create a new blank image with the total width and maximum height
        concatenated_image = Image.new('RGB', (total_width, max_height))
        # Paste each image next to each other
        x_offset = 0
        for image in images:
            concatenated_image.paste(image, (x_offset, 0))
            x_offset += image.width
    else:  # Vertical concatenation
        # Find the maximum width
        max_width = max(image.width for image in images)
        # Calculate the total height
        total_height = sum(image.height for image in images)
        # Create a new blank image with the total height and maximum width
        concatenated_image = Image.new('RGB', (max_width, total_height))
        # Paste each image below each other
        y_offset = 0
        for image in images:
            concatenated_image.paste(image, (0, y_offset))
            y_offset += image.height

    return concatenated_image

# Streamlit app
st.title("Image Files Concatenator")

# Image upload
uploaded_files = st.file_uploader("Choose images to concatenate", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

# Concatenation direction
direction = st.radio("Concatenate direction", ('Horizontal', 'Vertical'))

if uploaded_files:
    images = [Image.open(file) for file in uploaded_files]
    cropped_images = []

    st.subheader("Crop Uploaded Images")

    for i, image in enumerate(images):
        st.image(image, caption=f"Original Image {i+1}", use_column_width=True)
        x_start = st.number_input(f"Crop X start for Image {i+1}", min_value=0, max_value=image.width, value=0)
        y_start = st.number_input(f"Crop Y start for Image {i+1}", min_value=0, max_value=image.height, value=0)
        x_end = st.number_input(f"Crop X end for Image {i+1}", min_value=0, max_value=image.width, value=image.width)
        y_end = st.number_input(f"Crop Y end for Image {i+1}", min_value=0, max_value=image.height, value=image.height)
        
        cropped_image = image.crop((x_start, y_start, x_end, y_end))
        cropped_images.append(cropped_image)
        st.image(cropped_image, caption=f"Cropped Image {i+1}", use_column_width=True)

    if st.button("Concatenate Images"):
        concatenated_image = concatenate_images(cropped_images, direction.lower())
        st.subheader("Concatenated Image")
        st.image(concatenated_image, use_column_width=True)
        
        # Save concatenated image to a file
        concatenated_image.save("concatenated_image.jpg")
        
        with open("concatenated_image.jpg", "rb") as file:
            st.download_button(label="Download Image", data=file, file_name="concatenated_image.jpg", mime="image/jpeg")

        # Generate PDF from concatenated image
        pdf_buffer = io.BytesIO()
        concatenated_image.save(pdf_buffer, format="PDF")
        pdf_buffer.seek(0)
        st.download_button(label="Download PDF", data=pdf_buffer, file_name="concatenated_image.pdf", mime="application/pdf")