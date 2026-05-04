## Task: 
Design and create a containerized backend API to accept a video feed on an endpoint, process the video feed to detect a face, store import regions of interest in a database, draw a rectangle around that face (specifically, an axis-aligned minimal bounding box, henceforth referred to as “ROI”) without using the OpenCV python library, and return the feed and the corresponding ROI data to the frontend.

- API should have 3 endpoints, one to receive the video feed, one to serve it, and one to serve ROI data.
- Any relevant data gathered from face detection should be stored in a database (pick the most appropriate database for the data).
- Assume only one face will be present in the video.
- Draw the ROI on each frame of the video feed without using OpenCV 3. Create a Frontend for Displaying a Video Feed
<!-- Create Image (png) showing the design/architecture diagram Docker container containing the frontend and backend working together. -->