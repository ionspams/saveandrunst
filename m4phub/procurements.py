import streamlit as st
import pandas as pd
from datetime import datetime
import base64
from PIL import Image, ImageEnhance, ImageFilter
import io
import numpy as np

# Initialize session state
if 'requests' not in st.session_state:
    st.session_state.requests = []

def send_email(subject, body, to_email):
    # This is a placeholder function. You'll need to implement actual email sending logic.
    st.write(f"Email sent to {to_email}")
    st.write(f"Subject: {subject}")
    st.write(f"Body: {body}")

def enhance_image(image):
    # Convert to grayscale
    image = image.convert('L')
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    # Apply sharpening filter
    image = image.filter(ImageFilter.SHARPEN)
    return image

def main():
    st.title("Procurement Request Management")

    # Sidebar for navigation
    page = st.sidebar.radio("Navigate", ["Submit Request", "View Requests", "Admin Panel"])

    if page == "Submit Request":
        submit_request()
    elif page == "View Requests":
        view_requests()
    elif page == "Admin Panel":
        admin_panel()

def submit_request():
    st.header("Submit a Procurement Request")

    # Custom HTML for better camera access
    st.markdown("""
    <style>
        #camera-container { width: 100%; max-width: 640px; margin: 0 auto; }
        #camera-feed { width: 100%; }
        #capture-btn { display: block; margin: 10px auto; }
    </style>
    <div id="camera-container">
        <video id="camera-feed" autoplay playsinline></video>
        <button id="capture-btn">Capture Document</button>
    </div>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        const video = document.getElementById('camera-feed');
        const canvas = document.getElementById('canvas');
        const captureBtn = document.getElementById('capture-btn');
        
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => {
                video.srcObject = stream;
            })
            .catch(error => {
                console.error('Error accessing camera:', error);
            });
        
        captureBtn.addEventListener('click', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg');
            window.parent.postMessage({type: 'camera_capture', image: imageData}, '*');
        });
    </script>
    """, unsafe_allow_html=True)

    # Guidelines for better document scanning
    st.markdown("""
    ### Guidelines for Better Document Scanning:
    1. Ensure good lighting - avoid shadows and glare.
    2. Place the document on a contrasting background.
    3. Keep the camera steady and parallel to the document.
    4. Capture the entire document within the frame.
    5. Focus on the document before capturing.
    """)

    # Form for submitting a request
    with st.form("procurement_request"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        link = st.text_input("Link (if available)")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        repeat_purchase = st.radio("Will this item or purchase likely be needed again?", ("Yes", "No"))
        
        if repeat_purchase == "Yes":
            frequency = st.selectbox("Frequency", ["Weekly", "Monthly", "Other"])
            if frequency == "Other":
                frequency_other = st.text_input("Specify frequency")
        
        price_per_item = st.number_input("Price per item (in Moldovan Lira)", min_value=0.0, format="%.2f")
        total_price = quantity * price_per_item
        st.write(f"Total Price: {total_price:.2f} Moldovan Lira")

        if total_price > 10000:
            st.warning("For purchases over 10,000 Moldovan Lira, please provide two more offers.")
            offer2_link = st.text_input("Second offer link")
            offer2_price = st.number_input("Second offer price", min_value=0.0, format="%.2f")
            offer3_link = st.text_input("Third offer link")
            offer3_price = st.number_input("Third offer price", min_value=0.0, format="%.2f")

        # File upload option
        uploaded_file = st.file_uploader("Upload a document (receipt, invoice, etc.)", type=["png", "jpg", "jpeg", "pdf"])

        submitted = st.form_submit_button("Submit Request")

        if submitted:
            if not title:
                st.error("Please enter a title for the request.")
            else:
                request = {
                    "title": title,
                    "description": description,
                    "link": link,
                    "quantity": quantity,
                    "repeat_purchase": repeat_purchase,
                    "price_per_item": price_per_item,
                    "total_price": total_price,
                    "status": "Pending",
                    "timestamp": datetime.now().isoformat()
                }
                if repeat_purchase == "Yes":
                    request["frequency"] = frequency_other if frequency == "Other" else frequency
                if total_price > 10000:
                    request["additional_offers"] = [
                        {"link": offer2_link, "price": offer2_price},
                        {"link": offer3_link, "price": offer3_price}
                    ]
                
                # Process uploaded file
                if uploaded_file is not None:
                    file_contents = uploaded_file.read()
                    request["file"] = file_contents
                    request["file_type"] = uploaded_file.type
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(io.BytesIO(file_contents))
                        enhanced_image = enhance_image(image)
                        buffered = io.BytesIO()
                        enhanced_image.save(buffered, format="JPEG")
                        request["enhanced_file"] = buffered.getvalue()

                st.session_state.requests.append(request)
                st.success("Request submitted successfully!")
                send_email("New Procurement Request", f"A new procurement request has been submitted: {title}", "admin@example.com")

    # Handle camera capture
    if st.session_state.get('camera_image'):
        image_data = base64.b64decode(st.session_state.camera_image.split(',')[1])
        image = Image.open(io.BytesIO(image_data))
        enhanced_image = enhance_image(image)
        st.image(enhanced_image, caption="Captured and Enhanced Document", use_column_width=True)
        
        if st.button("Use this image"):
            buffered = io.BytesIO()
            enhanced_image.save(buffered, format="JPEG")
            st.session_state.requests[-1]["file"] = buffered.getvalue()
            st.session_state.requests[-1]["file_type"] = "image/jpeg"
            st.session_state.requests[-1]["enhanced_file"] = buffered.getvalue()
            st.success("Image added to the request successfully!")

def view_requests():
    st.header("View Procurement Requests")

    if not st.session_state.requests:
        st.info("No requests submitted yet.")
    else:
        for i, request in enumerate(st.session_state.requests):
            with st.expander(f"Request: {request['title']}"):
                st.write(f"Description: {request['description']}")
                st.write(f"Quantity: {request['quantity']}")
                st.write(f"Total Price: {request['total_price']} Moldovan Lira")
                st.write(f"Status: {request['status']}")
                if 'file' in request:
                    if request['file_type'].startswith('image/'):
                        if 'enhanced_file' in request:
                            st.image(request['enhanced_file'], caption="Enhanced Document Image")
                        else:
                            st.image(request['file'], caption="Document Image")
                    elif request['file_type'] == 'application/pdf':
                        st.write("PDF file uploaded (preview not available)")
                    else:
                        st.write(f"File of type {request['file_type']} uploaded")

def admin_panel():
    st.header("Admin Panel")

    if not st.session_state.requests:
        st.info("No requests to review.")
    else:
        for i, request in enumerate(st.session_state.requests):
            with st.expander(f"Request: {request['title']}"):
                st.write(f"Description: {request['description']}")
                st.write(f"Quantity: {request['quantity']}")
                st.write(f"Total Price: {request['total_price']} Moldovan Lira")
                st.write(f"Status: {request['status']}")
                if 'file' in request:
                    if request['file_type'].startswith('image/'):
                        if 'enhanced_file' in request:
                            st.image(request['enhanced_file'], caption="Enhanced Document Image")
                        else:
                            st.image(request['file'], caption="Document Image")
                    elif request['file_type'] == 'application/pdf':
                        st.write("PDF file uploaded (preview not available)")
                    else:
                        st.write(f"File of type {request['file_type']} uploaded")

                new_status = st.selectbox("Update Status", ["Pending", "Approved", "Denied", "Archived"], key=f"status_{i}")
                comment = st.text_area("Add Comment", key=f"comment_{i}")

                if st.button("Update", key=f"update_{i}"):
                    request['status'] = new_status
                    if comment:
                        request['comment'] = comment
                    st.success("Request updated successfully!")
                    send_email("Procurement Request Update", f"The status of your request '{request['title']}' has been updated to {new_status}", "employee@example.com")

if __name__ == "__main__":
    main()

# Add this to handle camera capture events
if 'camera_image' not in st.session_state:
    st.session_state.camera_image = None

def handle_camera_capture(image_data):
    st.session_state.camera_image = image_data

st.components.v1.html("""
<script>
window.addEventListener('message', function(e) {
    if (e.data.type === 'camera_capture') {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: e.data.image
        }, '*');
    }
}, false);
</script>
""", height=0)
