FROM python:3.10

# Set the working directory within the container
WORKDIR /api-flask

# Copy the necessary files and directories into the container
COPY app.py requirements.txt /api-flask/
COPY world/ /api-flask/world/


# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Flask application
EXPOSE 9000

# Define the command to run the Flask application using Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:9000", "-w", "2"]